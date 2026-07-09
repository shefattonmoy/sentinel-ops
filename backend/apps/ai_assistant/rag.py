# apps/ai_assistant/rag.py
import json
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
import logging

logger = logging.getLogger(__name__)

class SecurityRAG:
    """Retrieval-Augmented Generation for security data"""
    
    def __init__(self, user):
        self.user = user
        self.org = user.organization
    
    def answer_query(self, query):
        """Answer a natural language query about security data"""
        query_lower = query.lower()
        
        # Parse intent from query
        if any(word in query_lower for word in ['alert', 'alerts', 'critical', 'warning']):
            return self._handle_alert_query(query)
        
        elif any(word in query_lower for word in ['ip', 'attacker', 'attacking', 'source']):
            return self._handle_ip_query(query)
        
        elif any(word in query_lower for word in ['event', 'events', 'happened', 'today', 'yesterday']):
            return self._handle_event_query(query)
        
        elif any(word in query_lower for word in ['incident', 'incidents', 'breach']):
            return self._handle_incident_query(query)
        
        elif any(word in query_lower for word in ['agent', 'server', 'host', 'online', 'offline']):
            return self._handle_agent_query(query)
        
        elif any(word in query_lower for word in ['score', 'risk', 'security score']):
            return self._handle_score_query(query)
        
        elif any(word in query_lower for word in ['summary', 'overview', 'status', 'report']):
            return self._handle_summary_query(query)
        
        elif any(word in query_lower for word in ['top', 'most', 'highest', 'worst']):
            return self._handle_top_query(query)
        
        else:
            return self._handle_general_query(query)
    
    def _handle_alert_query(self, query):
        """Handle alert-related queries"""
        from apps.alerts.models import Alert
        
        query_lower = query.lower()
        alerts = Alert.objects.all()
        if self.org:
            alerts = alerts.filter(organization=self.org)
        
        # Determine timeframe
        if 'today' in query_lower:
            since = timezone.now().replace(hour=0, minute=0, second=0)
            alerts = alerts.filter(created_at__gte=since)
            timeframe = 'today'
        elif '24 hour' in query_lower or 'last day' in query_lower:
            since = timezone.now() - timedelta(hours=24)
            alerts = alerts.filter(created_at__gte=since)
            timeframe = 'last 24 hours'
        elif 'week' in query_lower:
            since = timezone.now() - timedelta(days=7)
            alerts = alerts.filter(created_at__gte=since)
            timeframe = 'last 7 days'
        else:
            timeframe = 'all time'
        
        # Filter by severity
        if 'critical' in query_lower:
            alerts = alerts.filter(severity='critical')
            severity_filter = 'critical'
        elif 'high' in query_lower:
            alerts = alerts.filter(severity='high')
            severity_filter = 'high'
        else:
            severity_filter = 'all'
        
        total = alerts.count()
        open_count = alerts.filter(status='open').count()
        
        response = f"📊 **Alerts Summary** ({timeframe}, {severity_filter} severity)\n\n"
        response += f"- **Total**: {total} alerts\n"
        response += f"- **Open**: {open_count} alerts\n"
        response += f"- **Acknowledged**: {alerts.filter(status='acknowledged').count()}\n"
        response += f"- **Resolved**: {alerts.filter(status='resolved').count()}\n\n"
        
        if total > 0:
            response += "**Recent Critical Alerts:**\n"
            for alert in alerts.filter(severity__in=['critical', 'high']).order_by('-created_at')[:5]:
                response += f"- 🚨 {alert.title} ({alert.severity}) - {alert.created_at.strftime('%H:%M')}\n"
        
        return response
    
    def _handle_ip_query(self, query):
        """Handle IP-related queries"""
        from apps.events.models import Event
        from apps.threat_intel.models import ThreatScore
        
        query_lower = query.lower()
        events = Event.objects.all()
        if self.org:
            events = events.filter(agent__organization=self.org)
        
        # Try to extract IP from query
        import re
        ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', query)
        
        if ip_match:
            ip = ip_match.group(0)
            ip_events = events.filter(source_ip=ip)
            threat = ThreatScore.objects.filter(source_ip=ip, organization=self.org).first()
            
            response = f"🔍 **IP Analysis: {ip}**\n\n"
            response += f"- **Total Events**: {ip_events.count()}\n"
            response += f"- **First Seen**: {ip_events.order_by('timestamp').first().timestamp.strftime('%Y-%m-%d %H:%M') if ip_events.exists() else 'N/A'}\n"
            response += f"- **Last Seen**: {ip_events.order_by('-timestamp').first().timestamp.strftime('%Y-%m-%d %H:%M') if ip_events.exists() else 'N/A'}\n"
            
            if threat:
                response += f"- **Threat Score**: {threat.threat_score}/100 ({threat.risk_level})\n"
                response += f"- **Known Attacker**: {'Yes ⚠️' if threat.is_known_attacker else 'No'}\n"
            
            return response
        
        # Top attacking IPs
        since = timezone.now() - timedelta(hours=24)
        top_ips = events.filter(timestamp__gte=since, source_ip__isnull=False).values('source_ip').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        response = "🌍 **Top Attacking IPs (Last 24h)**\n\n"
        for i, ip in enumerate(top_ips, 1):
            response += f"{i}. `{ip['source_ip']}` - {ip['count']} events\n"
        
        return response
    
    def _handle_event_query(self, query):
        """Handle event-related queries"""
        from apps.events.models import Event
        
        events = Event.objects.all()
        if self.org:
            events = events.filter(agent__organization=self.org)
        
        query_lower = query.lower()
        
        if 'today' in query_lower:
            since = timezone.now().replace(hour=0, minute=0, second=0)
            events = events.filter(timestamp__gte=since)
            timeframe = 'today'
        elif 'yesterday' in query_lower:
            yesterday = timezone.now().date() - timedelta(days=1)
            since = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
            until = since + timedelta(days=1)
            events = events.filter(timestamp__gte=since, timestamp__lt=until)
            timeframe = 'yesterday'
        else:
            since = timezone.now() - timedelta(hours=24)
            events = events.filter(timestamp__gte=since)
            timeframe = 'last 24 hours'
        
        total = events.count()
        
        response = f"📈 **Events Summary** ({timeframe})\n\n"
        response += f"- **Total Events**: {total:,}\n"
        response += f"- **Event Types**: {events.values('event_type').distinct().count()}\n\n"
        
        response += "**Top Event Types:**\n"
        for et in events.values('event_type').annotate(count=Count('id')).order_by('-count')[:5]:
            response += f"- {et['event_type']}: {et['count']}\n"
        
        return response
    
    def _handle_incident_query(self, query):
        """Handle incident-related queries"""
        from apps.incidents.models import Incident
        
        incidents = Incident.objects.all()
        if self.org:
            incidents = incidents.filter(organization=self.org)
        
        open_incidents = incidents.filter(status__in=['new', 'triaging', 'investigating'])
        critical = open_incidents.filter(severity='critical')
        
        response = "⚖️ **Incidents Status**\n\n"
        response += f"- **Open Incidents**: {open_incidents.count()}\n"
        response += f"- **Critical**: {critical.count()} ⚠️\n"
        response += f"- **Resolved (30d)**: {incidents.filter(status='resolved', resolved_at__gte=timezone.now()-timedelta(days=30)).count()}\n\n"
        
        if critical.exists():
            response += "**Active Critical Incidents:**\n"
            for inc in critical.order_by('-created_at')[:3]:
                response += f"- 🔴 {inc.title}\n"
        
        return response
    
    def _handle_agent_query(self, query):
        """Handle agent-related queries"""
        from apps.agents.models import Agent
        
        agents = Agent.objects.filter(is_active=True)
        if self.org:
            agents = agents.filter(organization=self.org)
        
        online = agents.filter(status='online').count()
        total = agents.count()
        
        response = f"🖥️ **Agent Status**\n\n"
        response += f"- **Online**: {online}/{total}\n"
        response += f"- **Offline**: {agents.filter(status='offline').count()}\n"
        response += f"- **CPU Avg**: {agents.filter(cpu_usage__isnull=False).aggregate(avg=Avg('cpu_usage'))['avg'] or 0:.1f}%\n"
        response += f"- **Memory Avg**: {agents.filter(memory_usage__isnull=False).aggregate(avg=Avg('memory_usage'))['avg'] or 0:.1f}%\n\n"
        
        if agents.filter(status='offline').exists():
            response += "**Offline Agents:**\n"
            for agent in agents.filter(status='offline')[:5]:
                response += f"- 🔴 {agent.name} ({agent.hostname})\n"
        
        return response
    
    def _handle_score_query(self, query):
        """Handle security score queries"""
        response = "🛡️ **Security Score Analysis**\n\n"
        response += self._generate_security_score()
        return response
    
    def _handle_summary_query(self, query):
        """Generate comprehensive summary"""
        response = "📋 **SentinelOps Security Summary**\n\n"
        response += self._generate_security_score()
        response += "\n" + self._handle_agent_query("")
        response += "\n" + self._handle_alert_query("critical today")
        return response
    
    def _handle_top_query(self, query):
        """Handle 'top X' queries"""
        from apps.events.models import Event
        
        query_lower = query.lower()
        since = timezone.now() - timedelta(hours=24)
        events = Event.objects.filter(timestamp__gte=since)
        if self.org:
            events = events.filter(agent__organization=self.org)
        
        response = "🏆 **Top Statistics (Last 24h)**\n\n"
        
        # Top IPs
        response += "**Top Attacking IPs:**\n"
        for ip in events.filter(source_ip__isnull=False).values('source_ip').annotate(count=Count('id')).order_by('-count')[:5]:
            response += f"- `{ip['source_ip']}`: {ip['count']} events\n"
        
        # Top events
        response += "\n**Top Event Types:**\n"
        for et in events.values('event_type').annotate(count=Count('id')).order_by('-count')[:5]:
            response += f"- {et['event_type']}: {et['count']}\n"
        
        return response
    
    def _handle_general_query(self, query):
        """Handle general/unrecognized queries"""
        return self._handle_summary_query(query)
    
    def _generate_security_score(self):
        """Generate security score breakdown"""
        from apps.alerts.models import Alert
        from apps.incidents.models import Incident
        from apps.agents.models import Agent
        
        alerts = Alert.objects.all()
        incidents = Incident.objects.filter(status__in=['new', 'triaging', 'investigating'])
        agents = Agent.objects.filter(is_active=True)
        
        if self.org:
            alerts = alerts.filter(organization=self.org)
            incidents = incidents.filter(organization=self.org)
            agents = agents.filter(organization=self.org)
        
        critical_alerts = alerts.filter(severity='critical', status='open').count()
        open_incidents = incidents.count()
        agents_online = agents.filter(status='online').count()
        agents_total = agents.count()
        
        score = 100
        score -= min(critical_alerts * 5, 30)
        score -= min(open_incidents * 3, 20)
        if agents_total > 0:
            score -= (1 - agents_online/agents_total) * 30
        
        score = max(0, min(100, round(score)))
        
        emoji = '🟢' if score >= 80 else '🟡' if score >= 50 else '🔴'
        
        return f"{emoji} **Overall Score: {score}/100**\n"