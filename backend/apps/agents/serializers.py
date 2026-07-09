# apps/agents/serializers.py
from rest_framework import serializers
from django.utils import timezone
import uuid
import hashlib
import secrets
from .models import Agent, AgentHeartbeat, AgentConfiguration, AgentGroup

class AgentHeartbeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentHeartbeat
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class AgentConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentConfiguration
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    uptime = serializers.SerializerMethodField()
    heartbeat_info = serializers.SerializerMethodField()
    config = AgentConfigurationSerializer(source='configuration', read_only=True)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'agent_id', 'name', 'hostname', 'version',
            'agent_type', 'status', 'is_online', 'uptime',
            'os_info', 'ip_address', 'mac_address',
            'cpu_usage', 'memory_usage', 'disk_usage',
            'last_heartbeat', 'missed_heartbeats',
            'total_logs_collected', 'total_events_generated',
            'total_alerts_triggered',
            'monitored_logs', 'tags',
            'heartbeat_info', 'config',
            'error_count', 'last_error_time',
            'created_at', 'updated_at',
            'is_active',
        ]
        read_only_fields = [
            'id', 'agent_id', 'token', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'token': {'write_only': True}
        }
    
    def get_is_online(self, obj):
        return obj.is_online()
    
    def get_uptime(self, obj):
        return obj.get_uptime()
    
    def get_heartbeat_info(self, obj):
        last_hb = obj.heartbeats.first()
        if last_hb:
            return AgentHeartbeatSerializer(last_hb).data
        return None


class AgentRegistrationSerializer(serializers.Serializer):
    """Serializer for agent registration request"""
    name = serializers.CharField(max_length=255)
    hostname = serializers.CharField(max_length=255)
    version = serializers.CharField(max_length=20, default='1.0.0')
    agent_type = serializers.CharField(max_length=20, default='linux')
    os_info = serializers.JSONField(default=dict)
    ip_address = serializers.IPAddressField(required=False)
    mac_address = serializers.CharField(max_length=50, required=False)
    monitored_logs = serializers.JSONField(default=list)
    tags = serializers.JSONField(default=list)
    
    def validate_hostname(self, value):
        """Validate hostname format"""
        if not value.strip():
            raise serializers.ValidationError("Hostname cannot be empty")
        return value.lower().strip()
    
    def validate_name(self, value):
        """Validate agent name"""
        if not value.strip():
            raise serializers.ValidationError("Agent name cannot be empty")
        return value.strip()


class AgentRegistrationResponseSerializer(serializers.Serializer):
    """Serializer for agent registration response"""
    agent_id = serializers.CharField()
    token = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()
    server_url = serializers.CharField()
    config = serializers.DictField()


class HeartbeatSerializer(serializers.Serializer):
    """Serializer for heartbeat data"""
    # System metrics
    cpu_usage = serializers.FloatField(required=False)
    cpu_cores = serializers.IntegerField(required=False)
    cpu_model = serializers.CharField(required=False, max_length=255)
    
    memory_usage = serializers.FloatField(required=False)
    memory_total = serializers.IntegerField(required=False)
    memory_used = serializers.IntegerField(required=False)
    memory_free = serializers.IntegerField(required=False)
    
    disk_usage = serializers.FloatField(required=False)
    disk_total = serializers.IntegerField(required=False)
    disk_used = serializers.IntegerField(required=False)
    disk_free = serializers.IntegerField(required=False)
    disk_partitions = serializers.ListField(required=False)
    
    network_io = serializers.DictField(required=False)
    network_interfaces = serializers.ListField(required=False)
    network_connections = serializers.IntegerField(required=False)
    
    process_count = serializers.IntegerField(required=False)
    zombie_processes = serializers.IntegerField(required=False)
    
    uptime = serializers.FloatField(required=False)
    load_average = serializers.DictField(required=False)
    boot_time = serializers.DateTimeField(required=False)
    
    # Agent metrics
    buffer_size = serializers.IntegerField(required=False)
    logs_collected = serializers.IntegerField(default=0)
    events_generated = serializers.IntegerField(default=0)
    errors_encountered = serializers.IntegerField(default=0)


class AgentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating agent information"""
    class Meta:
        model = Agent
        fields = [
            'name', 'monitored_logs', 'tags',
            'heartbeat_interval', 'is_active'
        ]


class AgentGroupSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()
    online_count = serializers.SerializerMethodField()
    offline_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentGroup
        fields = [
            'id', 'name', 'description', 'agents',
            'tags', 'agent_count', 'online_count',
            'offline_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_agent_count(self, obj):
        return obj.agents.count()
    
    def get_online_count(self, obj):
        return obj.online_count()
    
    def get_offline_count(self, obj):
        return obj.offline_count()


class AgentStatsSerializer(serializers.Serializer):
    """Serializer for agent statistics"""
    total_agents = serializers.IntegerField()
    online_agents = serializers.IntegerField()
    offline_agents = serializers.IntegerField()
    degraded_agents = serializers.IntegerField()
    error_agents = serializers.IntegerField()
    total_logs_collected = serializers.IntegerField()
    total_events_generated = serializers.IntegerField()
    total_alerts_triggered = serializers.IntegerField()
    avg_cpu_usage = serializers.FloatField()
    avg_memory_usage = serializers.FloatField()
    avg_disk_usage = serializers.FloatField()