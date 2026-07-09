# apps/rules/models.py
import uuid
from django.db import models
from django.core.exceptions import ValidationError
import json

class DetectionRule(models.Model):
    """Detection rules that define alert conditions"""
    
    RULE_TYPE_CHOICES = [
        ('threshold', 'Threshold'),
        ('anomaly', 'Anomaly'),
        ('correlation', 'Correlation'),
        ('pattern', 'Pattern Match'),
        ('frequency', 'Frequency'),
        ('sequence', 'Sequence'),
        ('blacklist', 'Blacklist'),
        ('whitelist', 'Whitelist'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('testing', 'Testing'),
        ('disabled', 'Disabled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES, default='threshold')
    
    # Organization
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='detection_rules',
        null=True,
        blank=True
    )
    
    # Rule conditions (JSON schema)
    conditions = models.JSONField(
        help_text="""
        Example threshold rule:
        {
            "event_type": "FAILED_LOGIN",
            "timeframe_minutes": 5,
            "threshold": 5,
            "group_by": ["source_ip"],
            "filters": {
                "severity": ["medium", "high", "critical"],
                "source": ["ssh"]
            }
        }
        
        Example correlation rule:
        {
            "events": [
                {"event_type": "FAILED_LOGIN", "count": 5, "timeframe_minutes": 5},
                {"event_type": "SUCCESSFUL_LOGIN", "count": 1, "timeframe_minutes": 5}
            ],
            "group_by": ["source_ip"],
            "require_all": true
        }
        """
    )
    
    # Actions to take when rule triggers
    actions = models.JSONField(
        default=dict,
        help_text="""
        {
            "create_alert": true,
            "alert_title": "Brute Force Attack Detected",
            "alert_severity": "high",
            "alert_category": "security",
            "auto_escalate": true,
            "notify_channels": ["email", "slack"],
            "create_incident": false,
            "block_ip": false
        }
        """
    )
    
    # Rule metadata
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    category = models.CharField(max_length=100, default='security')
    
    # Status and scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.IntegerField(default=100)  # Lower = higher priority
    cooldown_minutes = models.IntegerField(default=5)  # Minimum time between triggers
    
    # Statistics
    times_triggered = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    alerts_generated = models.IntegerField(default=0)
    
    # Scope
    apply_to_all_agents = models.BooleanField(default=True)
    agents = models.ManyToManyField('agents.Agent', blank=True, related_name='rules')
    agent_groups = models.ManyToManyField('agents.AgentGroup', blank=True, related_name='rules')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'rule_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['organization']),
        ]
        verbose_name = 'Detection Rule'
        verbose_name_plural = 'Detection Rules'
    
    def __str__(self):
        return f"{self.name} ({self.rule_type}) - {self.status}"
    
    def clean(self):
        """Validate rule conditions"""
        if self.rule_type == 'threshold':
            required_fields = ['event_type', 'timeframe_minutes', 'threshold']
            for field in required_fields:
                if field not in self.conditions:
                    raise ValidationError(f"Threshold rule requires '{field}' in conditions")
        
        elif self.rule_type == 'correlation':
            if 'events' not in self.conditions:
                raise ValidationError("Correlation rule requires 'events' in conditions")
            if len(self.conditions['events']) < 2:
                raise ValidationError("Correlation rule requires at least 2 events")
    
    def get_agent_filter(self):
        """Get the agent filter based on rule scope"""
        from django.db.models import Q
        
        if self.apply_to_all_agents:
            return Q()
        
        agent_filter = Q()
        if self.agents.exists():
            agent_filter |= Q(agent__in=self.agents.all())
        
        for group in self.agent_groups.all():
            agent_filter |= Q(agent__in=group.agents.all())
        
        return agent_filter if agent_filter else Q()


class RuleExecution(models.Model):
    """Tracks rule execution history"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        DetectionRule,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution details
    executed_at = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(null=True, blank=True)  # in milliseconds
    
    # Results
    is_triggered = models.BooleanField(default=False)
    matched_count = models.IntegerField(default=0)
    events_analyzed = models.IntegerField(default=0)
    
    # Context
    context = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['rule', 'executed_at']),
            models.Index(fields=['is_triggered']),
        ]
        verbose_name = 'Rule Execution'
        verbose_name_plural = 'Rule Executions'
    
    def __str__(self):
        return f"{self.rule.name} - {'Triggered' if self.is_triggered else 'Not Triggered'} at {self.executed_at}"


class RuleTemplate(models.Model):
    """Pre-built rule templates for common scenarios"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    rule_type = models.CharField(max_length=50, choices=DetectionRule.RULE_TYPE_CHOICES)
    conditions = models.JSONField()
    actions = models.JSONField(default=dict)
    severity = models.CharField(max_length=20, choices=DetectionRule.SEVERITY_CHOICES)
    category = models.CharField(max_length=100)
    tags = models.JSONField(default=list)
    use_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-use_count']
        verbose_name = 'Rule Template'
        verbose_name_plural = 'Rule Templates'
    
    def __str__(self):
        return self.name