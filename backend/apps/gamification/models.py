# apps/gamification/models.py
import uuid
from django.db import models

class AnalystProfile(models.Model):
    """Gamification profile for SOC analysts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    
    # Points
    total_points = models.IntegerField(default=0)
    weekly_points = models.IntegerField(default=0)
    monthly_points = models.IntegerField(default=0)
    
    # Stats
    alerts_resolved = models.IntegerField(default=0)
    incidents_closed = models.IntegerField(default=0)
    threats_detected = models.IntegerField(default=0)
    playbooks_executed = models.IntegerField(default=0)
    response_time_avg = models.FloatField(default=0)  # minutes
    
    # Level
    level = models.IntegerField(default=1)
    title = models.CharField(max_length=100, default='Junior Analyst')
    
    # Achievements
    achievements = models.JSONField(default=list)
    
    updated_at = models.DateTimeField(auto_now=True)

class Badge(models.Model):
    """Achievement badges"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏅')
    criteria = models.JSONField(default=dict)
    points = models.IntegerField(default=50)
    
    def __str__(self):
        return f"{self.icon} {self.name}"

class Leaderboard(models.Model):
    """Weekly/Monthly leaderboard snapshots"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.CharField(max_length=20)  # weekly, monthly
    period_start = models.DateField()
    period_end = models.DateField()
    rankings = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)