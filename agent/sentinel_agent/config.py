# agent/sentinel_agent/config.py
import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class AgentConfig:
    """Agent configuration"""
    # Server connection
    server_url: str = "http://localhost:8000/api"
    agent_name: str = ""
    hostname: str = ""
    
    # Authentication
    agent_id: Optional[str] = None
    token: Optional[str] = None
    
    # Log monitoring
    log_paths: List[str] = field(default_factory=lambda: [
        "/var/log/auth.log",
        "/var/log/syslog",
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
    ])
    
    # Custom log paths to watch
    custom_log_paths: List[str] = field(default_factory=list)
    
    # Docker monitoring (if available)
    monitor_docker: bool = True
    
    # Django log paths
    django_log_paths: List[str] = field(default_factory=list)
    
    # Performance
    heartbeat_interval: int = 30  # seconds
    log_batch_size: int = 100
    max_buffer_size: int = 10000
    
    # Retry settings
    max_retries: int = 5
    retry_delay: int = 5  # seconds
    retry_backoff: float = 2.0  # exponential backoff multiplier
    
    # Buffer settings
    buffer_path: str = "/tmp/sentinel_agent_buffer"
    
    # Metrics collection
    collect_metrics: bool = True
    metrics_interval: int = 60  # seconds
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def save(self, path: str = None):
        """Save configuration to file"""
        if path is None:
            path = str(Path.home() / ".sentinel_agent" / "config.json")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str = None) -> 'AgentConfig':
        """Load configuration from file"""
        if path is None:
            path = str(Path.home() / ".sentinel_agent" / "config.json")
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        
        return cls()
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Load configuration from environment variables"""
        return cls(
            server_url=os.getenv("SENTINEL_SERVER_URL", "http://localhost:8000/api"),
            agent_name=os.getenv("SENTINEL_AGENT_NAME", ""),
            hostname=os.getenv("SENTINEL_HOSTNAME", ""),
            token=os.getenv("SENTINEL_TOKEN"),
            heartbeat_interval=int(os.getenv("SENTINEL_HEARTBEAT_INTERVAL", "30")),
            log_batch_size=int(os.getenv("SENTINEL_BATCH_SIZE", "100")),
            max_retries=int(os.getenv("SENTINEL_MAX_RETRIES", "5")),
        )