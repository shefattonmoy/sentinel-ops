# apps/logs/serializers.py
from rest_framework import serializers
from .models import RawLog, LogBatch

class RawLogSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)
    
    class Meta:
        model = RawLog
        fields = [
            'id', 'agent', 'agent_name', 'agent_hostname',
            'timestamp', 'source', 'log_level',
            'raw_message', 'file_path', 'hostname', 'service',
            'is_parsed', 'parsed_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_parsed', 'parsed_at', 'created_at']


class LogIngestionSerializer(serializers.Serializer):
    """Serializer for log ingestion request"""
    agent = serializers.CharField(max_length=255)
    hostname = serializers.CharField(max_length=255)
    logs = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=1000  # Maximum batch size
    )
    
    def validate_logs(self, value):
        """Validate each log entry"""
        validated_logs = []
        for log in value:
            if 'message' not in log:
                raise serializers.ValidationError("Each log must have a 'message' field")
            
            validated_log = {
                'timestamp': log.get('timestamp'),
                'source': log.get('source', 'unknown'),
                'level': log.get('level'),
                'message': log.get('message'),
                'path': log.get('path'),
                'service': log.get('service'),
            }
            validated_logs.append(validated_log)
        
        return validated_logs


class LogBatchSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = LogBatch
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'completed_at']


class LogSearchSerializer(serializers.Serializer):
    """Serializer for log search queries"""
    query = serializers.CharField(required=False, allow_blank=True)
    sources = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    log_levels = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    agent_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=50, min_value=1, max_value=1000)