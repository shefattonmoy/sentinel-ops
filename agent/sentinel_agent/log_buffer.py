# agent/sentinel_agent/log_buffer.py
import json
import os
import threading
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import time

class LogBuffer:
    """
    Buffers logs when the server is unreachable.
    Persists to disk and retries on reconnect.
    """
    
    def __init__(self, buffer_path: str = "/tmp/sentinel_agent_buffer", max_size: int = 10000):
        self.buffer_path = Path(buffer_path)
        self.max_size = max_size
        self.buffer: List[Dict] = []
        self.lock = threading.Lock()
        self._load_from_disk()
    
    def add(self, entry: Dict):
        """Add a log entry to the buffer"""
        with self.lock:
            self.buffer.append(entry)
            
            # Trim if over max size
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
            
            # Periodically save to disk
            if len(self.buffer) % 100 == 0:
                self._save_to_disk()
    
    def add_batch(self, entries: List[Dict]):
        """Add multiple log entries"""
        with self.lock:
            self.buffer.extend(entries)
            
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
    
    def get_all(self) -> List[Dict]:
        """Get all buffered entries"""
        with self.lock:
            entries = self.buffer.copy()
            return entries
    
    def get_batch(self, batch_size: int = 100) -> List[Dict]:
        """Get a batch of entries"""
        with self.lock:
            batch = self.buffer[:batch_size]
            return batch
    
    def remove(self, count: int):
        """Remove first N entries from buffer"""
        with self.lock:
            self.buffer = self.buffer[count:]
    
    def clear(self):
        """Clear the buffer"""
        with self.lock:
            self.buffer.clear()
            self._save_to_disk()
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def _save_to_disk(self):
        """Save buffer to disk"""
        try:
            self.buffer_path.parent.mkdir(parents=True, exist_ok=True)
            
            buffer_file = self.buffer_path / "buffer.json"
            with open(buffer_file, 'w') as f:
                json.dump(self.buffer, f)
        except Exception as e:
            print(f"Error saving buffer to disk: {e}")
    
    def _load_from_disk(self):
        """Load buffer from disk"""
        buffer_file = self.buffer_path / "buffer.json"
        
        if buffer_file.exists():
            try:
                with open(buffer_file, 'r') as f:
                    self.buffer = json.load(f)
                print(f"Loaded {len(self.buffer)} buffered logs from disk")
            except Exception as e:
                print(f"Error loading buffer from disk: {e}")
                self.buffer = []