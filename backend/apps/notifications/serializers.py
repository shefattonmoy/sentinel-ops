# apps/notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationChannel


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'organization', 'title', 'message',
            'priority', 'channel', 'trigger_type', 'trigger_id',
            'is_read', 'is_sent', 'sent_at', 'read_at',
            'metadata', 'action_url', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'read_at']


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'organization',
            'config', 'notify_on_critical', 'notify_on_high',
            'notify_on_incident', 'notify_on_agent_offline',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']