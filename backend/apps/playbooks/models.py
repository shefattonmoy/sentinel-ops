# apps/playbooks/models.py
import uuid
from django.db import models

class Playbook(models.Model):
    """Automated response playbooks"""
    
    TRIGGER_TYPES = [
        ('alert', 'On Alert'),
        ('threshold', 'On Threshold'),
        ('schedule', 'On Schedule'),
        ('manual', 'Manual Only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    
    # Trigger conditions
    trigger_conditions = models.JSONField(default=dict)
    
    # Actions to execute (ordered list)
    actions = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    
    # Stats
    times_executed = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-times_executed']
    
    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class PlaybookExecution(models.Model):
    """Execution history of playbooks"""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='executions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    trigger_event = models.JSONField(default=dict)
    results = models.JSONField(default=list)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-started_at']