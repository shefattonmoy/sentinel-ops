# apps/alerts/serializers.py
from rest_framework import serializers
from .models import Alert, AlertComment, AlertHistory
from apps.events.serializers import EventSerializer

class AlertCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AlertComment
        fields = ['id', 'alert', 'user', 'user_name', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class AlertHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AlertHistory
        fields = ['id', 'alert', 'user', 'user_name', 'from_status', 'to_status', 'note', 'created_at']

class AlertSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    events_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'severity', 'status',
            'source', 'category',
            'organization', 'assigned_to', 'assigned_to_name',
            'resolved_by', 'resolved_by_name',
            'related_events', 'related_rule',
            'metadata', 'tags',
            'resolution',
            'created_at', 'updated_at',
            'acknowledged_at', 'resolved_at', 'closed_at',
            'sla_deadline', 'is_overdue',
            'events_count', 'comments_count',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'acknowledged_at', 'resolved_at', 'closed_at'
        ]
    
    def get_events_count(self, obj):
        return obj.related_events.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_is_overdue(self, obj):
        return obj.is_overdue

class AlertListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'severity', 'status', 'source',
            'category', 'assigned_to_name', 'created_at',
            'sla_deadline',
        ]

class AlertStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating alert status"""
    status = serializers.ChoiceField(choices=Alert.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    resolution = serializers.CharField(required=False, allow_blank=True)
    assigned_to = serializers.UUIDField(required=False)