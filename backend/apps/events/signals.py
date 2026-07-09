# apps/events/signals.py
"""
Django signals for real-time WebSocket notifications.
Automatically sends WebSocket updates when models are created/updated.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event
from .websocket import WebSocketNotifier


@receiver(post_save, sender=Event)
def event_created_websocket(sender, instance, created, **kwargs):
    """Send WebSocket notification when a new event is created"""
    if created:
        try:
            org_id = str(instance.agent.organization_id) if instance.agent.organization_id else None
            
            event_data = {
                'id': str(instance.id),
                'event_type': instance.event_type,
                'severity': instance.severity,
                'source': instance.source,
                'source_ip': instance.source_ip,
                'username': instance.username,
                'message': instance.message[:200],
                'timestamp': instance.timestamp.isoformat(),
                'agent_name': instance.agent.name,
                'agent_hostname': instance.agent.hostname,
            }
            
            WebSocketNotifier.notify_event(event_data, org_id)
        except Exception as e:
            # Silently fail - don't break event creation if WebSocket fails
            pass