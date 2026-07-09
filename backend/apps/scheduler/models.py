# apps/scheduler/models.py
import uuid
from django.db import models

class ExportSchedule(models.Model):
    """Scheduled data exports"""
    
    EXPORT_TYPES = [
        ('events', 'Events'),
        ('alerts', 'Alerts'),
        ('incidents', 'Incidents'),
        ('report', 'Report'),
        ('audit', 'Audit Log'),
    ]
    
    FORMATS = [('csv', 'CSV'), ('json', 'JSON'), ('pdf', 'PDF')]
    
    FREQUENCIES = [
        ('hourly', 'Every Hour'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DESTINATIONS = [
        ('email', 'Email'),
        ('s3', 'Amazon S3'),
        ('webhook', 'Webhook'),
        ('local', 'Local Storage'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    
    export_type = models.CharField(max_length=50, choices=EXPORT_TYPES)
    format = models.CharField(max_length=20, choices=FORMATS, default='csv')
    frequency = models.CharField(max_length=20, choices=FREQUENCIES, default='daily')
    destination = models.CharField(max_length=20, choices=DESTINATIONS, default='email')
    
    # Configuration
    destination_config = models.JSONField(default=dict)  # email addresses, S3 bucket, webhook URL
    filters = models.JSONField(default=dict)  # date range, severity, etc.
    
    # Scheduling
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True)
    next_run = models.DateTimeField(null=True)
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"


class ExportRun(models.Model):
    """Execution history of exports"""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(ExportSchedule, on_delete=models.CASCADE, related_name='runs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    file_url = models.URLField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True)
    record_count = models.IntegerField(null=True)
    error_message = models.TextField(null=True, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-started_at']