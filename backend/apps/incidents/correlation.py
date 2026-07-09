# apps/incidents/correlation.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Count, Q, Max, Min
from collections import defaultdict
import uuid

from apps.events.models import Event
from apps.alerts.models import Alert
from .models import Incident, IncidentTimeline

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """
    Correlates related events and alerts to create incidents.
    Reduces alert fatigue by grouping related security events.
    """
    
    # Correlation rules define how events/patterns are linked
    CORRELATION_PATTERNS = [
        {
            'name': 'SSH Attack Chain',
            'description': 'Failed SSH → Successful Login → Privilege Escalation',
            'patterns': [
                {'event_type': 'FAILED_LOGIN', 'source': 'ssh', 'timeframe': 10},
                {'event_type': 'SUCCESSFUL_LOGIN', 'source': 'ssh', 'timeframe': 10},
                {'event_type': 'SUDO_COMMAND', 'source': 'ssh', 'timeframe': 5},
            ],
            'min_events': 3,
            'incident_type': 'brute_force',
            'severity': 'high',
            'title_template': 'SSH Attack Chain Detected from {source_ip}',
            'priority': 'p2',
        },
        {
            'name': 'Privilege Escalation',
            'description': 'New user created after suspicious activity',
            'patterns': [
                {'event_type': 'SUCCESSFUL_LOGIN', 'source': 'ssh', 'timeframe': 10},
                {'event_type': 'SUDO_COMMAND', 'timeframe': 5},
                {'event_type': 'USER_CREATED', 'timeframe': 5},
            ],
            'min_events': 3,
            'incident_type': 'privilege_escalation',
            'severity': 'critical',
            'title_template': 'Privilege Escalation Detected - User {username}',
            'priority': 'p1',
        },
        {
            'name': 'Container Failure Cascade',
            'description': 'Multiple container failures in sequence',
            'patterns': [
                {'event_type': 'CONTAINER_CRASH', 'timeframe': 5},
                {'event_type': 'CONTAINER_RESTART', 'timeframe': 5},
                {'event_type': 'CONTAINER_OOM', 'timeframe': 5},
            ],
            'min_events': 2,
            'incident_type': 'other',
            'severity': 'high',
            'title_template': 'Container Failure Cascade - {service}',
            'priority': 'p2',
        },
        {
            'name': 'Web Application Attack',
            'description': 'Multiple attack patterns against web application',
            'patterns': [
                {'event_type': 'ACCESS_DENIED', 'timeframe': 5},
                {'event_type': 'SERVER_ERROR', 'timeframe': 5},
            ],
            'min_events': 5,
            'incident_type': 'unauthorized_access',
            'severity': 'high',
            'title_template': 'Web Application Attack from {source_ip}',
            'priority': 'p2',
        },
        {
            'name': 'Data Exfiltration Pattern',
            'description': 'Large data transfer after unauthorized access',
            'patterns': [
                {'event_type': 'FAILED_LOGIN', 'timeframe': 30},
                {'event_type': 'SUCCESSFUL_LOGIN', 'timeframe': 30},
                {'event_type': 'SUDO_COMMAND', 'timeframe': 15},
            ],
            'min_events': 3,
            'incident_type': 'data_breach',
            'severity': 'critical',
            'title_template': 'Potential Data Exfiltration - {source_ip}',
            'priority': 'p1',
        },
    ]
    
    def correlate_alerts(self, organization=None) -> List[Incident]:
        """
        Correlate open alerts and create incidents.
        Groups related alerts by source IP, username, and timeframe.
        """
        alerts_query = Alert.objects.filter(
            status__in=['open', 'acknowledged'],
        ).exclude(
            incidents__isnull=False 
        )
        
        if organization:
            alerts_query = alerts_query.filter(organization=organization)
        
        open_alerts = list(alerts_query.select_related('assigned_to'))
        
        if len(open_alerts) < 2:
            return []
        
        incidents_created = []
        
        # Group alerts by source IP, username, and timeframe
        ip_groups = defaultdict(list)
        username_groups = defaultdict(list)
        timeframe_groups = defaultdict(list)
        
        for alert in open_alerts:
            metadata = alert.metadata or {}
            context = metadata.get('context', {})
            
            # Extract IP and username from alert metadata
            for group in context.get('triggered_groups', []):
                group_data = group.get('group', {})
                if 'source_ip' in group_data:
                    ip_groups[group_data['source_ip']].append(alert)
                if 'username' in group_data:
                    username_groups[group_data['username']].append(alert)
            
            # Group by timeframe (alerts within same hour)
            hour_key = alert.created_at.strftime('%Y-%m-%d-%H')
            timeframe_groups[hour_key].append(alert)
        
        # Check each correlation pattern against alert groups
        for pattern in self.CORRELATION_PATTERNS:
            correlated = self._match_pattern(pattern, open_alerts, ip_groups, username_groups)
            
            if correlated:
                incident = self._create_incident_from_correlation(
                    pattern,
                    correlated['alerts'],
                    correlated['context']
                )
                incidents_created.append(incident)
        
        return incidents_created
    
    def correlate_events(self, events: List[Event], timeframe_minutes: int = 15) -> List[Dict]:
        """
        Correlate events to find attack patterns.
        """
        correlations = []
        
        # Group events by source IP
        ip_groups = defaultdict(list)
        for event in events:
            if event.source_ip:
                ip_groups[event.source_ip].append(event)
        
        # Check each correlation pattern
        for pattern in self.CORRELATION_PATTERNS:
            for ip, ip_events in ip_groups.items():
                if len(ip_events) < pattern['min_events']:
                    continue
                
                # Check if events match the pattern sequence
                match = self._check_sequence_match(pattern, ip_events)
                
                if match:
                    correlations.append({
                        'pattern': pattern['name'],
                        'source_ip': ip,
                        'events': match['matched_events'],
                        'confidence': match['confidence'],
                        'incident_type': pattern['incident_type'],
                        'severity': pattern['severity'],
                    })
        
        return correlations
    
    def _match_pattern(self, pattern: Dict, alerts: List[Alert], ip_groups: Dict, username_groups: Dict) -> Optional[Dict]:
        """Match alerts against a correlation pattern"""
        correlated_alerts = set()
        
        # Check IP-based correlations
        for ip, ip_alerts in ip_groups.items():
            if len(ip_alerts) >= pattern['min_events']:
                # Check if alerts match the pattern's event types
                matched = self._check_alert_pattern(pattern, ip_alerts)
                if matched:
                    correlated_alerts.update(ip_alerts)
        
        # Check username-based correlations
        for username, user_alerts in username_groups.items():
            if len(user_alerts) >= pattern['min_events']:
                correlated_alerts.update(user_alerts)
        
        if len(correlated_alerts) >= pattern['min_events']:
            return {
                'alerts': list(correlated_alerts),
                'context': {
                    'pattern_name': pattern['name'],
                    'matched_count': len(correlated_alerts),
                }
            }
        
        return None
    
    def _check_sequence_match(self, pattern: Dict, events: List[Event]) -> Optional[Dict]:
        """Check if events match a sequence pattern"""
        matched_events = []
        total_confidence = 0.0
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Check each pattern step
        for pattern_step in pattern['patterns']:
            timeframe = pattern_step.get('timeframe', 15)
            event_type = pattern_step.get('event_type')
            
            # Find matching events within timeframe
            step_matches = []
            for event in sorted_events:
                if event.event_type == event_type:
                    # Check if this event is within timeframe of previous match
                    if step_matches:
                        last_match = step_matches[-1]
                        time_diff = (event.timestamp - last_match.timestamp).total_seconds() / 60
                        if time_diff <= timeframe:
                            step_matches.append(event)
                    else:
                        step_matches.append(event)
            
            if step_matches:
                matched_events.extend(step_matches)
                total_confidence += 0.5  # Confidence for each matched step
        
        if len(matched_events) >= pattern['min_events']:
            return {
                'matched_events': matched_events,
                'confidence': min(total_confidence, 1.0),
            }
        
        return None
    
    def _check_alert_pattern(self, pattern: Dict, alerts: List[Alert]) -> bool:
        """Check if alerts match a pattern"""
        # This is a simplified check - in production, you'd match alert metadata
        # against the pattern's expected event types
        return len(alerts) >= pattern['min_events']
    
    def _create_incident_from_correlation(self, pattern: Dict, alerts: List[Alert], context: Dict) -> Incident:
        """Create an incident from correlated alerts"""
        # Determine source IP from alerts
        source_ip = None
        source_hostname = None
        username = None
        
        for alert in alerts:
            metadata = alert.metadata or {}
            ctx = metadata.get('context', {})
            
            for group in ctx.get('triggered_groups', []):
                group_data = group.get('group', {})
                if 'source_ip' in group_data and not source_ip:
                    source_ip = group_data['source_ip']
                if 'source_hostname' in group_data and not source_hostname:
                    source_hostname = group_data['source_hostname']
                if 'username' in group_data and not username:
                    username = group_data['username']
        
        # Build title
        title = pattern.get('title_template', 'Correlated Security Incident')
        if source_ip:
            title = title.replace('{source_ip}', source_ip)
        if username:
            title = title.replace('{username}', username)
        if source_hostname:
            title = title.replace('{hostname}', source_hostname)
        
        # Build description
        description = f"Correlated incident detected by pattern: {pattern['name']}\n\n"
        description += f"Correlation Pattern: {pattern['description']}\n"
        description += f"Related Alerts: {len(alerts)}\n\n"
        
        # Add alert summaries
        description += "Alert Summary:\n"
        for i, alert in enumerate(alerts[:10]):
            description += f"{i+1}. [{alert.severity.upper()}] {alert.title}\n"
        
        if len(alerts) > 10:
            description += f"... and {len(alerts) - 10} more alerts\n"
        
        # Create incident
        incident = Incident.objects.create(
            title=title,
            description=description,
            incident_type=pattern.get('incident_type', 'other'),
            severity=pattern.get('severity', 'high'),
            priority=pattern.get('priority', 'p2'),
            status='new',
            source_ip=source_ip,
            source_hostname=source_hostname,
            correlation_id=f"corr-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
            correlation_confidence=0.8,
            detected_at=timezone.now(),
            started_at=min(a.created_at for a in alerts),
            organization=alerts[0].organization if alerts else None,
            metadata={
                'correlation_pattern': pattern['name'],
                'correlation_description': pattern['description'],
                'matched_alerts_count': len(alerts),
            }
        )
        
        # Add alerts to incident
        incident.alerts.add(*alerts)
        
        # Add events from alerts
        for alert in alerts:
            incident.events.add(*alert.related_events.all())
        
        # Set SLA
        incident.set_sla_deadline()
        
        # Add timeline entries
        IncidentTimeline.objects.create(
            incident=incident,
            entry_type='alert',
            timestamp=incident.created_at,
            description=f"Incident created from {len(alerts)} correlated alerts using pattern: {pattern['name']}",
            metadata={'alerts_count': len(alerts), 'pattern': pattern['name']}
        )
        
        # Update alerts
        for alert in alerts:
            alert.status = 'acknowledged'
            alert.save()
        
        return incident


