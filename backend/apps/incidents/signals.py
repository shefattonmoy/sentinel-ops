# apps/incidents/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incident
from apps.events.websocket import WebSocketNotifier


@receiver(post_save, sender=Incident)
def incident_websocket_notification(sender, instance, created, **kwargs):
    """Send WebSocket notification for incident changes"""
    try:
        org_id = str(instance.organization_id) if instance.organization_id else None
        
        incident_data = {
            'id': str(instance.id),
            'title': instance.title,
            'severity': instance.severity,
            'status': instance.status,
            'priority': instance.priority,
            'incident_type': instance.incident_type,
            'source_ip': instance.source_ip,
            'created_at': instance.created_at.isoformat(),
            'is_critical': instance.is_critical,
        }
        
        if created:
            WebSocketNotifier.notify_incident(incident_data, org_id)
        else:
            WebSocketNotifier.notify_incident_update(incident_data, org_id)
    except Exception:
        pass