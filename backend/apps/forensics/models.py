# apps/forensics/models.py
import uuid
from django.db import models

class ForensicTimeline(models.Model):
    """Forensic timeline for hosts/IPs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host_identifier = models.CharField(max_length=255, db_index=True)  # IP or hostname
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class TimelineEntry(models.Model):
    """Individual timeline entry"""
    
    ENTRY_TYPES = [
        ('event', 'Security Event'),
        ('alert', 'Alert'),
        ('incident', 'Incident'),
        ('action', 'User Action'),
        ('system', 'System Change'),
        ('network', 'Network Activity'),
        ('file', 'File Change'),
        ('process', 'Process Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timeline = models.ForeignKey(ForensicTimeline, on_delete=models.CASCADE, related_name='entries')
    
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    timestamp = models.DateTimeField(db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, default='info')
    source = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['timestamp']