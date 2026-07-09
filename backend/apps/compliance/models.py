# apps/compliance/models.py
import uuid
from django.db import models

class ComplianceFramework(models.Model):
    """Compliance framework (SOC2, ISO27001, GDPR)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class ComplianceControl(models.Model):
    """Individual compliance control"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='controls')
    control_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    
    # Mapping to SentinelOps features
    mapped_events = models.JSONField(default=list)  # Event types that prove this control
    mapped_rules = models.JSONField(default=list)   # Rules that enforce this control
    
    class Meta:
        unique_together = ['framework', 'control_id']

class ComplianceEvidence(models.Model):
    """Auto-generated compliance evidence"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control = models.ForeignKey(ComplianceControl, on_delete=models.CASCADE, related_name='evidence')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)
    
    evidence_type = models.CharField(max_length=50)  # event_log, alert, configuration
    description = models.TextField()
    data = models.JSONField(default=dict)
    
    collected_at = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()