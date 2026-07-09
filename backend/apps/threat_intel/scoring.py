# apps/threat_intel/scoring.py
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, Max, Min
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ThreatScoringEngine:
    """AI-powered threat scoring engine"""
    
    # Weights for different factors
    WEIGHTS = {
        'frequency': 0.30,
        'severity': 0.35,
        'pattern': 0.20,
        'reputation': 0.15,
    }
    
    # Severity multipliers
    SEVERITY_MULTIPLIERS = {
        'critical': 1.0,
        'high': 0.8,
        'medium': 0.5,
        'low': 0.2,
        'info': 0.05,
    }
    
    # Attack pattern multipliers
    ATTACK_PATTERNS = {
        'FAILED_LOGIN': 0.7,
        'BRUTE_FORCE_ATTEMPT': 1.0,
        'SUCCESSFUL_LOGIN': 0.4,
        'ACCESS_DENIED': 0.8,
        'SERVER_ERROR': 0.3,
        'CONTAINER_CRASH': 0.5,
        'CONTAINER_OOM': 0.6,
        'OOM_KILLER': 0.8,
        'SUDO_COMMAND': 0.9,
        'USER_CREATED': 0.9,
    }
    
    def __init__(self, organization=None):
        self.organization = organization
    
    def calculate_threat_score(self, source_ip, events=None):
        """Calculate comprehensive threat score for an IP"""
        from apps.events.models import Event
        from apps.threat_intel.models import IPReputation
        
        if events is None:
            # Get events from last 7 days
            since = timezone.now() - timedelta(days=7)
            events = Event.objects.filter(
                source_ip=source_ip,
                timestamp__gte=since
            )
            if self.organization:
                events = events.filter(agent__organization=self.organization)
        
        if not events.exists():
            return {
                'threat_score': 0,
                'frequency_score': 0,
                'severity_score': 0,
                'pattern_score': 0,
                'reputation_score': 0,
                'risk_level': 'low',
                'total_events': 0,
            }
        
        total_events = events.count()
        
        # 1. Frequency Score
        frequency_score = self._calculate_frequency_score(events, total_events)
        
        # 2. Severity Score
        severity_score = self._calculate_severity_score(events)
        
        # 3. Pattern Score
        pattern_score = self._calculate_pattern_score(events)
        
        # 4. Reputation Score
        reputation_score = self._calculate_reputation_score(source_ip)
        
        # Weighted threat score
        threat_score = (
            frequency_score * self.WEIGHTS['frequency'] +
            severity_score * self.WEIGHTS['severity'] +
            pattern_score * self.WEIGHTS['pattern'] +
            reputation_score * self.WEIGHTS['reputation']
        )
        
        # Cap at 100
        threat_score = min(threat_score, 100)
        
        # Determine risk level
        risk_level = self._determine_risk_level(threat_score)
        
        return {
            'threat_score': round(threat_score, 1),
            'frequency_score': round(frequency_score, 1),
            'severity_score': round(severity_score, 1),
            'pattern_score': round(pattern_score, 1),
            'reputation_score': round(reputation_score, 1),
            'risk_level': risk_level,
            'total_events': total_events,
            'is_known_attacker': threat_score > 70,
        }
    
    def _calculate_frequency_score(self, events, total_events):
        """Calculate frequency-based score"""
        if total_events == 0:
            return 0
        
        # Get time range
        time_range = (events.latest('timestamp').timestamp - 
                      events.earliest('timestamp').timestamp).total_seconds() / 3600  # hours
        
        if time_range < 0.01:
            time_range = 0.01
        
        # Events per hour
        events_per_hour = total_events / time_range
        
        # Score based on events per hour
        if events_per_hour > 100:
            return 100
        elif events_per_hour > 50:
            return 80
        elif events_per_hour > 20:
            return 60
        elif events_per_hour > 10:
            return 40
        elif events_per_hour > 5:
            return 20
        else:
            return max(events_per_hour * 2, 5)
    
    def _calculate_severity_score(self, events):
        """Calculate severity-based score"""
        severity_counts = events.values('severity').annotate(count=Count('id'))
        total = events.count()
        
        if total == 0:
            return 0
        
        weighted_sum = 0
        for item in severity_counts:
            multiplier = self.SEVERITY_MULTIPLIERS.get(item['severity'], 0.1)
            weighted_sum += item['count'] * multiplier * 100
        
        return weighted_sum / total
    
    def _calculate_pattern_score(self, events):
        """Calculate attack pattern score"""
        event_types = events.values('event_type').annotate(count=Count('id'))
        total = events.count()
        
        if total == 0:
            return 0
        
        pattern_score = 0
        unique_patterns = 0
        
        for item in event_types:
            pattern_weight = self.ATTACK_PATTERNS.get(item['event_type'], 0.2)
            pattern_score += pattern_weight * item['count']
            if pattern_weight > 0.5:  # Count severe patterns
                unique_patterns += 1
        
        # Normalize
        pattern_score = (pattern_score / total) * 100
        
        # Bonus for multiple attack types
        if unique_patterns >= 3:
            pattern_score += 20
        elif unique_patterns >= 2:
            pattern_score += 10
        
        return min(pattern_score, 100)
    
    def _calculate_reputation_score(self, source_ip):
        """Calculate reputation-based score"""
        from apps.threat_intel.models import IPReputation
        
        try:
            reputation = IPReputation.objects.get(ip_address=source_ip)
            
            # Higher abuse confidence = higher score
            score = reputation.abuse_confidence
            
            # Additional penalties
            if reputation.is_tor:
                score += 20
            if reputation.is_proxy:
                score += 15
            if reputation.is_vpn:
                score += 10
            
            return min(score, 100)
        except IPReputation.DoesNotExist:
            return 25  # Unknown, neutral score
    
    def _determine_risk_level(self, score):
        """Determine risk level from score"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 35:
            return 'medium'
        return 'low'
    
    def get_top_threats(self, limit=20):
        """Get top threats across the organization"""
        from apps.events.models import Event
        from apps.threat_intel.models import ThreatScore
        
        since = timezone.now() - timedelta(days=7)
        
        # Get distinct IPs with events
        ips = Event.objects.filter(
            timestamp__gte=since,
            source_ip__isnull=False
        )
        if self.organization:
            ips = ips.filter(agent__organization=self.organization)
        
        ips = ips.values('source_ip').annotate(
            count=Count('id')
        ).order_by('-count')[:100]
        
        threats = []
        for item in ips:
            score_data = self.calculate_threat_score(item['source_ip'])
            
            # Update or create ThreatScore
            threat_score, created = ThreatScore.objects.update_or_create(
                source_ip=item['source_ip'],
                organization=self.organization,
                defaults={
                    'threat_score': score_data['threat_score'],
                    'frequency_score': score_data['frequency_score'],
                    'severity_score': score_data['severity_score'],
                    'pattern_score': score_data['pattern_score'],
                    'reputation_score': score_data['reputation_score'],
                    'total_events': score_data['total_events'],
                    'risk_level': score_data['risk_level'],
                    'is_known_attacker': score_data['is_known_attacker'],
                    'last_seen': timezone.now(),
                }
            )
            
            if score_data['threat_score'] > 20:  # Only include notable threats
                threats.append({
                    'source_ip': item['source_ip'],
                    **score_data,
                })
        
        return sorted(threats, key=lambda x: x['threat_score'], reverse=True)[:limit]