class IncidentManager:
    """Manages incident lifecycle and operations"""
    
    def create_manual_incident(self, title, description, severity, user, **kwargs):
        """Create an incident manually"""
        incident = Incident.objects.create(
            title=title,
            description=description,
            severity=severity,
            created_by=user,
            detected_at=timezone.now(),
            organization=user.organization,
            **kwargs
        )
        
        incident.set_sla_deadline()
        
        IncidentTimeline.objects.create(
            incident=incident,
            entry_type='action',
            timestamp=incident.created_at,
            description=f"Incident manually created by {user.username}",
            user=user
        )
        
        return incident
    
    def escalate_incident(self, incident, new_priority, reason=''):
        """Escalate incident to higher priority"""
        old_priority = incident.priority
        
        incident.priority = new_priority
        incident.is_critical = new_priority in ['p1']
        incident.set_sla_deadline()
        incident.save()
        
        IncidentTimeline.objects.create(
            incident=incident,
            entry_type='escalation',
            description=f"Incident escalated from {old_priority} to {new_priority}. Reason: {reason}",
            metadata={'old_priority': old_priority, 'new_priority': new_priority, 'reason': reason}
        )
        
        return incident
    
    def link_events_to_incident(self, incident, events, correlation_reason=''):
        """Link events to an existing incident"""
        incident.events.add(*events)
        
        if correlation_reason:
            IncidentTimeline.objects.create(
                incident=incident,
                entry_type='evidence',
                description=f"Linked {len(events)} events to incident: {correlation_reason}",
                metadata={'events_count': len(events), 'reason': correlation_reason}
            )
        
        # Update correlation confidence
        incident.correlation_confidence = min(incident.correlation_confidence + 0.1, 1.0)
        incident.save()
        
        return incident
    
    def add_ioc(self, incident, ioc_type, ioc_value, description=''):
        """Add Indicator of Compromise to incident"""
        if not incident.indicators_of_compromise:
            incident.indicators_of_compromise = []
        
        incident.indicators_of_compromise.append({
            'type': ioc_type,
            'value': ioc_value,
            'description': description,
            'added_at': timezone.now().isoformat(),
        })
        incident.save()
        
        IncidentTimeline.objects.create(
            incident=incident,
            entry_type='evidence',
            description=f"IOC added: {ioc_type} - {ioc_value}",
            metadata={'ioc_type': ioc_type, 'ioc_value': ioc_value}
        )
        
        return incident
    
    def auto_contain(self, incident):
        """Automated containment actions (placeholder for actual implementation)"""
        actions_taken = []
        
        # Block source IP at firewall
        if incident.source_ip:
            actions_taken.append(f"Blocked IP: {incident.source_ip}")
        
        # Isolate affected systems
        for system in incident.affected_systems:
            actions_taken.append(f"Isolated system: {system}")
        
        incident.status = 'containment'
        incident.contained_at = timezone.now()
        incident.save()
        
        IncidentTimeline.objects.create(
            incident=incident,
            entry_type='action',
            description=f"Auto-containment actions taken: {'; '.join(actions_taken)}",
            metadata={'actions': actions_taken}
        )
        
        return incident