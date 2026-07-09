# apps/risk/scoring.py
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import AssetRiskScore

class RiskScoringEngine:
    """Calculate risk scores for assets"""
    
    def calculate_asset_risk(self, hostname, ip_address=None):
        """Calculate comprehensive risk score for an asset"""
        from apps.events.models import Event
        from apps.alerts.models import Alert
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Get events for this asset
        events = Event.objects.filter(
            Q(source_hostname=hostname) | Q(source_ip=ip_address) |
            Q(agent__hostname=hostname)
        )
        
        recent_events = events.filter(timestamp__gte=last_24h)
        week_events = events.filter(timestamp__gte=last_7d)
        
        # 1. Threat Risk (based on attacks targeting this asset)
        attack_events = recent_events.filter(
            event_type__in=['FAILED_LOGIN', 'BRUTE_FORCE_ATTEMPT', 'ACCESS_DENIED']
        ).count()
        threat_risk = min(attack_events * 2, 100)
        
        # 2. Vulnerability Risk (based on critical events on this asset)
        critical_count = recent_events.filter(
            severity__in=['critical', 'high']
        ).count()
        vulnerability_risk = min(critical_count * 10, 100)
        
        # 3. Exposure Risk (based on variety of event types)
        unique_types = recent_events.values('event_type').distinct().count()
        exposure_risk = min(unique_types * 10, 100)
        
        # 4. Impact Risk (based on alerts generated)
        alerts = Alert.objects.filter(
            Q(metadata__contains={'hostname': hostname}) |
            Q(metadata__contains={'source_ip': ip_address}),
            created_at__gte=last_7d
        ).count()
        impact_risk = min(alerts * 15, 100)
        
        # Overall risk (weighted)
        overall_risk = (
            threat_risk * 0.35 +
            vulnerability_risk * 0.30 +
            exposure_risk * 0.20 +
            impact_risk * 0.15
        )
        
        return {
            'overall_risk': round(overall_risk, 1),
            'threat_risk': round(threat_risk, 1),
            'vulnerability_risk': round(vulnerability_risk, 1),
            'exposure_risk': round(exposure_risk, 1),
            'impact_risk': round(impact_risk, 1),
            'recent_attacks': attack_events,
            'critical_events': critical_count,
            'open_alerts': alerts,
        }
    
    def get_all_asset_risks(self, organization=None):
        """Get risk scores for all assets"""
        from apps.agents.models import Agent
        
        agents = Agent.objects.filter(is_active=True)
        if organization:
            agents = agents.filter(organization=organization)
        
        risks = []
        for agent in agents:
            score = self.calculate_asset_risk(agent.hostname, agent.ip_address)
            
            # Update or create
            AssetRiskScore.objects.update_or_create(
                asset_name=agent.name,
                organization=organization,
                defaults={
                    'asset_type': agent.agent_type,
                    'hostname': agent.hostname,
                    'ip_address': agent.ip_address,
                    **score,
                }
            )
            
            risks.append({
                'asset_name': agent.name,
                'hostname': agent.hostname,
                'asset_type': agent.agent_type,
                **score,
            })
        
        return sorted(risks, key=lambda x: x['overall_risk'], reverse=True)