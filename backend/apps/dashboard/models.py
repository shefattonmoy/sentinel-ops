# apps/dashboard/models.py
import uuid
from django.db import models

class DashboardWidget(models.Model):
    """Customizable dashboard widgets"""
    
    WIDGET_TYPES = [
        ('stats', 'Statistics'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('list', 'List'),
        ('timeline', 'Timeline'),
        ('map', 'Map'),
    ]
    
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('gauge', 'Gauge'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES, null=True, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict)
    data_source = models.CharField(max_length=255)
    refresh_interval = models.IntegerField(default=30)  # seconds
    
    # Position
    row = models.IntegerField(default=0)
    col = models.IntegerField(default=0)
    width = models.IntegerField(default=1)
    height = models.IntegerField(default=1)
    
    # Visibility
    is_active = models.BooleanField(default=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    roles = models.JSONField(default=list)  # Roles that can see this widget
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['row', 'col']
    
    def __str__(self):
        return self.name


class DashboardLayout(models.Model):
    """Saved dashboard layouts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    widgets = models.ManyToManyField(DashboardWidget)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"