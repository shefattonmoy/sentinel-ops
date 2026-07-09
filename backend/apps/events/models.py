# apps/events/models.py
import uuid
from django.db import models

class Event(models.Model):
    """Normalized security events generated from parsed logs"""
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    EVENT_CATEGORIES = [
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('network', 'Network'),
        ('system', 'System'),
        ('application', 'Application'),
        ('container', 'Container'),
        ('security', 'Security'),
        ('compliance', 'Compliance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    raw_log = models.ForeignKey(
        'logs.RawLog',
        on_delete=models.CASCADE,
        related_name='events',
        null=True
    )
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    # Event identification
    timestamp = models.DateTimeField(db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    category = models.CharField(
        max_length=50,
        choices=EVENT_CATEGORIES,
        default='system',
        db_index=True
    )
    
    # Severity and impact
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        db_index=True
    )
    confidence = models.FloatField(default=1.0)  # 0.0 to 1.0
    
    # Source information
    source = models.CharField(max_length=50, db_index=True)
    service = models.CharField(max_length=50, null=True, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    source_port = models.IntegerField(null=True, blank=True)
    source_hostname = models.CharField(max_length=255, null=True, blank=True)
    
    # Target information
    target_ip = models.GenericIPAddressField(null=True, blank=True)
    target_port = models.IntegerField(null=True, blank=True)
    target_hostname = models.CharField(max_length=255, null=True, blank=True)
    
    # User information
    username = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Event details
    message = models.TextField()
    description = models.TextField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    
    # Correlation
    correlation_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    parent_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_events'
    )
    
    # Processing
    is_analyzed = models.BooleanField(default=False, db_index=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['source_ip', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['agent', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['is_analyzed', 'timestamp']),
        ]
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.source_ip or self.username or 'N/A'} - {self.timestamp}"

class EventCorrelation(models.Model):
    """Stores correlations between events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    events = models.ManyToManyField(Event, related_name='correlations')
    
    correlation_type = models.CharField(max_length=100)
    description = models.TextField()
    confidence = models.FloatField(default=0.5)
    
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event Correlation'
        verbose_name_plural = 'Event Correlations'