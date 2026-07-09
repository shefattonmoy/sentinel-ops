# apps/risk/models.py
import uuid
from django.db import models

class AssetRiskScore(models.Model):
    """Risk score for each asset"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=50)  # server, container, application
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    
    # Risk scores (0-100)
    overall_risk = models.FloatField(default=0)
    threat_risk = models.FloatField(default=0)
    vulnerability_risk = models.FloatField(default=0)
    exposure_risk = models.FloatField(default=0)
    impact_risk = models.FloatField(default=0)
    
    # Components
    recent_attacks = models.IntegerField(default=0)
    open_alerts = models.IntegerField(default=0)
    critical_events = models.IntegerField(default=0)
    exposed_ports = models.JSONField(default=list)
    running_services = models.JSONField(default=list)
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-overall_risk']