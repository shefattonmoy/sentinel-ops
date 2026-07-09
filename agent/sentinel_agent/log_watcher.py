# agent/sentinel_agent/log_watcher.py
import os
import time
import threading
from pathlib import Path
from typing import List, Dict, Callable, Optional
from datetime import datetime
import hashlib

class LogWatcher:
    """
    Watches log files for new entries and sends them to callback.
    Supports log rotation and file truncation.
    """
    
    def __init__(self, callback: Callable[[Dict], None]):
        self.callback = callback
        self.watched_files: Dict[str, dict] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
    
    def add_file(self, filepath: str, source: str = None):
        """Add a file to watch"""
        with self.lock:
            if filepath not in self.watched_files:
                if source is None:
                    # Auto-detect source from filepath
                    source = self._detect_source(filepath)
                
                self.watched_files[filepath] = {
                    'source': source,
                    'position': 0,
                    'inode': None,
                    'last_size': 0,
                }
                
                # Set initial position to end of file
                if os.path.exists(filepath):
                    self.watched_files[filepath]['position'] = os.path.getsize(filepath)
                    self.watched_files[filepath]['inode'] = os.stat(filepath).st_ino
    
    def _detect_source(self, filepath: str) -> str:
        """Auto-detect log source from filepath"""
        path_lower = filepath.lower()
        
        if 'auth' in path_lower:
            return 'auth'
        elif 'syslog' in path_lower or 'messages' in path_lower:
            return 'syslog'
        elif 'nginx' in path_lower and 'access' in path_lower:
            return 'nginx_access'
        elif 'nginx' in path_lower and 'error' in path_lower:
            return 'nginx_error'
        elif 'docker' in path_lower:
            return 'docker'
        elif 'django' in path_lower:
            return 'django'
        else:
            return 'application'
    
    def remove_file(self, filepath: str):
        """Stop watching a file"""
        with self.lock:
            self.watched_files.pop(filepath, None)
    
    def start(self):
        """Start watching files in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop watching files"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _watch_loop(self):
        """Main watch loop"""
        while self.running:
            try:
                with self.lock:
                    for filepath, info in list(self.watched_files.items()):
                        self._check_file(filepath, info)
            except Exception as e:
                print(f"Error watching files: {e}")
            
            time.sleep(1)  # Check every second
    
    def _check_file(self, filepath: str, info: dict):
        """Check a single file for new content"""
        if not os.path.exists(filepath):
            return
        
        try:
            current_inode = os.stat(filepath).st_ino
            current_size = os.path.getsize(filepath)
            
            # Handle log rotation
            if current_inode != info['inode']:
                info['inode'] = current_inode
                info['position'] = 0
            
            # Handle file truncation
            if current_size < info['position']:
                info['position'] = 0
            
            # Read new content
            if current_size > info['position']:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(info['position'])
                    new_content = f.read()
                    info['position'] = f.tell()
                
                # Process new lines
                self._process_new_content(filepath, info['source'], new_content)
        
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    def _process_new_content(self, filepath: str, source: str, content: str):
        """Process new log content and send to callback"""
        lines = content.split('\n')
        
        for line in lines:
            if line.strip():
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': source,
                    'message': line.strip(),
                    'path': filepath,
                    'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
                }
                
                # Try to extract log level
                log_entry['level'] = self._extract_log_level(line)
                
                self.callback(log_entry)
    
    def _extract_log_level(self, line: str) -> Optional[str]:
        """Extract log level from log line"""
        line_upper = line.upper()
        
        if 'CRITICAL' in line_upper or 'FATAL' in line_upper:
            return 'CRITICAL'
        elif 'ERROR' in line_upper:
            return 'ERROR'
        elif 'WARNING' in line_upper or 'WARN' in line_upper:
            return 'WARNING'
        elif 'INFO' in line_upper:
            return 'INFO'
        elif 'DEBUG' in line_upper:
            return 'DEBUG'
        
        return None