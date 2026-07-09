# apps/events/parsers.py
import re
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

class BaseParser(ABC):
    """Base class for all log parsers"""
    
    @abstractmethod
    def parse(self, raw_log) -> List[Dict]:
        """Parse a raw log entry and return list of normalized events"""
        pass
    
    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """Check if this parser can handle the given source"""
        pass
    
    def _normalize_event(self, **kwargs) -> Dict:
        """Create a normalized event dictionary"""
        event = {
            'event_type': kwargs.get('event_type', 'UNKNOWN'),
            'category': kwargs.get('category', 'system'),
            'severity': kwargs.get('severity', 'info'),
            'source': kwargs.get('source', 'unknown'),
            'service': kwargs.get('service'),
            'source_ip': kwargs.get('source_ip'),
            'source_port': kwargs.get('source_port'),
            'target_ip': kwargs.get('target_ip'),
            'target_port': kwargs.get('target_port'),
            'source_hostname': kwargs.get('source_hostname'),
            'target_hostname': kwargs.get('target_hostname'),
            'username': kwargs.get('username'),
            'user_id': kwargs.get('user_id'),
            'message': kwargs.get('message', ''),
            'description': kwargs.get('description'),
            'metadata': kwargs.get('metadata', {}),
            'tags': kwargs.get('tags', []),
            'confidence': kwargs.get('confidence', 1.0),
        }
        return event


class SSHParser(BaseParser):
    """Parser for SSH/authentication logs"""
    
    def can_handle(self, source: str) -> bool:
        return source in ['auth', 'auth.log', 'secure']
    
    def parse(self, raw_log) -> List[Dict]:
        events = []
        message = raw_log.raw_message
        
        # Failed password
        failed_pwd = re.search(
            r'Failed password for (\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)',
            message
        )
        if failed_pwd:
            events.append(self._normalize_event(
                event_type='FAILED_LOGIN',
                category='authentication',
                severity='medium',
                source='ssh',
                service='ssh',
                source_ip=failed_pwd.group(2),
                source_port=int(failed_pwd.group(3)),
                username=failed_pwd.group(1),
                message=f"Failed SSH login for {failed_pwd.group(1)} from {failed_pwd.group(2)}",
                tags=['ssh', 'failed_login', 'authentication'],
            ))
        
        # Successful login
        success_login = re.search(
            r'Accepted (password|publickey) for (\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)',
            message
        )
        if success_login:
            events.append(self._normalize_event(
                event_type='SUCCESSFUL_LOGIN',
                category='authentication',
                severity='info',
                source='ssh',
                service='ssh',
                source_ip=success_login.group(3),
                source_port=int(success_login.group(4)),
                username=success_login.group(2),
                message=f"Successful SSH login for {success_login.group(2)} from {success_login.group(3)}",
                metadata={'auth_method': success_login.group(1)},
                tags=['ssh', 'successful_login', 'authentication'],
            ))
        
        # Invalid user
        invalid_user = re.search(
            r'Invalid user (\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)',
            message
        )
        if invalid_user:
            events.append(self._normalize_event(
                event_type='INVALID_USER',
                category='authentication',
                severity='medium',
                source='ssh',
                service='ssh',
                source_ip=invalid_user.group(2),
                source_port=int(invalid_user.group(3)),
                username=invalid_user.group(1),
                message=f"Invalid user {invalid_user.group(1)} from {invalid_user.group(2)}",
                tags=['ssh', 'invalid_user', 'authentication'],
            ))
        
        # Brute force
        if 'authentication failure' in message.lower() or 'maximum authentication attempts' in message.lower():
            events.append(self._normalize_event(
                event_type='BRUTE_FORCE_ATTEMPT',
                category='security',
                severity='high',
                source='ssh',
                service='ssh',
                message='Multiple authentication failures detected',
                tags=['ssh', 'brute_force', 'attack'],
            ))
        
        # Sudo command
        sudo_cmd = re.search(r'(\S+) : TTY=.* ; USER=(\S+) ; COMMAND=(.+)', message)
        if sudo_cmd:
            events.append(self._normalize_event(
                event_type='SUDO_COMMAND',
                category='authorization',
                severity='medium',
                source='ssh',
                service='sudo',
                username=sudo_cmd.group(1),
                message=f"Sudo command executed by {sudo_cmd.group(1)} as {sudo_cmd.group(2)}: {sudo_cmd.group(3)}",
                metadata={
                    'original_user': sudo_cmd.group(1),
                    'target_user': sudo_cmd.group(2),
                    'command': sudo_cmd.group(3).strip(),
                },
                tags=['sudo', 'privilege_escalation'],
            ))
        
        # User added/deleted
        user_added = re.search(r'new user: name=(\S+)', message)
        if user_added:
            events.append(self._normalize_event(
                event_type='USER_CREATED',
                category='authorization',
                severity='high',
                source='system',
                username=user_added.group(1),
                message=f"New user created: {user_added.group(1)}",
                tags=['user_management', 'user_created'],
            ))
        
        user_deleted = re.search(r'delete user \'(\S+)\'', message)
        if user_deleted:
            events.append(self._normalize_event(
                event_type='USER_DELETED',
                category='authorization',
                severity='high',
                source='system',
                username=user_deleted.group(1),
                message=f"User deleted: {user_deleted.group(1)}",
                tags=['user_management', 'user_deleted'],
            ))
        
        return events if events else [self._normalize_event(
            event_type='AUTH_EVENT',
            category='authentication',
            severity='info',
            source='ssh',
            message=message[:200],
        )]


