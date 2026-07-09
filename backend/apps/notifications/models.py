# apps/notifications/models.py
import uuid
from django.db import models

class Notification(models.Model):
    """Notification records"""
    
    CHANNEL_CHOICES = [
        ('browser', 'Browser'),
        ('email', 'Email'),
        ('slack', 'Slack'),
        ('discord', 'Discord'),
        ('webhook', 'Webhook'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    
    # Content
    title = models.CharField(max_length=500)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Channel
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='browser')
    
    # Trigger
    trigger_type = models.CharField(max_length=100)
    trigger_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    action_url = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['channel', 'is_sent']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user}"


class NotificationChannel(models.Model):
    """Notification channel configurations"""
    
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('slack', 'Slack Webhook'),
        ('discord', 'Discord Webhook'),
        ('webhook', 'Custom Webhook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=50, choices=CHANNEL_TYPES)
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)
    
    # Configuration
    config = models.JSONField(default=dict)
    
    # Triggers
    notify_on_critical = models.BooleanField(default=True)
    notify_on_high = models.BooleanField(default=True)
    notify_on_incident = models.BooleanField(default=True)
    notify_on_agent_offline = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['channel_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"