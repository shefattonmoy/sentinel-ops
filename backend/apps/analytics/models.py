# apps/analytics/models.py
import uuid
from django.db import models

class UserBehaviorProfile(models.Model):
    """Baseline behavior profile for a user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='behavior_profile')
    
    avg_login_time = models.TimeField(null=True)
    common_ips = models.JSONField(default=list)
    common_hosts = models.JSONField(default=list)
    login_frequency_per_day = models.FloatField(default=0)
    common_commands = models.JSONField(default=list)
    sudo_frequency = models.FloatField(default=0)
    anomaly_score = models.FloatField(default=0)
    risk_level = models.CharField(max_length=20, default='low')
    total_events_analyzed = models.IntegerField(default=0)
    last_analyzed = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BehaviorAnomaly(models.Model):
    """Detected behavioral anomaly"""
    ANOMALY_TYPES = [
        ('unusual_login_time', 'Unusual Login Time'),
        ('unusual_ip', 'Unusual IP Address'),
        ('unusual_command', 'Unusual Command'),
        ('high_activity', 'High Activity Volume'),
        ('new_host', 'New Host Access'),
        ('privilege_escalation', 'Privilege Escalation Attempt'),
        ('data_exfil', 'Potential Data Exfiltration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='medium')
    confidence = models.FloatField(default=0.5)
    metadata = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    detected_at = models.DateTimeField(auto_now_add=True)