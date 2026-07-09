# apps/reports/generator.py
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from datetime import datetime, timedelta
from collections import defaultdict

from apps.events.models import Event
from apps.alerts.models import Alert
from apps.incidents.models import Incident
from apps.agents.models import Agent, AgentHeartbeat
from apps.logs.models import RawLog

class ReportGenerator:
    """Generate various security reports"""
    
    def __init__(self, organization=None):
        self.organization = organization
        self.org_filter = {'organization': organization} if organization else {}
        self.agent_org_filter = {'agent__organization': organization} if organization else {}
    
    def generate_daily_soc_report(self, date=None):
        """Generate daily SOC report"""
        if not date:
            date = timezone.now().date()
        
        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)
        
        # Events
        events = Event.objects.filter(
            timestamp__gte=start_of_day,
            timestamp__lt=end_of_day,
            **self.agent_org_filter
        )
        
        # Alerts
        alerts = Alert.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            **self.org_filter
        )
        
        # Incidents
        incidents = Incident.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            **self.org_filter
        )
        
        # Agents
        agents = Agent.objects.filter(
            is_active=True,
            **({'organization': self.organization} if self.organization else {})
        )
        
        report = {
            'report_type': 'daily_soc',
            'date': date.isoformat(),
            'generated_at': timezone.now().isoformat(),
            'summary': {
                'total_events': events.count(),
                'total_alerts': alerts.count(),
                'total_incidents': incidents.count(),
                'agents_online': agents.filter(status='online').count(),
                'agents_total': agents.count(),
            },
            'events': {
                'by_severity': list(events.values('severity').annotate(count=Count('id'))),
                'by_type': list(events.values('event_type').annotate(count=Count('id')).order_by('-count')[:10]),
                'top_source_ips': list(events.values('source_ip').annotate(count=Count('id')).order_by('-count')[:10]),
                'failed_logins': events.filter(event_type='FAILED_LOGIN').count(),
            },
            'alerts': {
                'by_severity': list(alerts.values('severity').annotate(count=Count('id'))),
                'by_status': list(alerts.values('status').annotate(count=Count('id'))),
                'critical_alerts': alerts.filter(severity='critical').count(),
                'avg_response_time': self._calculate_avg_response_time(alerts),
            },
            'incidents': {
                'created': incidents.count(),
                'resolved': incidents.filter(status__in=['resolved', 'closed']).count(),
                'still_open': incidents.filter(status__in=['new', 'triaging', 'investigating']).count(),
            },
            'hourly_breakdown': self._get_hourly_breakdown(events, start_of_day),
        }
        
        return report
    
    def generate_weekly_report(self, end_date=None):
        """Generate weekly report"""
        if not end_date:
            end_date = timezone.now().date()
        
        start_date = end_date - timedelta(days=7)
        
        return self._generate_period_report(start_date, end_date, 'weekly')
    
    def generate_monthly_report(self, end_date=None):
        """Generate monthly report"""
        if not end_date:
            end_date = timezone.now().date()
        
        start_date = end_date - timedelta(days=30)
        
        return self._generate_period_report(start_date, end_date, 'monthly')
    
    def generate_incident_summary(self, incident_id):
        """Generate incident summary report"""
        try:
            incident = Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            return None
        
        return {
            'report_type': 'incident_summary',
            'incident_id': str(incident.id),
            'title': incident.title,
            'severity': incident.severity,
            'status': incident.status,
            'priority': incident.priority,
            'incident_type': incident.incident_type,
            'detected_at': incident.detected_at.isoformat() if incident.detected_at else None,
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'time_to_detect': incident.time_to_detect,
            'time_to_resolve': incident.time_to_resolve,
            'source_ip': incident.source_ip,
            'alerts_count': incident.alerts.count(),
            'events_count': incident.events.count(),
            'timeline': list(incident.timeline.values('entry_type', 'description', 'timestamp')),
            'resolution': incident.resolution,
            'root_cause': incident.root_cause,
            'lessons_learned': incident.lessons_learned,
        }
    
    def generate_executive_summary(self):
        """Generate executive summary report"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Key metrics
        events = Event.objects.filter(
            timestamp__gte=thirty_days_ago,
            **self.agent_org_filter
        )
        
        alerts = Alert.objects.filter(
            created_at__gte=thirty_days_ago,
            **self.org_filter
        )
        
        incidents = Incident.objects.filter(
            created_at__gte=thirty_days_ago,
            **self.org_filter
        )
        
        return {
            'report_type': 'executive_summary',
            'period': {
                'start': thirty_days_ago.date().isoformat(),
                'end': now.date().isoformat(),
            },
            'key_metrics': {
                'total_events': events.count(),
                'total_alerts': alerts.count(),
                'total_incidents': incidents.count(),
                'critical_incidents': incidents.filter(severity='critical').count(),
                'avg_incidents_per_day': incidents.count() / 30,
                'avg_time_to_resolve': incidents.filter(
                    time_to_resolve__isnull=False
                ).aggregate(avg=Avg('time_to_resolve'))['avg'],
            },
            'trends': {
                'events_trend': self._calculate_trend(events, 30),
                'alerts_trend': self._calculate_trend(alerts, 30),
            },
            'top_risks': self._identify_top_risks(events, alerts, incidents),
            'recommendations': self._generate_recommendations(alerts, incidents),
        }
    
    def _generate_period_report(self, start_date, end_date, report_type):
        """Generate period-based report"""
        start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
        
        events = Event.objects.filter(
            timestamp__gte=start_dt,
            timestamp__lt=end_dt,
            **self.agent_org_filter
        )
        
        alerts = Alert.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            **self.org_filter
        )
        
        days = (end_date - start_date).days
        
        return {
            'report_type': report_type,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days,
            },
            'summary': {
                'total_events': events.count(),
                'avg_events_per_day': events.count() / days,
                'total_alerts': alerts.count(),
                'avg_alerts_per_day': alerts.count() / days,
            },
            'top_events': list(events.values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
            'top_alerts': list(alerts.values('category').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
        }
    
    def _calculate_avg_response_time(self, alerts):
        """Calculate average response time"""
        result = alerts.filter(
            acknowledged_at__isnull=False
        ).annotate(
            response_time=F('acknowledged_at') - F('created_at')
        ).aggregate(avg=Avg('response_time'))
        
        if result['avg']:
            return round(result['avg'].total_seconds() / 60, 1)
        return 0
    
    def _get_hourly_breakdown(self, events, start_of_day):
        """Get hourly event breakdown"""
        breakdown = []
        for hour in range(24):
            hour_start = start_of_day + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            count = events.filter(
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            ).count()
            breakdown.append({
                'hour': f'{hour:02d}:00',
                'count': count
            })
        return breakdown
    
    def _calculate_trend(self, queryset, days):
        """Calculate trend over days"""
        trend = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            count = queryset.filter(
                timestamp__gte=day_start if hasattr(queryset.model, 'timestamp') else Q(created_at__gte=day_start),
                timestamp__lt=day_end if hasattr(queryset.model, 'timestamp') else Q(created_at__lt=day_end)
            ).count()
            trend.append({'date': date.isoformat(), 'count': count})
        return trend
    
    def _identify_top_risks(self, events, alerts, incidents):
        """Identify top security risks"""
        risks = []
        
        # Check for brute force
        failed_logins = events.filter(event_type='FAILED_LOGIN').count()
        if failed_logins > 100:
            risks.append({
                'risk': 'Brute Force Activity',
                'severity': 'high',
                'description': f'{failed_logins} failed login attempts detected'
            })
        
        # Check for critical incidents
        critical_incidents = incidents.filter(severity='critical').count()
        if critical_incidents > 0:
            risks.append({
                'risk': 'Critical Security Incidents',
                'severity': 'critical',
                'description': f'{critical_incidents} critical incidents occurred'
            })
        
        return risks
    
    def _generate_recommendations(self, alerts, incidents):
        """Generate security recommendations"""
        recommendations = []
        
        # Check incident patterns
        if incidents.filter(incident_type='brute_force').count() > 0:
            recommendations.append('Enable additional authentication controls (MFA, rate limiting)')
        
        if alerts.filter(severity='critical').count() > 10:
            recommendations.append('Review critical alert thresholds and response procedures')
        
        return recommendations