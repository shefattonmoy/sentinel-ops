# agent/sentinel_agent/metrics_collector.py
import os
import threading
import time
from typing import Dict, Optional
from datetime import datetime

class MetricsCollector:
    """Collects system metrics"""
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.interval = 60  # seconds
    
    def start(self, interval: int = 60):
        """Start collecting metrics"""
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop collecting metrics"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _collect_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.callback(metrics)
            except Exception as e:
                print(f"Error collecting metrics: {e}")
            
            time.sleep(self.interval)
    
    def collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_usage': self._get_cpu_usage(),
            'memory_usage': self._get_memory_usage(),
            'disk_usage': self._get_disk_usage(),
            'network_io': self._get_network_io(),
            'process_count': self._get_process_count(),
            'uptime': self._get_uptime(),
        }
        
        return metrics
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get CPU usage percentage"""
        try:
            # Linux: /proc/stat
            if os.path.exists('/proc/stat'):
                with open('/proc/stat', 'r') as f:
                    for line in f:
                        if line.startswith('cpu '):
                            parts = line.split()
                            total = sum(int(x) for x in parts[1:])
                            idle = int(parts[4])
                            return ((total - idle) / total) * 100
        except Exception as e:
            print(f"Error getting CPU usage: {e}")
        
        return None
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get memory usage percentage"""
        try:
            # Linux: /proc/meminfo
            if os.path.exists('/proc/meminfo'):
                mem_total = 0
                mem_available = 0
                
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            mem_total = int(line.split()[1])
                        elif line.startswith('MemAvailable:'):
                            mem_available = int(line.split()[1])
                
                if mem_total > 0:
                    return ((mem_total - mem_available) / mem_total) * 100
        except Exception as e:
            print(f"Error getting memory usage: {e}")
        
        return None
    
    def _get_disk_usage(self) -> Optional[float]:
        """Get disk usage percentage for root partition"""
        try:
            import shutil
            usage = shutil.disk_usage('/')
            return (usage.used / usage.total) * 100
        except Exception as e:
            print(f"Error getting disk usage: {e}")
        
        return None
    
    def _get_network_io(self) -> Dict:
        """Get network IO statistics"""
        network_io = {
            'bytes_sent': 0,
            'bytes_recv': 0,
        }
        
        try:
            if os.path.exists('/proc/net/dev'):
                with open('/proc/net/dev', 'r') as f:
                    # Skip header lines
                    next(f)
                    next(f)
                    
                    for line in f:
                        parts = line.split()
                        if parts[0].startswith(('eth', 'ens', 'enp', 'wlan')):
                            network_io['bytes_recv'] += int(parts[1])
                            network_io['bytes_sent'] += int(parts[9])
        except Exception as e:
            print(f"Error getting network IO: {e}")
        
        return network_io
    
    def _get_process_count(self) -> Optional[int]:
        """Get total number of processes"""
        try:
            if os.path.exists('/proc'):
                return len([d for d in os.listdir('/proc') if d.isdigit()])
        except Exception as e:
            print(f"Error getting process count: {e}")
        
        return None
    
    def _get_uptime(self) -> Optional[float]:
        """Get system uptime in seconds"""
        try:
            if os.path.exists('/proc/uptime'):
                with open('/proc/uptime', 'r') as f:
                    return float(f.read().split()[0])
        except Exception as e:
            print(f"Error getting uptime: {e}")
        
        return None