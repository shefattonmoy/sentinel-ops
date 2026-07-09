from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event
from apps.alerts.models import Alert
from apps.incidents.models import Incident
from apps.agents.models import Agent


class ForensicsViewSet(viewsets.ViewSet):
    """Digital Forensics API"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def host_timeline(self, request):
        """Get complete forensic timeline for a host"""
        host = request.query_params.get("host")
        hours = int(request.query_params.get("hours", 24))
        entry_types = request.query_params.get("types", "") 

        if not host:
            return Response({"error": "Host identifier required"}, status=400)

        since = timezone.now() - timedelta(hours=hours)
        selected_types = entry_types.split(",") if entry_types else ["event", "alert", "incident"]

        # Determine if host is an IP address or hostname
        import re
        is_ip = re.match(r'^\d+\.\d+\.\d+\.\d+$', host) is not None

        timeline = []

        # Events
        if "event" in selected_types:
            # Build query based on whether input is IP or hostname
            if is_ip:
                event_filter = Q(source_ip=host) | Q(target_ip=host)
            else:
                # Hostname - only search hostname fields, NOT IP fields
                event_filter = Q(source_hostname__icontains=host) | Q(agent__hostname__icontains=host)

            events = (
                Event.objects.filter(
                    event_filter,
                    timestamp__gte=since,
                )
                .select_related("agent")
                .order_by("timestamp")[:500]
            )

            for e in events:
                timeline.append({
                    "id": str(e.id),
                    "type": "event",
                    "icon": "📊",
                    "timestamp": e.timestamp.isoformat(),
                    "title": e.event_type.replace("_", " ").title(),
                    "description": e.message[:300],
                    "severity": e.severity,
                    "source": e.source,
                    "source_ip": e.source_ip,
                    "username": e.username,
                    "agent": e.agent.name if e.agent else None,
                })

        # Alerts
        if "alert" in selected_types:
            alerts = Alert.objects.filter(created_at__gte=since)
            if request.user.organization:
                alerts = alerts.filter(organization=request.user.organization)

            host_alerts = []
            for a in alerts:
                metadata = a.metadata or {}
                context = metadata.get("context", {})
                for group in context.get("triggered_groups", []):
                    gdata = group.get("group", {})
                    if host in str(gdata.get("source_ip", "")) or host in str(gdata.get("source_hostname", "")):
                        host_alerts.append(a)
                        break

            for a in host_alerts[:50]:
                timeline.append({
                    "id": str(a.id),
                    "type": "alert",
                    "icon": "🚨",
                    "timestamp": a.created_at.isoformat(),
                    "title": a.title,
                    "description": a.description[:300],
                    "severity": a.severity,
                    "source": a.source,
                    "status": a.status,
                })

        # Incidents
        if "incident" in selected_types:
            incidents = Incident.objects.filter(created_at__gte=since)
            if request.user.organization:
                incidents = incidents.filter(organization=request.user.organization)

            # Same fix for incidents - check if IP or hostname
            if is_ip:
                incident_filter = Q(source_ip=host)
            else:
                incident_filter = Q(source_hostname__icontains=host)

            host_incidents = incidents.filter(incident_filter)[:20]

            for i in host_incidents:
                timeline.append({
                    "id": str(i.id),
                    "type": "incident",
                    "icon": "🔴",
                    "timestamp": i.created_at.isoformat(),
                    "title": i.title,
                    "description": i.description[:300],
                    "severity": i.severity,
                    "source": "incident",
                    "status": i.status,
                })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return Response({
            "host": host,
            "is_ip": is_ip,
            "timeframe_hours": hours,
            "total_entries": len(timeline),
            "timeline": timeline,
        })
    
    @action(detail=False, methods=["get"])
    def attack_chain(self, request):
        """Reconstruct attack chain for an IP"""
        ip = request.query_params.get("ip")
        if not ip:
            return Response({"error": "IP address required"}, status=400)

        events = Event.objects.filter(source_ip=ip).order_by("timestamp")

        if not events.exists():
            return Response(
                {"ip": ip, "chain": [], "message": "No events found for this IP"}
            )

        chain = []
        current_stage = None
        stage_events = []

        stage_order = [
            "reconnaissance",
            "weaponization",
            "delivery",
            "exploitation",
            "installation",
            "command_and_control",
            "actions_on_objective",
        ]

        for event in events:
            stage = self._classify_stage(event.event_type)

            if stage != current_stage and stage_events:
                chain.append(
                    {
                        "stage": current_stage,
                        "stage_order": (
                            stage_order.index(current_stage)
                            if current_stage in stage_order
                            else 99
                        ),
                        "event_count": len(stage_events),
                        "start_time": stage_events[0]["timestamp"],
                        "end_time": stage_events[-1]["timestamp"],
                        "events": stage_events,
                    }
                )
                stage_events = []

            current_stage = stage
            stage_events.append(
                {
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "message": event.message[:200],
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        # Add last stage
        if stage_events:
            chain.append(
                {
                    "stage": current_stage,
                    "stage_order": (
                        stage_order.index(current_stage)
                        if current_stage in stage_order
                        else 99
                    ),
                    "event_count": len(stage_events),
                    "start_time": stage_events[0]["timestamp"],
                    "end_time": stage_events[-1]["timestamp"],
                    "events": stage_events,
                }
            )

        # Sort by stage order
        chain.sort(key=lambda x: x["stage_order"])

        return Response(
            {
                "ip": ip,
                "total_events": events.count(),
                "first_seen": events.first().timestamp.isoformat(),
                "last_seen": events.last().timestamp.isoformat(),
                "chain": chain,
            }
        )

    @action(detail=False, methods=["get"])
    def hosts(self, request):
        """Get list of hosts with forensic data"""
        org = request.user.organization
        since = timezone.now() - timedelta(days=7)

        # Get hosts from agents
        agents = Agent.objects.filter(is_active=True)
        if org:
            agents = agents.filter(organization=org)

        hosts = []
        for agent in agents:
            event_count = Event.objects.filter(
                Q(source_hostname=agent.hostname) | Q(agent=agent), timestamp__gte=since
            ).count()

            alert_count = (
                Alert.objects.filter(
                    created_at__gte=since, metadata__icontains=agent.hostname
                ).count()
                if org
                else 0
            )

            hosts.append(
                {
                    "hostname": agent.hostname,
                    "ip": agent.ip_address,
                    "name": agent.name,
                    "status": agent.status,
                    "events_7d": event_count,
                    "alerts_7d": alert_count,
                }
            )

        return Response(hosts)

    def _classify_stage(self, event_type):
        """Classify event into attack chain stage"""
        stages = {
            "INVALID_USER": "reconnaissance",
            "FAILED_LOGIN": "reconnaissance",
            "NETWORK_EVENT": "reconnaissance",
            "DATABASE_QUERY": "reconnaissance",
            "BRUTE_FORCE_ATTEMPT": "delivery",
            "ACCESS_DENIED": "exploitation",
            "SUCCESSFUL_LOGIN": "exploitation",
            "SUDO_COMMAND": "installation",
            "USER_CREATED": "installation",
            "DJANGO_ERROR": "exploitation",
            "SERVER_ERROR": "actions_on_objective",
            "CONTAINER_CRASH": "actions_on_objective",
            "CONTAINER_OOM": "actions_on_objective",
            "OOM_KILLER": "actions_on_objective",
            "KERNEL_PANIC": "actions_on_objective",
            "SERVICE_FAILURE": "actions_on_objective",
            "DISK_ERROR": "actions_on_objective",
        }
        return stages.get(event_type, "unknown")

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get forensics statistics"""
        org = request.user.organization
        since = timezone.now() - timedelta(days=7)

        events = Event.objects.filter(timestamp__gte=since)
        if org:
            events = events.filter(agent__organization=org)

        return Response(
            {
                "total_events_7d": events.count(),
                "unique_ips": events.filter(source_ip__isnull=False)
                .values("source_ip")
                .distinct()
                .count(),
                "unique_hosts": events.filter(source_hostname__isnull=False)
                .values("source_hostname")
                .distinct()
                .count(),
                "top_event_types": list(
                    events.values("event_type")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10]
                ),
                "top_ips": list(
                    events.filter(source_ip__isnull=False)
                    .values("source_ip")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10]
                ),
            }
        )
