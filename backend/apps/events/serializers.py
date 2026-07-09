# apps/events/serializers.py
from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'raw_log', 'agent', 'agent_name', 'agent_hostname',
            'timestamp', 'event_type', 'category', 'severity', 'confidence',
            'source', 'service',
            'source_ip', 'source_port', 'source_hostname',
            'target_ip', 'target_port', 'target_hostname',
            'username', 'user_id',
            'message', 'description',
            'metadata', 'tags',
            'correlation_id', 'parent_event',
            'is_analyzed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class EventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'timestamp', 'event_type', 'severity',
            'source', 'source_ip', 'username',
            'message', 'agent_name', 'created_at'
        ]