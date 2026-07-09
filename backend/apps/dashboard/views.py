# apps/dashboard/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg, F, Max, Min
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from datetime import datetime, timedelta
from collections import defaultdict

from apps.agents.models import Agent, AgentHeartbeat
from apps.events.models import Event
from apps.alerts.models import Alert
from apps.incidents.models import Incident
from apps.logs.models import RawLog, LogBatch
from apps.rules.models import DetectionRule


class DashboardViewSet(viewsets.ViewSet):
    """
    Complete dashboard data endpoints.
    Provides all statistics, charts, and metrics for the frontend dashboard.
    """

    permission_classes = [IsAuthenticated]

    def _get_org_filter(self, field="agent__organization"):
        """Get organization filter based on user"""
        if self.request.user.organization:
            return {field: self.request.user.organization}
        return {}

    def _get_alert_org_filter(self):
        """Get organization filter for alert/incident models"""
        if self.request.user.organization:
            return {"organization": self.request.user.organization}
        return {}

    # ============ OVERVIEW STATISTICS ============

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """
        Get main dashboard overview statistics.
        Returns counts for agents, events, alerts, incidents, and security score.
        """
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        org_filter = self._get_org_filter()
        alert_org_filter = self._get_alert_org_filter()

        # Agent statistics
        agents_queryset = Agent.objects.filter(
            is_active=True, is_deleted=False, **self._get_org_filter("organization")
        )
        agents_total = agents_queryset.count()
        agents_online = agents_queryset.filter(status="online").count()
        agents_offline = agents_queryset.filter(status="offline").count()
        agents_degraded = agents_queryset.filter(status="degraded").count()
        agents_error = agents_queryset.filter(status="error").count()

        # Event statistics
        events_total = Event.objects.filter(**org_filter).count()
        events_today = Event.objects.filter(
            timestamp__gte=today_start, **org_filter
        ).count()
        events_last_hour = Event.objects.filter(
            timestamp__gte=last_hour, **org_filter
        ).count()
        events_last_24h = Event.objects.filter(
            timestamp__gte=last_24h, **org_filter
        ).count()

        # Alert statistics
        alerts_queryset = Alert.objects.filter(**alert_org_filter)
        alerts_total = alerts_queryset.count()
        alerts_open = alerts_queryset.filter(status="open").count()
        alerts_acknowledged = alerts_queryset.filter(status="acknowledged").count()
        alerts_investigating = alerts_queryset.filter(status="investigating").count()
        alerts_resolved_today = alerts_queryset.filter(
            resolved_at__gte=today_start
        ).count()
        alerts_today = alerts_queryset.filter(created_at__gte=today_start).count()

        # Critical alerts
        critical_alerts = alerts_queryset.filter(
            severity="critical", status__in=["open", "acknowledged", "investigating"]
        ).count()

        high_alerts = alerts_queryset.filter(
            severity="high", status__in=["open", "acknowledged", "investigating"]
        ).count()

        # Overdue alerts
        overdue_alerts = alerts_queryset.filter(
            is_overdue=True, status__in=["open", "acknowledged", "investigating"]
        ).count()

        # Incident statistics
        incidents_queryset = Incident.objects.filter(**alert_org_filter)
        incidents_total = incidents_queryset.count()
        incidents_open = incidents_queryset.filter(
            status__in=[
                "new",
                "triaging",
                "investigating",
                "containment",
                "eradication",
                "recovery",
            ]
        ).count()
        incidents_critical = incidents_queryset.filter(
            severity="critical", status__in=["new", "triaging", "investigating"]
        ).count()
        incidents_today = incidents_queryset.filter(created_at__gte=today_start).count()
        incidents_resolved_today = incidents_queryset.filter(
            resolved_at__gte=today_start
        ).count()

        # Rule statistics
        rules_queryset = DetectionRule.objects.filter(**alert_org_filter)
        rules_total = rules_queryset.count()
        rules_active = rules_queryset.filter(status="active").count()

        # Log statistics
        logs_today = RawLog.objects.filter(
            timestamp__gte=today_start, **org_filter
        ).count()

        # Security score calculation
        security_score = self._calculate_security_score(
            agents_total=agents_total,
            agents_online=agents_online,
            events_last_24h=events_last_24h,
            critical_alerts=critical_alerts,
            open_incidents=incidents_open,
            overdue_alerts=overdue_alerts,
        )

        # Average response time (acknowledged - created)
        avg_response_time = self._get_avg_response_time(alerts_queryset)

        # Average resolution time (resolved - created)
        avg_resolution_time = self._get_avg_resolution_time(alerts_queryset)

        return Response(
            {
                "timestamp": now.isoformat(),
                "agents": {
                    "total": agents_total,
                    "online": agents_online,
                    "offline": agents_offline,
                    "degraded": agents_degraded,
                    "error": agents_error,
                    "health_percentage": round(
                        (agents_online / agents_total * 100) if agents_total > 0 else 0,
                        1,
                    ),
                },
                "events": {
                    "total": events_total,
                    "today": events_today,
                    "last_hour": events_last_hour,
                    "last_24h": events_last_24h,
                },
                "alerts": {
                    "total": alerts_total,
                    "open": alerts_open,
                    "acknowledged": alerts_acknowledged,
                    "investigating": alerts_investigating,
                    "today": alerts_today,
                    "resolved_today": alerts_resolved_today,
                    "critical": critical_alerts,
                    "high": high_alerts,
                    "overdue": overdue_alerts,
                    "avg_response_time_minutes": avg_response_time,
                    "avg_resolution_time_minutes": avg_resolution_time,
                },
                "incidents": {
                    "total": incidents_total,
                    "open": incidents_open,
                    "critical": incidents_critical,
                    "today": incidents_today,
                    "resolved_today": incidents_resolved_today,
                },
                "rules": {
                    "total": rules_total,
                    "active": rules_active,
                },
                "logs": {
                    "today": logs_today,
                },
                "security_score": security_score,
            }
        )

    # ============ EVENTS CHART ============

    @action(detail=False, methods=["get"])
    def events_chart(self, request):
        """
        Get events over time chart data.
        Query params: hours (default 24), interval (hour/day)
        """
        hours = int(request.query_params.get("hours", 24))
        interval = request.query_params.get("interval", "hour")
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        queryset = Event.objects.filter(timestamp__gte=since, **org_filter)

        if interval == "day":
            events = (
                queryset.annotate(period=TruncDay("timestamp"))
                .values("period")
                .annotate(
                    count=Count("id"),
                    critical=Count("id", filter=Q(severity="critical")),
                    high=Count("id", filter=Q(severity="high")),
                    medium=Count("id", filter=Q(severity="medium")),
                )
                .order_by("period")
            )
        else:
            events = (
                queryset.annotate(period=TruncHour("timestamp"))
                .values("period")
                .annotate(
                    count=Count("id"),
                    critical=Count("id", filter=Q(severity="critical")),
                    high=Count("id", filter=Q(severity="high")),
                    medium=Count("id", filter=Q(severity="medium")),
                )
                .order_by("period")
            )

        return Response(list(events))

    @action(detail=False, methods=["get"])
    def events_by_type(self, request):
        """Get events grouped by type"""
        hours = int(request.query_params.get("hours", 24))
        limit = int(request.query_params.get("limit", 20))
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        event_types = (
            Event.objects.filter(timestamp__gte=since, **org_filter)
            .values("event_type")
            .annotate(count=Count("id"), last_seen=Max("timestamp"))
            .order_by("-count")[:limit]
        )

        return Response(list(event_types))

    # ============ ALERT STATISTICS ============

    @action(detail=False, methods=["get"])
    def alert_stats(self, request):
        """Get alert statistics for charts"""
        alert_org_filter = self._get_alert_org_filter()

        queryset = Alert.objects.filter(**alert_org_filter)

        # Severity distribution (open alerts only)
        severity_dist = (
            queryset.filter(status__in=["open", "acknowledged", "investigating"])
            .values("severity")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Status distribution
        status_dist = (
            queryset.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # Top alert categories
        top_categories = (
            queryset.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Top alert sources
        top_sources = (
            queryset.values("source")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Alerts over time (last 7 days)
        last_7d = timezone.now() - timedelta(days=7)
        alerts_timeline = (
            queryset.filter(created_at__gte=last_7d)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(
                count=Count("id"),
                critical=Count("id", filter=Q(severity="critical")),
                high=Count("id", filter=Q(severity="high")),
            )
            .order_by("day")
        )

        # SLA compliance
        total_with_sla = queryset.filter(sla_deadline__isnull=False).count()
        overdue = queryset.filter(is_overdue=True).count()
        sla_compliance = round(
            (
                ((total_with_sla - overdue) / total_with_sla * 100)
                if total_with_sla > 0
                else 100
            ),
            1,
        )

        return Response(
            {
                "severity_distribution": list(severity_dist),
                "status_distribution": list(status_dist),
                "top_categories": list(top_categories),
                "top_sources": list(top_sources),
                "timeline": list(alerts_timeline),
                "sla_compliance": {
                    "total": total_with_sla,
                    "overdue": overdue,
                    "compliance_rate": sla_compliance,
                },
            }
        )

    # ============ TOP ATTACKERS ============

    @action(detail=False, methods=["get"])
    def top_ips(self, request):
        """Get top source IPs by event count"""
        hours = int(request.query_params.get("hours", 24))
        limit = int(request.query_params.get("limit", 20))
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        top_ips = (
            Event.objects.filter(
                timestamp__gte=since, source_ip__isnull=False, **org_filter
            )
            .values("source_ip")
            .annotate(
                count=Count("id"),
                unique_events=Count("event_type", distinct=True),
                last_seen=Max("timestamp"),
                first_seen=Min("timestamp"),
                countries=Count("source_hostname", distinct=True),
            )
            .order_by("-count")[:limit]
        )

        return Response(list(top_ips))

    @action(detail=False, methods=["get"])
    def top_usernames(self, request):
        """Get top usernames in events"""
        hours = int(request.query_params.get("hours", 24))
        limit = int(request.query_params.get("limit", 20))
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        top_users = (
            Event.objects.filter(
                timestamp__gte=since, username__isnull=False, **org_filter
            )
            .values("username")
            .annotate(
                count=Count("id"),
                last_seen=Max("timestamp"),
            )
            .order_by("-count")[:limit]
        )

        return Response(list(top_users))

    # ============ SERVER STATISTICS ============

    @action(detail=False, methods=["get"])
    def top_servers(self, request):
        """Get top noisy servers (most events)"""
        org_filter = self._get_org_filter()

        top_servers = (
            Event.objects.filter(**org_filter)
            .values("agent__hostname", "agent__name", "agent__agent_id")
            .annotate(
                total_events=Count("id"),
                critical_events=Count("id", filter=Q(severity="critical")),
                high_events=Count("id", filter=Q(severity="high")),
                medium_events=Count("id", filter=Q(severity="medium")),
                unique_ips=Count("source_ip", distinct=True),
            )
            .order_by("-total_events")[:10]
        )

        return Response(list(top_servers))

    @action(detail=False, methods=["get"])
    def agent_health(self, request):
        """Get health status of all agents"""
        org_filter = self._get_org_filter("organization")

        agents = Agent.objects.filter(
            is_active=True, is_deleted=False, **org_filter
        ).select_related("configuration")

        health_data = []
        for agent in agents:
            # Get latest heartbeat
            latest_hb = agent.heartbeats.first()

            health_data.append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "hostname": agent.hostname,
                    "status": agent.status,
                    "is_online": agent.is_online(),
                    "version": agent.version,
                    "agent_type": agent.agent_type,
                    "cpu_usage": agent.cpu_usage,
                    "memory_usage": agent.memory_usage,
                    "disk_usage": agent.disk_usage,
                    "last_heartbeat": (
                        agent.last_heartbeat.isoformat()
                        if agent.last_heartbeat
                        else None
                    ),
                    "uptime_seconds": agent.get_uptime(),
                    "missed_heartbeats": agent.missed_heartbeats,
                    "error_count": agent.error_count,
                    "total_logs_collected": agent.total_logs_collected,
                    "total_events_generated": agent.total_events_generated,
                    "ip_address": agent.ip_address,
                    "tags": agent.tags,
                    "latest_metrics": (
                        {
                            "cpu_cores": latest_hb.cpu_cores if latest_hb else None,
                            "memory_total_gb": (
                                round(latest_hb.memory_total / (1024**3), 2)
                                if latest_hb and latest_hb.memory_total
                                else None
                            ),
                            "disk_total_gb": (
                                round(latest_hb.disk_total / (1024**3), 2)
                                if latest_hb and latest_hb.disk_total
                                else None
                            ),
                            "process_count": (
                                latest_hb.process_count if latest_hb else None
                            ),
                            "load_average": (
                                latest_hb.load_average if latest_hb else None
                            ),
                        }
                        if latest_hb
                        else None
                    ),
                    "health_checks": {
                        "heartbeat_ok": agent.missed_heartbeats < 3,
                        "cpu_ok": not agent.cpu_usage or agent.cpu_usage < 90,
                        "memory_ok": not agent.memory_usage or agent.memory_usage < 90,
                        "disk_ok": not agent.disk_usage or agent.disk_usage < 95,
                        "errors_ok": agent.error_count < 10,
                    },
                }
            )

        return Response(health_data)

    # ============ FAILED LOGINS ============

    @action(detail=False, methods=["get"])
    def failed_logins(self, request):
        """Get failed login statistics"""
        hours = int(request.query_params.get("hours", 24))
        limit = int(request.query_params.get("limit", 10))
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        failed_logins = Event.objects.filter(
            event_type="FAILED_LOGIN", timestamp__gte=since, **org_filter
        )

        total_failed = failed_logins.count()

        # By source IP
        by_ip = list(
            failed_logins.values("source_ip")
            .annotate(
                count=Count("id"),
                unique_usernames=Count("username", distinct=True),
                last_attempt=Max("timestamp"),
            )
            .order_by("-count")[:limit]
        )

        # By username
        by_username = list(
            failed_logins.values("username")
            .annotate(
                count=Count("id"),
                unique_ips=Count("source_ip", distinct=True),
                last_attempt=Max("timestamp"),
            )
            .order_by("-count")[:limit]
        )

        # By hour
        by_hour = list(
            failed_logins.annotate(hour=TruncHour("timestamp"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # Top targeted services
        by_service = list(
            failed_logins.values("service", "source")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response(
            {
                "total_failed_logins": total_failed,
                "by_ip": by_ip,
                "by_username": by_username,
                "by_hour": by_hour,
                "by_service": by_service,
                "timeframe_hours": hours,
            }
        )

    @action(detail=False, methods=["get"])
    def successful_logins(self, request):
        """Get successful login statistics"""
        hours = int(request.query_params.get("hours", 24))
        org_filter = self._get_org_filter()

        since = timezone.now() - timedelta(hours=hours)

        success_logins = Event.objects.filter(
            event_type="SUCCESSFUL_LOGIN", timestamp__gte=since, **org_filter
        )

        return Response(
            {
                "total_successful": success_logins.count(),
                "by_ip": list(
                    success_logins.values("source_ip")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10]
                ),
                "by_username": list(
                    success_logins.values("username")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10]
                ),
            }
        )

    # ============ INCIDENT STATISTICS ============

    @action(detail=False, methods=["get"])
    def incident_stats(self, request):
        """Get incident statistics"""
        alert_org_filter = self._get_alert_org_filter()

        queryset = Incident.objects.filter(**alert_org_filter)

        now = timezone.now()
        last_30d = now - timedelta(days=30)

        # By type
        by_type = list(
            queryset.values("incident_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # By severity
        by_severity = list(
            queryset.values("severity").annotate(count=Count("id")).order_by("-count")
        )

        # By status
        by_status = list(
            queryset.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # MTTR (Mean Time to Resolve)
        mttr = queryset.filter(
            time_to_resolve__isnull=False, resolved_at__gte=last_30d
        ).aggregate(
            avg_mttr=Avg("time_to_resolve"),
            min_mttr=Min("time_to_resolve"),
            max_mttr=Max("time_to_resolve"),
        )

        # MTTD (Mean Time to Detect)
        mttd = queryset.filter(
            time_to_detect__isnull=False, detected_at__gte=last_30d
        ).aggregate(
            avg_mttd=Avg("time_to_detect"),
        )

        return Response(
            {
                "by_type": by_type,
                "by_severity": by_severity,
                "by_status": by_status,
                "mttr_minutes": {
                    "average": round(mttr["avg_mttr"], 1) if mttr["avg_mttr"] else None,
                    "minimum": mttr["min_mttr"],
                    "maximum": mttr["max_mttr"],
                },
                "mttd_minutes": {
                    "average": round(mttd["avg_mttd"], 1) if mttd["avg_mttd"] else None,
                },
            }
        )

    # ============ RECENT ACTIVITY ============

    @action(detail=False, methods=["get"])
    def recent_activity(self, request):
        """Get recent activity across all modules"""
        limit = int(request.query_params.get("limit", 20))
        org_filter = self._get_org_filter()
        alert_org_filter = self._get_alert_org_filter()

        activities = []

        # Recent events
        recent_events = Event.objects.filter(**org_filter).order_by("-timestamp")[
            :limit
        ]
        for event in recent_events:
            activities.append(
                {
                    "type": "event",
                    "id": str(event.id),
                    "timestamp": event.timestamp.isoformat(),
                    "title": event.event_type,
                    "description": event.message[:200],
                    "severity": event.severity,
                    "source": event.source,
                    "source_ip": event.source_ip,
                }
            )

        # Recent alerts
        recent_alerts = Alert.objects.filter(**alert_org_filter).order_by(
            "-created_at"
        )[:limit]
        for alert in recent_alerts:
            activities.append(
                {
                    "type": "alert",
                    "id": str(alert.id),
                    "timestamp": alert.created_at.isoformat(),
                    "title": alert.title,
                    "description": alert.description[:200],
                    "severity": alert.severity,
                    "status": alert.status,
                }
            )

        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return Response(activities[:limit])

    # ============ HELPER METHODS ============

    def _calculate_security_score(
        self,
        agents_total,
        agents_online,
        events_last_24h,
        critical_alerts,
        open_incidents,
        overdue_alerts,
    ):
        """Calculate security score (0-100)"""
        score = 100

        # Agent health deduction (max 30)
        if agents_total > 0:
            agent_health_pct = (agents_online / agents_total) * 100
            score -= (100 - agent_health_pct) * 0.3

        # Critical alerts deduction (max 25)
        score -= min(critical_alerts * 5, 25)

        # Open incidents deduction (max 20)
        score -= min(open_incidents * 3, 20)

        # Overdue alerts deduction (max 15)
        score -= min(overdue_alerts * 3, 15)

        # High event volume deduction (max 10)
        if events_last_24h > 100000:
            score -= 10
        elif events_last_24h > 50000:
            score -= 7
        elif events_last_24h > 10000:
            score -= 3

        return max(0, min(100, round(score)))

    def _get_avg_response_time(self, alerts_queryset):
        """Calculate average response time in minutes"""
        result = (
            alerts_queryset.filter(
                acknowledged_at__isnull=False, created_at__isnull=False
            )
            .annotate(response_time=F("acknowledged_at") - F("created_at"))
            .aggregate(avg=Avg("response_time"))
        )

        if result["avg"]:
            return round(result["avg"].total_seconds() / 60, 1)
        return 0

    def _get_avg_resolution_time(self, alerts_queryset):
        """Calculate average resolution time in minutes"""
        result = (
            alerts_queryset.filter(resolved_at__isnull=False, created_at__isnull=False)
            .annotate(resolution_time=F("resolved_at") - F("created_at"))
            .aggregate(avg=Avg("resolution_time"))
        )

        if result["avg"]:
            return round(result["avg"].total_seconds() / 60, 1)
        return 0


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """Manage dashboard widgets"""

    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get_queryset(self):
        from .models import DashboardWidget

        return DashboardWidget.objects.filter(
            organization=self.request.user.organization
        )

    def list(self, request):
        return Response([])
