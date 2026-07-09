# agent/sentinel_agent/api_client.py
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class APIClient:
    """Client for communicating with SentinelOps server"""
    
    def __init__(self, server_url: str, token: str = None):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    def _get_headers(self) -> Dict:
        """Get request headers"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SentinelOps-Agent/1.0.0',
        }
        
        if self.token:
            headers['Authorization'] = f'Token {self.token}'
        
        return headers
    
    def register(self, name: str, hostname: str, version: str = "1.0.0") -> Optional[Dict]:
        """Register agent with the server"""
        try:
            url = f"{self.server_url}/agents/register/"
            data = {
                'name': name,
                'hostname': hostname,
                'version': version,
            }
            
            response = self.session.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Registration failed: {response.status_code} - {response.text}")
                return None
        
        except requests.RequestException as e:
            print(f"Registration error: {e}")
            return None
    
    def send_heartbeat(self, metrics: Dict = None) -> bool:
        """Send heartbeat with optional metrics"""
        try:
            url = f"{self.server_url}/agents/heartbeat/"
            data = {}
            
            if metrics:
                data['metrics'] = metrics
            
            response = self.session.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=10
            )
            
            return response.status_code == 200
        
        except requests.RequestException as e:
            print(f"Heartbeat error: {e}")
            return False
    
    def send_logs(self, agent_name: str, hostname: str, logs: List[Dict]) -> bool:
        """Send logs to the server"""
        try:
            url = f"{self.server_url}/events/ingest/"
            data = {
                'agent': agent_name,
                'hostname': hostname,
                'logs': logs,
            }
            
            response = self.session.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Log ingestion failed: {response.status_code} - {response.text}")
                return False
        
        except requests.RequestException as e:
            print(f"Log ingestion error: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if server is reachable"""
        try:
            response = self.session.get(
                f"{self.server_url}/agents/heartbeat/",
                headers=self._get_headers(),
                timeout=5
            )
            return True
        except requests.RequestException:
            return False