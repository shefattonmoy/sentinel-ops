# apps/events/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EventStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time event streaming.
    Handles live event updates, alert notifications, and agent status changes.
    """
    
    async def connect(self):
        """Handle new WebSocket connection"""
        self.user = self.scope.get('user')
        self.room_group_name = None
        
        # Check authentication
        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: User not authenticated")
            await self.close(code=4001)
            return
        
        # Determine room group based on organization
        org_id = self.scope['url_route']['kwargs'].get('org_id')
        if org_id:
            self.room_group_name = f'org_{org_id}'
        elif self.user.organization_id:
            self.room_group_name = f'org_{self.user.organization_id}'
        else:
            self.room_group_name = f'user_{self.user.id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Also add to global events group
        await self.channel_layer.group_add(
            'global_events',
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"WebSocket connected: user={self.user.username}, group={self.room_group_name}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'message': 'Connected to SentinelOps real-time stream',
            'timestamp': timezone.now().isoformat(),
            'group': self.room_group_name,
            'user': self.user.username,
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        await self.channel_layer.group_discard(
            'global_events',
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: code={close_code}")
    
    async def receive(self, text_data):
        """Handle incoming messages from client"""
        try:
            data = json.loads(text_data)
            action = data.get('action', '')
            
            if action == 'subscribe':
                await self._handle_subscribe(data)
            elif action == 'unsubscribe':
                await self._handle_unsubscribe(data)
            elif action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat(),
                }))
            elif action == 'filter':
                await self._handle_filter(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown action: {action}',
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
            }))
    
    async def _handle_subscribe(self, data):
        """Subscribe to specific event types"""
        event_types = data.get('event_types', [])
        self.subscribed_events = event_types
        
        await self.send(text_data=json.dumps({
            'type': 'subscription.updated',
            'subscribed_events': event_types,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def _handle_unsubscribe(self, data):
        """Unsubscribe from events"""
        self.subscribed_events = []
        
        await self.send(text_data=json.dumps({
            'type': 'subscription.cleared',
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def _handle_filter(self, data):
        """Update event filters"""
        self.event_filters = data.get('filters', {})
        
        await self.send(text_data=json.dumps({
            'type': 'filters.updated',
            'filters': self.event_filters,
            'timestamp': timezone.now().isoformat(),
        }))
    
    # ============ Event Handlers (called by channel layer) ============
    
    async def event_new(self, event):
        """Handle new event notification"""
        event_data = event.get('data', {})
        
        # Check if client subscribed to this event type
        if hasattr(self, 'subscribed_events') and self.subscribed_events:
            if event_data.get('event_type') not in self.subscribed_events:
                return
        
        # Check filters
        if hasattr(self, 'event_filters') and self.event_filters:
            if not self._matches_filters(event_data, self.event_filters):
                return
        
        await self.send(text_data=json.dumps({
            'type': 'event.new',
            'data': event_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def event_batch(self, event):
        """Handle batch of events"""
        events = event.get('data', [])
        
        await self.send(text_data=json.dumps({
            'type': 'event.batch',
            'data': events,
            'count': len(events),
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def alert_new(self, event):
        """Handle new alert notification"""
        alert_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'alert.new',
            'data': alert_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def alert_update(self, event):
        """Handle alert status update"""
        alert_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'alert.updated',
            'data': alert_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def incident_new(self, event):
        """Handle new incident notification"""
        incident_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'incident.new',
            'data': incident_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def incident_update(self, event):
        """Handle incident status update"""
        incident_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'incident.updated',
            'data': incident_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def agent_status(self, event):
        """Handle agent status change"""
        agent_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'agent.status_changed',
            'data': agent_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def notification(self, event):
        """Handle browser notification"""
        notification_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': notification_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def dashboard_update(self, event):
        """Handle dashboard statistics update"""
        dashboard_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'dashboard.updated',
            'data': dashboard_data,
            'timestamp': timezone.now().isoformat(),
        }))
    
    def _matches_filters(self, event_data, filters):
        """Check if event matches client filters"""
        for key, value in filters.items():
            if key in event_data:
                if isinstance(value, list):
                    if event_data[key] not in value:
                        return False
                elif event_data[key] != value:
                    return False
        return True


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for notifications only"""
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Personal notification channel
        self.room_group_name = f'notifications_user_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread count
        unread_count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification.unread_count',
            'count': unread_count,
        }))
    
    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def notification_new(self, event):
        """Handle new notification"""
        await self.send(text_data=json.dumps({
            'type': 'notification.new',
            'data': event.get('data', {}),
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def notification_badge(self, event):
        """Update notification badge count"""
        await self.send(text_data=json.dumps({
            'type': 'notification.badge',
            'count': event.get('count', 0),
        }))
    
    @database_sync_to_async
    def _get_unread_count(self):
        """Get unread notification count"""
        from apps.notifications.models import Notification
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()