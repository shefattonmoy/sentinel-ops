# apps/agents/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class Agent(models.Model):
    """Main agent model for registered monitoring agents"""
    
    AGENT_STATUS = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('degraded', 'Degraded'),
        ('error', 'Error'),
    ]
    
    AGENT_TYPE = [
        ('linux', 'Linux Server'),
        ('docker', 'Docker Host'),
        ('kubernetes', 'Kubernetes Node'),
        ('custom', 'Custom'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Relationships
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='agents',
        null=True,
        blank=True
    )
    
    # Agent metadata
    version = models.CharField(max_length=20, default='1.0.0')
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPE, default='linux')
    status = models.CharField(max_length=20, choices=AGENT_STATUS, default='offline', db_index=True)
    
    # System info
    os_info = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, null=True, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    monitored_logs = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Heartbeat tracking
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    heartbeat_interval = models.IntegerField(default=30)  # seconds
    missed_heartbeats = models.IntegerField(default=0)
    
    # Health status
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    network_status = models.CharField(max_length=50, null=True, blank=True)
    
    # Statistics
    total_logs_collected = models.BigIntegerField(default=0)
    total_events_generated = models.BigIntegerField(default=0)
    total_alerts_triggered = models.BigIntegerField(default=0)
    uptime_seconds = models.BigIntegerField(default=0)
    
    # Error tracking
    last_error = models.TextField(null=True, blank=True)
    last_error_time = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_heartbeat']
        indexes = [
            models.Index(fields=['agent_id']),
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['organization']),
            models.Index(fields=['hostname']),
            models.Index(fields=['last_heartbeat']),
        ]
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
    
    def __str__(self):
        return f"{self.name} ({self.hostname}) - {self.status}"
    
    def is_online(self):
        """Check if agent is online based on last heartbeat"""
        if not self.last_heartbeat:
            return False
        
        # Agent is online if last heartbeat was within 2 * heartbeat_interval
        threshold = timezone.now() - timedelta(seconds=self.heartbeat_interval * 2)
        return self.last_heartbeat > threshold
    
    def get_uptime(self):
        """Calculate agent uptime"""
        if not self.last_heartbeat or self.status == 'offline':
            return 0
        return int((timezone.now() - self.created_at).total_seconds())
    
    def mark_offline(self):
        """Mark agent as offline"""
        self.status = 'offline'
        self.missed_heartbeats += 1
        self.save(update_fields=['status', 'missed_heartbeats'])
    
    def mark_online(self):
        """Mark agent as online"""
        self.status = 'online'
        self.missed_heartbeats = 0
        self.last_heartbeat = timezone.now()
        self.save(update_fields=['status', 'missed_heartbeats', 'last_heartbeat'])
    
    def record_error(self, error_message: str):
        """Record an agent error"""
        self.last_error = error_message
        self.last_error_time = timezone.now()
        self.error_count += 1
        
        if self.error_count > 10:
            self.status = 'error'
        
        self.save(update_fields=['last_error', 'last_error_time', 'error_count', 'status'])


class AgentHeartbeat(models.Model):
    """Detailed heartbeat information from agents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='heartbeats'
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # System metrics
    cpu_usage = models.FloatField(null=True, blank=True)
    cpu_cores = models.IntegerField(null=True, blank=True)
    cpu_model = models.CharField(max_length=255, null=True, blank=True)
    
    memory_usage = models.FloatField(null=True, blank=True)
    memory_total = models.BigIntegerField(null=True, blank=True)
    memory_used = models.BigIntegerField(null=True, blank=True)
    memory_free = models.BigIntegerField(null=True, blank=True)
    
    disk_usage = models.FloatField(null=True, blank=True)
    disk_total = models.BigIntegerField(null=True, blank=True)
    disk_used = models.BigIntegerField(null=True, blank=True)
    disk_free = models.BigIntegerField(null=True, blank=True)
    disk_partitions = models.JSONField(default=list, blank=True)
    
    # Network metrics
    network_io = models.JSONField(default=dict, blank=True)
    network_interfaces = models.JSONField(default=list, blank=True)
    network_connections = models.IntegerField(null=True, blank=True)
    
    # Process metrics
    process_count = models.IntegerField(null=True, blank=True)
    zombie_processes = models.IntegerField(null=True, blank=True)
    
    # System info
    uptime = models.FloatField(null=True, blank=True)
    load_average = models.JSONField(default=dict, blank=True)
    boot_time = models.DateTimeField(null=True, blank=True)
    
    # Agent metrics
    buffer_size = models.IntegerField(null=True, blank=True)
    logs_collected = models.IntegerField(default=0)
    events_generated = models.IntegerField(default=0)
    errors_encountered = models.IntegerField(default=0)
    
    # Status flags
    is_healthy = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        verbose_name = 'Agent Heartbeat'
        verbose_name_plural = 'Agent Heartbeats'
    
    def __str__(self):
        return f"{self.agent.name} heartbeat at {self.timestamp}"


class AgentConfiguration(models.Model):
    """Agent configuration profiles"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField(
        Agent,
        on_delete=models.CASCADE,
        related_name='configuration'
    )
    
    # Log monitoring settings
    monitored_logs = models.JSONField(default=list, blank=True)
    log_batch_size = models.IntegerField(default=100)
    log_buffer_max_size = models.IntegerField(default=10000)
    log_level_filter = models.CharField(
        max_length=20,
        choices=[
            ('DEBUG', 'Debug'),
            ('INFO', 'Info'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical'),
        ],
        default='INFO'
    )
    
    # Collection intervals
    heartbeat_interval = models.IntegerField(default=30)
    metrics_interval = models.IntegerField(default=60)
    log_collection_interval = models.IntegerField(default=10)
    
    # Retry settings
    max_retries = models.IntegerField(default=5)
    retry_delay = models.IntegerField(default=5)
    retry_backoff = models.FloatField(default=2.0)
    
    # Notification settings
    notify_on_offline = models.BooleanField(default=True)
    notify_on_error = models.BooleanField(default=True)
    notify_on_high_cpu = models.BooleanField(default=False)
    cpu_threshold = models.FloatField(default=90.0)
    notify_on_high_memory = models.BooleanField(default=False)
    memory_threshold = models.FloatField(default=90.0)
    
    # Advanced settings
    enable_compression = models.BooleanField(default=True)
    enable_encryption = models.BooleanField(default=True)
    enable_docker_monitoring = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Agent Configuration'
        verbose_name_plural = 'Agent Configurations'
    
    def __str__(self):
        return f"Configuration for {self.agent.name}"


class AgentGroup(models.Model):
    """Group agents for easier management"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='agent_groups',
        null=True
    )
    agents = models.ManyToManyField(Agent, related_name='groups')
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Agent Group'
        verbose_name_plural = 'Agent Groups'
    
    def __str__(self):
        return f"{self.name} ({self.agents.count()} agents)"
    
    def online_count(self):
        return self.agents.filter(status='online').count()
    
    def offline_count(self):
        return self.agents.filter(status='offline').count()