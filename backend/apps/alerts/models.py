# apps/alerts/models.py
import uuid
from django.db import models
from django.utils import timezone

class Alert(models.Model):
    """Security alerts generated from detection rules"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('false_positive', 'False Positive'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Alert details
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    
    # Source information
    source = models.CharField(max_length=100, db_index=True)  # rule_engine, manual, agent
    category = models.CharField(max_length=100, default='security', db_index=True)
    
    # Relationships
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts'
    )
    
    # Related objects
    related_events = models.ManyToManyField('events.Event', blank=True, related_name='alerts')
    related_rule = models.ForeignKey(
        'rules.DetectionRule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    
    # Alert data
    metadata = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_deadline = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['source', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['organization', 'created_at']),
        ]
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
    
    def __str__(self):
        return f"{self.title} - {self.severity} - {self.status}"
    
    def acknowledge(self, user=None):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        if user:
            self.assigned_to = user
        self.save()
    
    def start_investigation(self):
        """Mark alert as under investigation"""
        self.status = 'investigating'
        self.save()
    
    def resolve(self, resolution='', user=None):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolution = resolution
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save()
    
    def close(self):
        """Close the alert"""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save()
    
    def mark_false_positive(self):
        """Mark as false positive"""
        self.status = 'false_positive'
        self.resolved_at = timezone.now()
        self.save()
    
    def set_sla_deadline(self):
        """Set SLA deadline based on severity"""
        sla_times = {
            'critical': 15,  # 15 minutes
            'high': 60,      # 1 hour
            'medium': 240,   # 4 hours
            'low': 480,      # 8 hours
            'info': 1440,    # 24 hours
        }
        minutes = sla_times.get(self.severity, 240)
        self.sla_deadline = timezone.now() + models.timedelta(minutes=minutes)
        self.save()


class AlertComment(models.Model):
    """Comments on alerts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    comment = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Alert Comment'
        verbose_name_plural = 'Alert Comments'
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.alert.title}"


class AlertHistory(models.Model):
    """History of alert status changes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    from_status = models.CharField(max_length=20, null=True, blank=True)
    to_status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert History'
        verbose_name_plural = 'Alert Histories'
    
    def __str__(self):
        return f"{self.alert.title}: {self.from_status} -> {self.to_status}"