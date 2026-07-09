# apps/mitre/models.py
import uuid
from django.db import models

class MitreTechnique(models.Model):
    """MITRE ATT&CK techniques"""
    
    technique_id = models.CharField(max_length=20, unique=True)  # e.g., T1110
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tactic = models.CharField(max_length=100)  # e.g., Credential Access
    platform = models.CharField(max_length=100, blank=True)
    data_sources = models.JSONField(default=list)
    detection_recommendations = models.TextField(blank=True)
    
    class Meta:
        ordering = ['technique_id']
    
    def __str__(self):
        return f"{self.technique_id} - {self.name}"

class EventTechniqueMapping(models.Model):
    """Maps event types to MITRE techniques"""
    
    event_type = models.CharField(max_length=100, unique=True)
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.8)
    
    class Meta:
        ordering = ['event_type']
    
    def __str__(self):
        return f"{self.event_type} → {self.technique.technique_id}"

class MitreCoverage(models.Model):
    """Tracks detection coverage for MITRE techniques"""
    
    technique = models.ForeignKey(MitreTechnique, on_delete=models.CASCADE)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)
    detected_events = models.IntegerField(default=0)
    last_detected = models.DateTimeField(null=True)
    is_covered = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['technique', 'organization']