class NginxParser(BaseParser):
    """Parser for Nginx access and error logs"""
    
    def can_handle(self, source: str) -> bool:
        return source in ['nginx', 'nginx_access', 'nginx_error', 'nginx.access', 'nginx.error']
    
    def parse(self, raw_log) -> List[Dict]:
        events = []
        message = raw_log.raw_message
        
        # Access log pattern
        access_pattern = r'(\d+\.\d+\.\d+\.\d+)\s-\s-\s\[(.*?)\]\s"(\w+)\s(\S+)\sHTTP/[\d.]*"\s(\d+)\s(\d+)\s".*?"\s"(.*?)"'
        access_match = re.search(access_pattern, message)
        
        if access_match:
            status_code = int(access_match.group(5))
            
            # Determine severity based on status code
            if status_code >= 500:
                severity = 'high'
                event_type = 'SERVER_ERROR'
                category = 'application'
            elif status_code >= 400:
                severity = 'medium'
                event_type = 'CLIENT_ERROR'
                category = 'application'
            elif status_code == 401 or status_code == 403:
                severity = 'high'
                event_type = 'ACCESS_DENIED'
                category = 'security'
            elif status_code >= 300:
                severity = 'info'
                event_type = 'REDIRECT'
                category = 'network'
            else:
                severity = 'info'
                event_type = 'HTTP_REQUEST'
                category = 'network'
            
            events.append(self._normalize_event(
                event_type=event_type,
                category=category,
                severity=severity,
                source='nginx',
                service='web',
                source_ip=access_match.group(1),
                source_port=None,
                message=f"{access_match.group(3)} {access_match.group(4)} - Status: {status_code}",
                metadata={
                    'method': access_match.group(3),
                    'path': access_match.group(4),
                    'status_code': status_code,
                    'response_size': int(access_match.group(6)),
                    'user_agent': access_match.group(7),
                },
                tags=['nginx', 'http', event_type.lower()],
            ))
            
            return events
        
        # Error log patterns
        if 'error' in message.lower() or 'crit' in message.lower():
            severity = 'critical' if 'crit' in message.lower() else 'high'
            
            # Extract client IP from error log
            client_ip = None
            ip_match = re.search(r'client: (\d+\.\d+\.\d+\.\d+)', message)
            if ip_match:
                client_ip = ip_match.group(1)
            
            events.append(self._normalize_event(
                event_type='NGINX_ERROR',
                category='application',
                severity=severity,
                source='nginx',
                service='web',
                source_ip=client_ip,
                message=message[:200],
                tags=['nginx', 'error'],
            ))
        
        return events if events else [self._normalize_event(
            event_type='NGINX_EVENT',
            category='network',
            severity='info',
            source='nginx',
            message=message[:200],
        )]


class DockerParser(BaseParser):
    """Parser for Docker container logs"""
    
    def can_handle(self, source: str) -> bool:
        return source in ['docker', 'container', 'docker_logs']
    
    def parse(self, raw_log) -> List[Dict]:
        events = []
        message = raw_log.raw_message
        
        # Container crash/exit
        if re.search(r'(container died|exited|killed)', message, re.IGNORECASE):
            container_name = self._extract_container_name(message)
            
            events.append(self._normalize_event(
                event_type='CONTAINER_CRASH',
                category='container',
                severity='high',
                source='docker',
                service=container_name,
                message=f"Container crashed: {message[:200]}",
                metadata={'container_name': container_name},
                tags=['docker', 'crash', 'container'],
            ))
        
        # Container restart
        if 'restarting' in message.lower():
            container_name = self._extract_container_name(message)
            
            events.append(self._normalize_event(
                event_type='CONTAINER_RESTART',
                category='container',
                severity='medium',
                source='docker',
                service=container_name,
                message=f"Container restarting: {message[:200]}",
                metadata={'container_name': container_name},
                tags=['docker', 'restart', 'container'],
            ))
        
        # OOM kill
        if 'out of memory' in message.lower() or 'oom' in message.lower():
            container_name = self._extract_container_name(message)
            
            events.append(self._normalize_event(
                event_type='CONTAINER_OOM',
                category='container',
                severity='critical',
                source='docker',
                service=container_name,
                message=f"Container out of memory: {message[:200]}",
                metadata={'container_name': container_name},
                tags=['docker', 'oom', 'memory'],
            ))
        
        # Health check failed
        if 'health check' in message.lower() and ('failed' in message.lower() or 'unhealthy' in message.lower()):
            container_name = self._extract_container_name(message)
            
            events.append(self._normalize_event(
                event_type='CONTAINER_UNHEALTHY',
                category='container',
                severity='high',
                source='docker',
                service=container_name,
                message=f"Container health check failed: {message[:200]}",
                metadata={'container_name': container_name},
                tags=['docker', 'health_check', 'unhealthy'],
            ))
        
        return events if events else [self._normalize_event(
            event_type='DOCKER_EVENT',
            category='container',
            severity='info',
            source='docker',
            message=message[:200],
        )]
    
    def _extract_container_name(self, message: str) -> Optional[str]:
        """Extract container name from docker log message"""
        # Try to find container ID or name
        container_match = re.search(r'container[_\s]*(\S+)', message, re.IGNORECASE)
        if container_match:
            return container_match.group(1)[:12]
        
        # Try hex container ID
        hex_match = re.search(r'([a-f0-9]{12,64})', message)
        if hex_match:
            return hex_match.group(1)[:12]
        
        return None


