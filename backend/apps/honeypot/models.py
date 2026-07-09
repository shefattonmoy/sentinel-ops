# apps/honeypot/models.py
import uuid
from django.db import models

class Honeypot(models.Model):
    """Honeypot deployment"""
    
    PROTOCOLS = [('ssh', 'SSH'), ('http', 'HTTP'), ('ftp', 'FTP'), ('mysql', 'MySQL'), ('telnet', 'Telnet')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    protocol = models.CharField(max_length=20, choices=PROTOCOLS)
    port = models.IntegerField()
    host = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class HoneypotInteraction(models.Model):
    """Captured honeypot interactions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    honeypot = models.ForeignKey(Honeypot, on_delete=models.CASCADE, related_name='interactions')
    
    source_ip = models.GenericIPAddressField(db_index=True)
    source_port = models.IntegerField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    interaction_type = models.CharField(max_length=50)  # connection, login_attempt, command
    payload = models.TextField(blank=True)
    headers = models.JSONField(default=dict)
    
    # Analysis
    is_malicious = models.BooleanField(default=True)
    threat_level = models.CharField(max_length=20, default='high')
    attack_pattern = models.CharField(max_length=100, blank=True)