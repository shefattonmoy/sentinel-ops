# apps/reports/models.py
import uuid
from django.db import models

class Report(models.Model):
    """Generated reports"""
    
    REPORT_TYPES = [
        ('daily_soc', 'Daily SOC Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('incident_summary', 'Incident Summary'),
        ('executive', 'Executive Summary'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='json')  # Changed from 'pdf' to 'json'
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Report data
    parameters = models.JSONField(default=dict)
    data = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('generating', 'Generating'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.report_type}"