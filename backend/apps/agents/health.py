# apps/agents/health.py
import logging
from django.utils import timezone
from datetime import timedelta
from apps.agents.models import Agent, AgentHeartbeat
from apps.notifications.service import notify_agent_offline

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor agent health and trigger alerts"""
    
    def check_all_agents(self):
        """Check health of all active agents"""
        agents = Agent.objects.filter(is_active=True, status='online')
        
        offline_count = 0
        degraded_count = 0
        
        for agent in agents:
            if self._is_agent_offline(agent):
                self._handle_offline_agent(agent)
                offline_count += 1
            elif self._is_agent_degraded(agent):
                self._handle_degraded_agent(agent)
                degraded_count += 1
        
        return {
            'checked': agents.count(),
            'offline': offline_count,
            'degraded': degraded_count,
        }
    
    def _is_agent_offline(self, agent):
        """Check if agent is offline"""
        if not agent.last_heartbeat:
            return True
        
        # Offline if no heartbeat for 2x the interval
        threshold = timezone.now() - timedelta(seconds=agent.heartbeat_interval * 2)
        return agent.last_heartbeat < threshold
    
    def _is_agent_degraded(self, agent):
        """Check if agent is degraded"""
        # Check resource usage
        if agent.cpu_usage and agent.cpu_usage > 90:
            return True
        if agent.memory_usage and agent.memory_usage > 90:
            return True
        if agent.disk_usage and agent.disk_usage > 90:
            return True
        
        return False
    
    def _handle_offline_agent(self, agent):
        """Handle offline agent"""
        # Mark as offline
        agent.mark_offline()
        
        # Send notification if configured
        if hasattr(agent, 'configuration') and agent.configuration.notify_on_offline:
            notify_agent_offline(agent)
        
        logger.warning(f"Agent {agent.name} ({agent.hostname}) marked as offline")
    
    def _handle_degraded_agent(self, agent):
        """Handle degraded agent"""
        agent.status = 'degraded'
        agent.save()
        
        logger.warning(f"Agent {agent.name} ({agent.hostname}) marked as degraded")
    
    def get_agent_health_report(self, agent):
        """Get detailed health report for an agent"""
        last_hb = agent.heartbeats.first()
        
        return {
            'agent_id': agent.agent_id,
            'name': agent.name,
            'hostname': agent.hostname,
            'status': agent.status,
            'is_online': agent.is_online(),
            'last_heartbeat': agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            'uptime_seconds': agent.get_uptime(),
            'cpu_usage': agent.cpu_usage,
            'memory_usage': agent.memory_usage,
            'disk_usage': agent.disk_usage,
            'missed_heartbeats': agent.missed_heartbeats,
            'error_count': agent.error_count,
            'last_error': agent.last_error,
            'latest_metrics': {
                'cpu': last_hb.cpu_usage if last_hb else None,
                'memory': last_hb.memory_usage if last_hb else None,
                'disk': last_hb.disk_usage if last_hb else None,
                'processes': last_hb.process_count if last_hb else None,
                'network': last_hb.network_io if last_hb else None,
            } if last_hb else None,
            'health_checks': {
                'cpu_healthy': not agent.cpu_usage or agent.cpu_usage < 90,
                'memory_healthy': not agent.memory_usage or agent.memory_usage < 90,
                'disk_healthy': not agent.disk_usage or agent.disk_usage < 90,
                'heartbeat_healthy': agent.missed_heartbeats < 3,
            }
        }