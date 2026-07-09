# apps/incidents/serializers.py
from rest_framework import serializers
from .models import Incident, IncidentTimeline, IncidentNote
from apps.alerts.serializers import AlertSerializer
from apps.events.serializers import EventSerializer

class IncidentTimelineSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = IncidentTimeline
        fields = '__all__'
        read_only_fields = ['id']

class IncidentNoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = IncidentNote
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class IncidentSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source='assigned_to.username', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.username', 
        read_only=True
    )
    alerts_count = serializers.SerializerMethodField()
    events_count = serializers.SerializerMethodField()
    timeline_count = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'incident_type',
            'severity', 'status', 'priority',
            'organization', 'assigned_to', 'assigned_to_name',
            'assigned_team',
            'alerts', 'events',
            'correlation_rule', 'correlation_id', 'correlation_confidence',
            'affected_systems', 'affected_users', 'impact_scope',
            'source_ip', 'source_hostname', 'attack_vector',
            'evidence', 'artifacts', 'indicators_of_compromise',
            'detected_at', 'started_at', 'contained_at',
            'eradicated_at', 'recovered_at',
            'resolution', 'resolution_type', 'root_cause', 'lessons_learned',
            'time_to_detect', 'time_to_contain', 'time_to_resolve',
            'sla_deadline', 'is_overdue', 'is_critical',
            'metadata', 'tags',
            'alerts_count', 'events_count', 'timeline_count', 'notes_count',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'created_by', 'created_by_name',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'time_to_detect', 'time_to_contain', 'time_to_resolve'
        ]
    
    def get_alerts_count(self, obj):
        return obj.alerts.count()
    
    def get_events_count(self, obj):
        return obj.events.count()
    
    def get_timeline_count(self, obj):
        return obj.timeline.count()
    
    def get_notes_count(self, obj):
        return obj.notes.count()
    
    def get_is_overdue(self, obj):
        return obj.is_overdue

class IncidentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    assigned_to_name = serializers.CharField(
        source='assigned_to.username', 
        read_only=True
    )
    alerts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'incident_type', 'severity',
            'status', 'priority', 'assigned_to_name',
            'source_ip', 'detected_at', 'sla_deadline',
            'alerts_count', 'created_at',
        ]
    
    def get_alerts_count(self, obj):
        return obj.alerts.count()

class IncidentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Incident.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    resolution = serializers.CharField(required=False, allow_blank=True)
    assigned_to = serializers.UUIDField(required=False)

class CorrelateAlertsSerializer(serializers.Serializer):
    """Serializer for alert correlation request"""
    alert_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    auto_correlate = serializers.BooleanField(default=True)
    pattern = serializers.CharField(required=False)