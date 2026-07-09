# apps/threat_intel/models.py
import uuid
from django.db import models

class ThreatScore(models.Model):
    """AI-powered threat scoring for events and IPs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Target
    source_ip = models.GenericIPAddressField(db_index=True)
    event_type = models.CharField(max_length=100, null=True)
    
    # Scores (0-100)
    threat_score = models.FloatField(default=0)  # Overall threat level
    frequency_score = models.FloatField(default=0)  # Based on event frequency
    severity_score = models.FloatField(default=0)  # Based on event severity
    pattern_score = models.FloatField(default=0)  # Based on attack patterns
    reputation_score = models.FloatField(default=0)  # Based on IP reputation
    
    # Metadata
    total_events = models.IntegerField(default=0)
    unique_event_types = models.IntegerField(default=0)
    first_seen = models.DateTimeField(null=True)
    last_seen = models.DateTimeField(null=True)
    is_known_attacker = models.BooleanField(default=False)
    
    # Risk level
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='low',
        db_index=True
    )
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['source_ip', 'organization']
        ordering = ['-threat_score']
        indexes = [
            models.Index(fields=['source_ip']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['threat_score']),
        ]
    
    def __str__(self):
        return f"{self.source_ip} - Score: {self.threat_score} ({self.risk_level})"


class IPReputation(models.Model):
    """IP reputation database"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    
    reputation_score = models.IntegerField(default=50)  # 0-100, lower = worse
    abuse_confidence = models.IntegerField(default=0)  # 0-100
    is_tor = models.BooleanField(default=False)
    is_proxy = models.BooleanField(default=False)
    is_vpn = models.BooleanField(default=False)
    is_datacenter = models.BooleanField(default=False)
    country = models.CharField(max_length=100, null=True)
    isp = models.CharField(max_length=255, null=True)
    domain = models.CharField(max_length=255, null=True)
    
    usage_type = models.CharField(max_length=100, null=True)
    last_reported = models.DateTimeField(null=True)
    report_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['abuse_confidence']
    
    def __str__(self):
        return f"{self.ip_address} - Rep: {self.reputation_score}"