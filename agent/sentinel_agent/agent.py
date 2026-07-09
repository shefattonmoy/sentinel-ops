# agent/sentinel_agent/agent.py
import os
import time
import signal
import socket
import threading
from typing import Dict, Optional
from datetime import datetime

from .config import AgentConfig
from .log_watcher import LogWatcher
from .metrics_collector import MetricsCollector
from .log_buffer import LogBuffer
from .api_client import APIClient


class SentinelAgent:
    """
    Main agent class that orchestrates all components.
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
        # Set hostname if not configured
        if not self.config.hostname:
            self.config.hostname = socket.gethostname()
        
        # Initialize components
        self.api_client = APIClient(
            server_url=self.config.server_url,
            token=self.config.token
        )
        
        self.log_buffer = LogBuffer(
            buffer_path=self.config.buffer_path,
            max_size=self.config.max_buffer_size
        )
        
        self.log_watcher = LogWatcher(callback=self._on_log_entry)
        self.metrics_collector = MetricsCollector(callback=self._on_metrics)
        
        # State
        self.running = False
        self.registered = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.log_sender_thread: Optional[threading.Thread] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the agent"""
        print(f"Starting SentinelOps Agent v1.0.0")
        print(f"Hostname: {self.config.hostname}")
        print(f"Server: {self.config.server_url}")
        
        self.running = True
        
        # Register with server
        self._register()
        
        # Start components
        self._start_log_watchers()
        self._start_metrics_collector()
        self._start_heartbeat()
        self._start_log_sender()
        
        print("Agent started successfully")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the agent"""
        print("Stopping agent...")
        self.running = False
        
        # Stop components
        self.log_watcher.stop()
        self.metrics_collector.stop()
        
        # Save buffered logs
        self.log_buffer._save_to_disk()
        
        print("Agent stopped")
    

    def _register(self):
        """Register agent with server"""
        if self.config.token:
            # Already registered
            self.api_client.set_token(self.config.token)
            self.registered = True
            print("Using existing registration token")
            return
        
        print("Registering with server...")
        
        for attempt in range(self.config.max_retries):
            result = self.api_client.register(
                name=self.config.agent_name or self.config.hostname,
                hostname=self.config.hostname,
                version="1.0.0"
            )
            
            if result:
                status = result.get('status', '')
                
                # Handle both "registered" and "existing" status
                if status in ['registered', 'existing']:
                    self.config.agent_id = result.get('agent_id')
                    self.config.token = result.get('token')
                    self.api_client.set_token(self.config.token)
                    self.registered = True
                    
                    # Save config with token
                    self.config.save()
                    
                    if status == 'existing':
                        print(f"Agent already registered. Agent ID: {self.config.agent_id}")
                    else:
                        print(f"Registered successfully. Agent ID: {self.config.agent_id}")
                    return
                
                # Handle error status
                elif status == 'error':
                    print(f"Registration error: {result.get('message', 'Unknown error')}")
                    return
            
            print(f"Registration attempt {attempt + 1} failed, retrying...")
            time.sleep(self.config.retry_delay * (self.config.retry_backoff ** attempt))
        
        print("Failed to register with server")
    
    
    def _start_log_watchers(self):
        """Start watching log files"""
        # Add configured log paths
        for log_path in self.config.log_paths:
            if os.path.exists(log_path):
                self.log_watcher.add_file(log_path)
                print(f"Watching: {log_path}")
            else:
                print(f"Log file not found: {log_path}")
        
        # Add custom log paths
        for log_path in self.config.custom_log_paths:
            if os.path.exists(log_path):
                self.log_watcher.add_file(log_path)
                print(f"Watching: {log_path}")
        
        # Add Django log paths
        for log_path in self.config.django_log_paths:
            if os.path.exists(log_path):
                self.log_watcher.add_file(log_path, source='django')
                print(f"Watching Django log: {log_path}")
        
        # Start watching
        self.log_watcher.start()
    
    def _start_metrics_collector(self):
        """Start collecting system metrics"""
        if self.config.collect_metrics:
            self.metrics_collector.start(interval=self.config.metrics_interval)
            print(f"Metrics collection started (interval: {self.config.metrics_interval}s)")
    
    def _start_heartbeat(self):
        """Start heartbeat thread"""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print(f"Heartbeat started (interval: {self.config.heartbeat_interval}s)")
    
    def _start_log_sender(self):
        """Start log sender thread"""
        self.log_sender_thread = threading.Thread(target=self._log_sender_loop, daemon=True)
        self.log_sender_thread.start()
        print("Log sender started")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                # Send heartbeat with latest metrics
                self.api_client.send_heartbeat()
            except Exception as e:
                print(f"Heartbeat error: {e}")
            
            time.sleep(self.config.heartbeat_interval)
    
    def _log_sender_loop(self):
        """Send buffered logs to server"""
        while self.running:
            try:
                if self.log_buffer.size() > 0:
                    self._send_buffered_logs()
            except Exception as e:
                print(f"Log sender error: {e}")
            
            time.sleep(2)  # Send every 2 seconds
    
    def _send_buffered_logs(self):
        """Send buffered logs to server"""
        batch = self.log_buffer.get_batch(self.config.log_batch_size)
        
        if not batch:
            return
        
        success = self.api_client.send_logs(
            agent_name=self.config.agent_name or self.config.hostname,
            hostname=self.config.hostname,
            logs=batch
        )
        
        if success:
            self.log_buffer.remove(len(batch))
            
            if self.log_buffer.size() > 0:
                print(f"Sent {len(batch)} logs, {self.log_buffer.size()} remaining in buffer")
        else:
            print(f"Failed to send logs, buffering for retry")
    
    def _on_log_entry(self, entry: Dict):
        """Callback for new log entries"""
        self.log_buffer.add(entry)
    
    def _on_metrics(self, metrics: Dict):
        """Callback for new metrics"""
        # Store latest metrics and send with next heartbeat
        self._latest_metrics = metrics