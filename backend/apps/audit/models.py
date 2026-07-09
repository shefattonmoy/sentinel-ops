# apps/audit/models.py
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """Audit trail for all important actions"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('EXPORT', 'Export'),
        ('VIEW', 'View'),
        ('CONFIG_CHANGE', 'Configuration Change'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('STATUS_CHANGE', 'Status Change'),
        ('2FA_SETUP', '2FA Setup'),
        ('2FA_DISABLE', '2FA Disable'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('AGENT_REGISTER', 'Agent Register'),
        ('AGENT_DELETE', 'Agent Delete'),
        ('RULE_EXECUTE', 'Rule Execute'),
        ('ALERT_CREATE', 'Alert Create'),
        ('INCIDENT_CREATE', 'Incident Create'),
        ('REPORT_GENERATE', 'Report Generate'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who did the action
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=255, blank=True)  # In case user is deleted
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # What action was performed
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    description = models.TextField()
    
    # What object was affected
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=500, blank=True)  # String representation
    
    # Additional data
    metadata = models.JSONField(default=dict)
    changes = models.JSONField(default=dict)  # Track what changed
    
    # Organization
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.action} by {self.username or self.user} at {self.timestamp}"


def log_action(user, action, description='', obj=None, severity='info', metadata=None, changes=None, request=None):
    """Helper function to create audit log entries"""
    log_entry = AuditLog(
        user=user if user and user.is_authenticated else None,
        username=user.username if user and user.is_authenticated else 'Anonymous',
        ip_address=get_client_ip(request) if request else None,
        action=action,
        severity=severity,
        description=description,
        object_repr=str(obj) if obj else '',
        metadata=metadata or {},
        changes=changes or {},
        organization=user.organization if user and user.is_authenticated and hasattr(user, 'organization') else None,
    )
    
    if obj:
        log_entry.content_type = ContentType.objects.get_for_model(obj)
        log_entry.object_id = str(obj.pk) if hasattr(obj, 'pk') else ''
    
    log_entry.save()
    return log_entry


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR') if request else None
    return ip