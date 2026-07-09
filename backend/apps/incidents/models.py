# apps/incidents/models.py
import uuid
from django.db import models
from django.utils import timezone

class Incident(models.Model):
    """Security incidents that group related alerts and events"""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('triaging', 'Triaging'),
        ('investigating', 'Investigating'),
        ('containment', 'Containment'),
        ('eradication', 'Eradication'),
        ('recovery', 'Recovery'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('false_positive', 'False Positive'),
    ]
    
    INCIDENT_TYPE_CHOICES = [
        ('brute_force', 'Brute Force Attack'),
        ('malware', 'Malware Infection'),
        ('data_breach', 'Data Breach'),
        ('ddos', 'DDoS Attack'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('privilege_escalation', 'Privilege Escalation'),
        ('system_compromise', 'System Compromise'),
        ('policy_violation', 'Policy Violation'),
        ('insider_threat', 'Insider Threat'),
        ('phishing', 'Phishing Attack'),
        ('ransomware', 'Ransomware'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('p1', 'P1 - Critical'),
        ('p2', 'P2 - High'),
        ('p3', 'P3 - Medium'),
        ('p4', 'P4 - Low'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPE_CHOICES, default='other')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    priority = models.CharField(max_length=3, choices=PRIORITY_CHOICES, default='p3')
    
    # Organization
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='incidents',
        null=True,
        blank=True
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    assigned_team = models.CharField(max_length=255, null=True, blank=True)
    
    # Related objects
    alerts = models.ManyToManyField('alerts.Alert', related_name='incidents', blank=True)
    events = models.ManyToManyField('events.Event', related_name='incidents', blank=True)
    
    # Correlation information
    correlation_rule = models.ForeignKey(
        'rules.DetectionRule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    correlation_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    correlation_confidence = models.FloatField(default=0.0)
    
    # Impact assessment
    affected_systems = models.JSONField(default=list, blank=True)
    affected_users = models.JSONField(default=list, blank=True)
    impact_scope = models.CharField(
        max_length=50,
        choices=[
            ('single_host', 'Single Host'),
            ('multiple_hosts', 'Multiple Hosts'),
            ('network_wide', 'Network Wide'),
            ('organization_wide', 'Organization Wide'),
        ],
        default='single_host'
    )
    
    # Source information
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    source_hostname = models.CharField(max_length=255, null=True, blank=True)
    attack_vector = models.CharField(max_length=255, null=True, blank=True)
    
    # Evidence and artifacts
    evidence = models.JSONField(default=dict, blank=True)
    artifacts = models.JSONField(default=list, blank=True)
    indicators_of_compromise = models.JSONField(default=list, blank=True)
    
    # Timeline
    detected_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    contained_at = models.DateTimeField(null=True, blank=True)
    eradicated_at = models.DateTimeField(null=True, blank=True)
    recovered_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolution_type = models.CharField(
        max_length=50,
        choices=[
            ('contained', 'Contained'),
            ('eradicated', 'Eradicated'),
            ('mitigated', 'Mitigated'),
            ('false_positive', 'False Positive'),
            ('not_applicable', 'Not Applicable'),
        ],
        null=True,
        blank=True
    )
    root_cause = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    
    # Metrics
    time_to_detect = models.IntegerField(null=True, blank=True)  # minutes
    time_to_contain = models.IntegerField(null=True, blank=True)  # minutes
    time_to_resolve = models.IntegerField(null=True, blank=True)  # minutes
    
    # SLA
    sla_deadline = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_incidents'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['incident_type']),
            models.Index(fields=['correlation_id']),
        ]
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
    
    def __str__(self):
        return f"{self.title} - {self.severity} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate metrics on save"""
        if self.started_at and self.detected_at:
            self.time_to_detect = int((self.detected_at - self.started_at).total_seconds() / 60)
        
        if self.contained_at and self.detected_at:
            self.time_to_contain = int((self.contained_at - self.detected_at).total_seconds() / 60)
        
        if self.resolved_at and self.detected_at:
            self.time_to_resolve = int((self.resolved_at - self.detected_at).total_seconds() / 60)
        
        super().save(*args, **kwargs)
    
    def set_sla_deadline(self):
        """Set SLA deadline based on severity and priority"""
        sla_times = {
            'critical': {'p1': 30, 'p2': 60, 'p3': 120, 'p4': 240},
            'high': {'p1': 60, 'p2': 120, 'p3': 240, 'p4': 480},
            'medium': {'p1': 120, 'p2': 240, 'p3': 480, 'p4': 960},
            'low': {'p1': 240, 'p2': 480, 'p3': 960, 'p4': 1440},
        }
        
        minutes = sla_times.get(self.severity, {}).get(self.priority, 480)
        self.sla_deadline = timezone.now() + models.timedelta(minutes=minutes)
        self.save()
    
    def add_evidence(self, evidence_type, data):
        """Add evidence to the incident"""
        if not self.evidence:
            self.evidence = {}
        
        if evidence_type not in self.evidence:
            self.evidence[evidence_type] = []
        
        self.evidence[evidence_type].append({
            'timestamp': timezone.now().isoformat(),
            'data': data
        })
        self.save()


class IncidentTimeline(models.Model):
    """Timeline of events in an incident"""
    
    ENTRY_TYPE_CHOICES = [
        ('alert', 'Alert Generated'),
        ('event', 'Event Occurred'),
        ('action', 'Action Taken'),
        ('comment', 'Comment Added'),
        ('status_change', 'Status Changed'),
        ('evidence', 'Evidence Added'),
        ('assignment', 'Assignment Changed'),
        ('escalation', 'Escalation'),
        ('notification', 'Notification Sent'),
        ('system', 'System Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='timeline'
    )
    
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['incident', 'timestamp']),
            models.Index(fields=['entry_type']),
        ]
        verbose_name = 'Incident Timeline'
        verbose_name_plural = 'Incident Timelines'
    
    def __str__(self):
        return f"{self.entry_type} - {self.timestamp}"


class IncidentNote(models.Model):
    """Notes and comments on incidents"""
    
    NOTE_TYPE_CHOICES = [
        ('investigation', 'Investigation Note'),
        ('analysis', 'Analysis'),
        ('action', 'Action Taken'),
        ('finding', 'Finding'),
        ('recommendation', 'Recommendation'),
        ('general', 'General Note'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )
    
    note_type = models.CharField(max_length=50, choices=NOTE_TYPE_CHOICES, default='general')
    content = models.TextField()
    
    is_private = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Incident Note'
        verbose_name_plural = 'Incident Notes'
    
    def __str__(self):
        return f"Note by {self.user.username} on {self.incident.title}"