# apps/alerts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alert
from apps.events.websocket import WebSocketNotifier


@receiver(post_save, sender=Alert)
def alert_websocket_notification(sender, instance, created, **kwargs):
    """Send WebSocket notification for alert changes"""
    try:
        org_id = str(instance.organization_id) if instance.organization_id else None
        
        alert_data = {
            'id': str(instance.id),
            'title': instance.title,
            'severity': instance.severity,
            'status': instance.status,
            'source': instance.source,
            'category': instance.category,
            'created_at': instance.created_at.isoformat(),
            'is_overdue': instance.is_overdue,
        }
        
        if created:
            WebSocketNotifier.notify_alert(alert_data, org_id)
        else:
            WebSocketNotifier.notify_alert_update(alert_data, org_id)
    except Exception:
        pass