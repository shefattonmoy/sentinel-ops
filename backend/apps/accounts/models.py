# apps/accounts/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True
    )
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Admin'), ('analyst', 'Security Analyst'), ('viewer', 'Viewer'),
    ], default='viewer')
    is_agent = models.BooleanField(default=False)
    
    # Profile fields
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # 2FA fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=100, blank=True, null=True)
    two_factor_backup_codes = models.JSONField(default=list, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    class Meta:
        ordering = ['-date_joined']