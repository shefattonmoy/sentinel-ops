# apps/events/websocket.py
"""
WebSocket notification helper.
Used by views/signals to send real-time updates to connected clients.
"""
import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class WebSocketNotifier:
    """Send real-time notifications via WebSocket to connected clients"""
    
    @staticmethod
    def _send_to_group(group_name, message_type, data):
        """Send message to a channel group"""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    'data': data,
                }
            )
        except Exception as e:
            logger.error(f"WebSocket send failed: {e}")
    
    @staticmethod
    def notify_event(event_data, organization_id=None):
        """
        Send new event notification.
        Called when a new event is created.
        """
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'event_new', event_data)
        
        # Also send to global group
        WebSocketNotifier._send_to_group('global_events', 'event_new', event_data)
    
    @staticmethod
    def notify_event_batch(events, organization_id=None):
        """Send batch of events"""
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'event_batch', events)
        
        WebSocketNotifier._send_to_group('global_events', 'event_batch', events)
    
    @staticmethod
    def notify_alert(alert_data, organization_id=None):
        """
        Send new alert notification.
        Called when a new alert is created.
        """
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'alert_new', alert_data)
        
        WebSocketNotifier._send_to_group('global_events', 'alert_new', alert_data)
    
    @staticmethod
    def notify_alert_update(alert_data, organization_id=None):
        """Send alert status update"""
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'alert_update', alert_data)
        
        WebSocketNotifier._send_to_group('global_events', 'alert_update', alert_data)
    
    @staticmethod
    def notify_incident(incident_data, organization_id=None):
        """
        Send new incident notification.
        Called when a new incident is created.
        """
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'incident_new', incident_data)
        
        WebSocketNotifier._send_to_group('global_events', 'incident_new', incident_data)
    
    @staticmethod
    def notify_incident_update(incident_data, organization_id=None):
        """Send incident status update"""
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'incident_update', incident_data)
        
        WebSocketNotifier._send_to_group('global_events', 'incident_update', incident_data)
    
    @staticmethod
    def notify_agent_status(agent_data, organization_id=None):
        """
        Send agent status change notification.
        Called when agent goes online/offline/degraded.
        """
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'agent_status', agent_data)
        
        WebSocketNotifier._send_to_group('global_events', 'agent_status', agent_data)
    
    @staticmethod
    def notify_user(user_id, notification_data):
        """
        Send personal notification to a specific user.
        """
        group = f'notifications_user_{user_id}'
        WebSocketNotifier._send_to_group(group, 'notification_new', notification_data)
    
    @staticmethod
    def notify_dashboard_update(dashboard_data, organization_id=None):
        """Send dashboard statistics update"""
        if organization_id:
            group = f'org_{organization_id}'
            WebSocketNotifier._send_to_group(group, 'dashboard_update', dashboard_data)
        
        WebSocketNotifier._send_to_group('global_events', 'dashboard_update', dashboard_data)
    
    @staticmethod
    def notify_badge_update(user_id, count):
        """Update notification badge count for a user"""
        group = f'notifications_user_{user_id}'
        WebSocketNotifier._send_to_group(group, 'notification_badge', {'count': count})