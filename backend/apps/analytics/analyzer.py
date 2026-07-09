# apps/analytics/analyzer.py
from django.utils import timezone
from datetime import timedelta
from collections import Counter
import statistics

class AnalyticsEngine:
    """User and Entity Behavior Analytics Engine"""
    
    def __init__(self, organization=None):
        self.organization = organization
    
    def analyze_user(self, user):
        """Analyze user behavior and detect anomalies"""
        from apps.events.models import Event
        from .models import UserBehaviorProfile, BehaviorAnomaly
        
        events = Event.objects.filter(username=user.username)
        if self.organization:
            events = events.filter(agent__organization=self.organization)
        
        if not events.exists():
            return None
        
        profile, _ = UserBehaviorProfile.objects.get_or_create(user=user)
        
        login_events = events.filter(event_type__in=['SUCCESSFUL_LOGIN', 'FAILED_LOGIN'])
        ips = list(login_events.values_list('source_ip', flat=True).distinct())
        profile.common_ips = ips[:20]
        
        sudo_events = events.filter(event_type='SUDO_COMMAND')
        profile.sudo_frequency = sudo_events.count() / max(events.count(), 1)
        
        anomalies = []
        
        recent_ips = list(events.filter(timestamp__gte=timezone.now()-timedelta(hours=24))
                         .values_list('source_ip', flat=True).distinct())
        new_ips = set(recent_ips) - set(ips[-20:])
        for ip in new_ips:
            if ip:
                anomalies.append(BehaviorAnomaly(
                    user=user, anomaly_type='unusual_ip',
                    description=f'Login from new IP: {ip}',
                    severity='high', confidence=0.8,
                    metadata={'ip': ip}
                ))
        
        if sudo_events.count() > profile.sudo_frequency * events.count() * 2:
            anomalies.append(BehaviorAnomaly(
                user=user, anomaly_type='privilege_escalation',
                description=f'Unusual sudo activity: {sudo_events.count()} commands',
                severity='critical', confidence=0.9,
            ))
        
        profile.anomaly_score = min(len(anomalies) * 20, 100)
        profile.risk_level = 'high' if profile.anomaly_score > 60 else 'medium' if profile.anomaly_score > 30 else 'low'
        profile.total_events_analyzed = events.count()
        profile.last_analyzed = timezone.now()
        profile.save()
        
        if anomalies:
            BehaviorAnomaly.objects.bulk_create(anomalies)
        
        return profile
    
    def get_all_profiles(self):
        """Get all user behavior profiles"""
        from .models import UserBehaviorProfile
        from apps.accounts.models import User
        
        profiles = UserBehaviorProfile.objects.all()
        if self.organization:
            profiles = profiles.filter(user__organization=self.organization)
        return profiles
    
    def get_anomalies(self, hours=24):
        """Get recent anomalies"""
        from .models import BehaviorAnomaly
        
        since = timezone.now() - timedelta(hours=hours)
        anomalies = BehaviorAnomaly.objects.filter(
            detected_at__gte=since, is_resolved=False
        ).order_by('-detected_at')
        return anomalies