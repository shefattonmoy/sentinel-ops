# agent/test_agent.py
"""
Test script to verify agent functionality without actual server
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sentinel_agent.config import AgentConfig
from sentinel_agent.log_watcher import LogWatcher
from sentinel_agent.log_buffer import LogBuffer
from sentinel_agent.metrics_collector import MetricsCollector

def test_log_watcher():
    """Test log watching functionality"""
    print("Testing Log Watcher...")
    
    def callback(entry):
        print(f"Log entry: {entry['source']} - {entry['message'][:50]}")
    
    watcher = LogWatcher(callback)
    
    # Watch a test file
    test_file = "/tmp/test_log.txt"
    with open(test_file, 'w') as f:
        f.write("Test log line 1\n")
    
    watcher.add_file(test_file, source="test")
    watcher.start()
    
    # Append to the file
    import time
    time.sleep(1)
    
    with open(test_file, 'a') as f:
        f.write("Test log line 2\n")
        f.write("Test log line 3\n")
    
    time.sleep(2)
    watcher.stop()
    
    print("Log watcher test complete!")

def test_buffer():
    """Test log buffer"""
    print("\nTesting Log Buffer...")
    
    buffer = LogBuffer(max_size=100)
    
    # Add entries
    for i in range(10):
        buffer.add({'id': i, 'message': f'Test log {i}'})
    
    print(f"Buffer size: {buffer.size()}")
    
    # Get batch
    batch = buffer.get_batch(5)
    print(f"Got batch of {len(batch)} entries")
    
    # Remove entries
    buffer.remove(3)
    print(f"Buffer size after remove: {buffer.size()}")
    
    buffer.clear()
    print(f"Buffer size after clear: {buffer.size()}")
    
    print("Buffer test complete!")

def test_metrics():
    """Test metrics collection"""
    print("\nTesting Metrics Collector...")
    
    def callback(metrics):
        print(f"Metrics collected:")
        for key, value in metrics.items():
            if key != 'timestamp':
                print(f"  {key}: {value}")
    
    collector = MetricsCollector(callback)
    collector.start(interval=2)
    
    import time
    time.sleep(5)
    
    collector.stop()
    print("Metrics test complete!")

if __name__ == '__main__':
    test_log_watcher()
    test_buffer()
    test_metrics()
    print("\nAll tests passed!")