class DjangoParser(BaseParser):
    """Parser for Django application logs"""
    
    def can_handle(self, source: str) -> bool:
        return source in ['django', 'application', 'django_app']
    
    def parse(self, raw_log) -> List[Dict]:
        events = []
        message = raw_log.raw_message
        
        # Django error
        if 'error' in message.lower() or 'traceback' in message.lower():
            events.append(self._normalize_event(
                event_type='DJANGO_ERROR',
                category='application',
                severity='high',
                source='django',
                service=raw_log.service or 'web',
                message=message[:200],
                tags=['django', 'error'],
            ))
        
        # Django warning
        elif 'warning' in message.lower() or 'warn' in message.lower():
            events.append(self._normalize_event(
                event_type='DJANGO_WARNING',
                category='application',
                severity='medium',
                source='django',
                service=raw_log.service or 'web',
                message=message[:200],
                tags=['django', 'warning'],
            ))
        
        # Database query
        elif 'select' in message.lower() or 'insert' in message.lower() or 'update' in message.lower() or 'delete' in message.lower():
            events.append(self._normalize_event(
                event_type='DATABASE_QUERY',
                category='application',
                severity='info',
                source='django',
                service='database',
                message=message[:200],
                tags=['django', 'database'],
            ))
        
        # Request handling
        elif any(method in message for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
            events.append(self._normalize_event(
                event_type='DJANGO_REQUEST',
                category='application',
                severity='info',
                source='django',
                service='web',
                message=message[:200],
                tags=['django', 'http'],
            ))
        
        # Default
        else:
            events.append(self._normalize_event(
                event_type='DJANGO_LOG',
                category='application',
                severity='info',
                source='django',
                service=raw_log.service or 'web',
                message=message[:200],
                tags=['django'],
            ))
        
        return events


class SystemLogParser(BaseParser):
    """Parser for system logs (syslog, messages)"""
    
    def can_handle(self, source: str) -> bool:
        return source in ['syslog', 'system', 'messages', 'kern']
    
    def parse(self, raw_log) -> List[Dict]:
        events = []
        message = raw_log.raw_message
        
        # Out of memory
        if 'out of memory' in message.lower() or 'oom killer' in message.lower():
            events.append(self._normalize_event(
                event_type='OOM_KILLER',
                category='system',
                severity='critical',
                source='system',
                message=message[:200],
                tags=['system', 'memory', 'oom'],
            ))
        
        # Kernel panic
        elif 'kernel panic' in message.lower():
            events.append(self._normalize_event(
                event_type='KERNEL_PANIC',
                category='system',
                severity='critical',
                source='system',
                message=message[:200],
                tags=['system', 'kernel', 'panic'],
            ))
        
        # Service failure
        elif any(term in message.lower() for term in ['service failed', 'service stopped', 'failed to start']):
            events.append(self._normalize_event(
                event_type='SERVICE_FAILURE',
                category='system',
                severity='high',
                source='system',
                message=message[:200],
                tags=['system', 'service', 'failure'],
            ))
        
        # Disk error
        elif 'disk' in message.lower() or 'i/o error' in message.lower() or 'read error' in message.lower():
            events.append(self._normalize_event(
                event_type='DISK_ERROR',
                category='system',
                severity='high',
                source='system',
                message=message[:200],
                tags=['system', 'disk', 'error'],
            ))
        
        # Network issue
        elif any(term in message.lower() for term in ['network', 'eth', 'link down', 'connection']):
            events.append(self._normalize_event(
                event_type='NETWORK_EVENT',
                category='network',
                severity='medium',
                source='system',
                message=message[:200],
                tags=['system', 'network'],
            ))
        
        # Default system event
        else:
            severity = 'info'
            if 'error' in message.lower():
                severity = 'high'
            elif 'warn' in message.lower():
                severity = 'medium'
            
            events.append(self._normalize_event(
                event_type='SYSTEM_EVENT',
                category='system',
                severity=severity,
                source='system',
                message=message[:200],
                tags=['system'],
            ))
        
        return events


# Parser registry
PARSER_REGISTRY = [
    SSHParser(),
    NginxParser(),
    DockerParser(),
    DjangoParser(),
    SystemLogParser(),
]

def get_parser(source: str) -> Optional[BaseParser]:
    """Get the appropriate parser for a log source"""
    for parser in PARSER_REGISTRY:
        if parser.can_handle(source):
            return parser
    return None