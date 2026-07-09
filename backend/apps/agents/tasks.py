# apps/agents/tasks.py
from celery import shared_task
from .health import HealthMonitor
from django.utils import timezone
from datetime import timedelta

from backend.apps.agents.health import HealthMonitor
from .models import Agent
from django.db.models import Q

@shared_task
def check_agent_heartbeats():
    """
    Periodic task to check agent heartbeats and mark offline agents.
    Runs every 2 minutes.
    """
    now = timezone.now()
    
    # Find agents that haven't sent heartbeat in 2x their interval
    agents = Agent.objects.filter(
        is_active=True,
        status='online'
    )
    
    offline_count = 0
    for agent in agents:
        if agent.last_heartbeat:
            threshold = now - timedelta(seconds=agent.heartbeat_interval * 2)
            if agent.last_heartbeat < threshold:
                agent.mark_offline()
                offline_count += 1
    
    return f"Checked {agents.count()} agents, {offline_count} marked offline"

@shared_task
def cleanup_old_heartbeats():
    """
    Clean up heartbeat records older than 30 days.
    """
    from .models import AgentHeartbeat
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    deleted_count, _ = AgentHeartbeat.objects.filter(
        timestamp__lt=thirty_days_ago
    ).delete()
    
    return f"Deleted {deleted_count} old heartbeat records"

@shared_task
def send_agent_offline_alerts():
    """
    Send alerts for agents that are offline.
    """
    from apps.alerts.models import Alert
    
    offline_agents = Agent.objects.filter(
        is_active=True,
        status='offline',
        missed_heartbeats__gte=3
    )
    
    alerts_created = 0
    for agent in offline_agents:
        # Check if alert already exists
        existing_alert = Alert.objects.filter(
            source='agent_monitor',
            metadata__agent_id=str(agent.agent_id),
            status='open',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).exists()
        
        if not existing_alert:
            Alert.objects.create(
                title=f'Agent Offline: {agent.name}',
                description=f'Agent {agent.name} ({agent.hostname}) has been offline for {agent.missed_heartbeats * agent.heartbeat_interval} seconds.',
                severity='high',
                source='agent_monitor',
                organization=agent.organization,
                metadata={
                    'agent_id': str(agent.agent_id),
                    'hostname': agent.hostname,
                    'last_heartbeat': agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
                    'missed_heartbeats': agent.missed_heartbeats,
                }
            )
            alerts_created += 1
    
    return f"Created {alerts_created} offline alerts"




@shared_task
def monitor_agent_health():
    """Periodic task to monitor agent health"""
    monitor = HealthMonitor()
    result = monitor.check_all_agents()
    return f"Health check complete: {result}"

@shared_task
def check_agent_heartbeats():
    """Check for missed heartbeats"""
    from django.utils import timezone
    from datetime import timedelta
    from .models import Agent
    
    threshold = timezone.now() - timedelta(minutes=2)
    
    offline_agents = Agent.objects.filter(
        is_active=True,
        status='online',
        last_heartbeat__lt=threshold
    )
    
    count = 0
    for agent in offline_agents:
        agent.mark_offline()
        count += 1
    
    return f"Marked {count} agents as offline"