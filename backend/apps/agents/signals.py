# apps/agents/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Agent
from apps.events.websocket import WebSocketNotifier


@receiver(post_save, sender=Agent)
def agent_status_websocket(sender, instance, **kwargs):
    """Send WebSocket notification for agent status changes"""
    try:
        org_id = str(instance.organization_id) if instance.organization_id else None
        
        agent_data = {
            'agent_id': instance.agent_id,
            'name': instance.name,
            'hostname': instance.hostname,
            'status': instance.status,
            'is_online': instance.is_online(),
            'cpu_usage': instance.cpu_usage,
            'memory_usage': instance.memory_usage,
            'disk_usage': instance.disk_usage,
            'last_heartbeat': instance.last_heartbeat.isoformat() if instance.last_heartbeat else None,
        }
        
        WebSocketNotifier.notify_agent_status(agent_data, org_id)
    except Exception:
        pass