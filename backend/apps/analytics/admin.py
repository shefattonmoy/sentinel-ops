from django.contrib import admin
from .models import UserBehaviorProfile, BehaviorAnomaly

@admin.register(UserBehaviorProfile)
class UserBehaviorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'anomaly_score', 'risk_level', 'total_events_analyzed', 'last_analyzed']
    list_filter = ['risk_level']
    search_fields = ['user__username']

@admin.register(BehaviorAnomaly)
class BehaviorAnomalyAdmin(admin.ModelAdmin):
    list_display = ['user', 'anomaly_type', 'severity', 'confidence', 'is_resolved', 'detected_at']
    list_filter = ['anomaly_type', 'severity', 'is_resolved']
    search_fields = ['user__username', 'description']