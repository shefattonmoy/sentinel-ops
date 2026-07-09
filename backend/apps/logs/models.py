# apps/logs/models.py
import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex

class RawLog(models.Model):
    """Stores raw log entries received from agents"""
    
    LOG_LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    SOURCE_CHOICES = [
        ('auth', 'Authentication'),
        ('syslog', 'System Log'),
        ('nginx_access', 'Nginx Access'),
        ('nginx_error', 'Nginx Error'),
        ('docker', 'Docker'),
        ('django', 'Django'),
        ('application', 'Application'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='raw_logs'
    )
    
    # Log metadata
    timestamp = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, db_index=True)
    log_level = models.CharField(
        max_length=20, 
        choices=LOG_LEVEL_CHOICES, 
        null=True, 
        blank=True,
        db_index=True
    )
    
    # Log content
    raw_message = models.TextField()
    file_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Additional metadata
    hostname = models.CharField(max_length=255, null=True, blank=True)
    service = models.CharField(max_length=100, null=True, blank=True)
    
    # Processing status
    is_parsed = models.BooleanField(default=False, db_index=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    parse_error = models.TextField(null=True, blank=True)
    
    # Retention
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Hash for deduplication
    log_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
            models.Index(fields=['log_level', 'timestamp']),
            models.Index(fields=['is_parsed', 'created_at']),
        ]
        verbose_name = 'Raw Log'
        verbose_name_plural = 'Raw Logs'
    
    def __str__(self):
        return f"{self.source} - {self.timestamp} - {self.raw_message[:50]}"
    
    def save(self, *args, **kwargs):
        """Generate log hash for deduplication"""
        import hashlib
        if not self.log_hash:
            content = f"{self.agent_id}:{self.source}:{self.timestamp}:{self.raw_message}"
            self.log_hash = hashlib.sha256(content.encode()).hexdigest()
        super().save(*args, **kwargs)


class LogBatch(models.Model):
    """Tracks batches of logs received from agents"""
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='log_batches'
    )
    
    batch_size = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    
    logs_processed = models.IntegerField(default=0)
    events_generated = models.IntegerField(default=0)
    errors_encountered = models.IntegerField(default=0)
    
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    error_details = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Log Batch'
        verbose_name_plural = 'Log Batches'
    
    def __str__(self):
        return f"Batch from {self.agent.name} - {self.batch_size} logs - {self.status}"