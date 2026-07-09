# apps/search/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Event
from apps.alerts.models import Alert
from apps.incidents.models import Incident
from apps.logs.models import RawLog
from apps.agents.models import Agent


class GlobalSearchViewSet(viewsets.ViewSet):
    """
    Global search across all entities with advanced query syntax.

    Supported filter syntax:
    - severity:critical
    - service:ssh
    - hostname:web01
    - ip:10.0.0.5
    - user:admin
    - source:nginx
    - type:FAILED_LOGIN
    - status:open
    - category:security
    - agent:server-01
    """

    permission_classes = [IsAuthenticated]

    def _get_org_filter(self, field="agent__organization"):
        if self.request.user.organization:
            return {field: self.request.user.organization}
        return {}

    def _get_alert_org_filter(self):
        if self.request.user.organization:
            return {"organization": self.request.user.organization}
        return {}

    def parse_query(self, query: str):
        """
        Parse advanced query syntax.
        Extracts filters like severity:critical, ip:10.0.0.5 etc.
        Returns (search_terms, filters)
        """
        filters = {}
        search_terms = []

        filter_patterns = {
            "severity:": "severity__iexact",
            "service:": "source__iexact",
            "source:": "source__iexact",
            "hostname:": "source_hostname__icontains",
            "agent:": "agent__name__icontains",
            "ip:": "source_ip__iexact",
            "user:": "username__iexact",
            "username:": "username__iexact",
            "type:": "event_type__iexact",
            "event_type:": "event_type__iexact",
            "status:": "status__iexact",
            "category:": "category__iexact",
            "port:": "source_port",
        }

        words = query.split()
        for word in words:
            matched = False
            for prefix, field in filter_patterns.items():
                if word.lower().startswith(prefix):
                    value = word[len(prefix) :]
                    filters[field] = value
                    matched = True
                    break

            if not matched:
                search_terms.append(word)

        return " ".join(search_terms), filters

    @action(detail=False, methods=["post"])
    def search(self, request):
        """
        Perform global search across all entities.

        Request body:
        {
            "query": "severity:critical service:ssh failed login",
            "types": ["events", "alerts", "incidents", "logs", "agents"],
            "limit": 20,
            "time_range": "24h"  // 1h, 24h, 7d, 30d, all
        }
        """
        query = request.data.get("query", "")
        entity_types = request.data.get(
            "types", ["events", "alerts", "incidents", "logs", "agents"]
        )
        limit = request.data.get("limit", 20)
        time_range = request.data.get("time_range", "24h")

        if not query and not request.data.get("filters"):
            return Response(
                {
                    "query": query,
                    "total_results": 0,
                    "results": {},
                    "took_ms": 0,
                }
            )

        search_terms, filters = self.parse_query(query)

        # Calculate time threshold
        time_threshold = self._get_time_threshold(time_range)

        import time

        start_time = time.time()

        results = {}
        total = 0

        if "events" in entity_types:
            events_results = self._search_events(
                search_terms, filters, time_threshold, limit
            )
            results["events"] = events_results
            total += events_results.get("total", 0)

        if "alerts" in entity_types:
            alerts_results = self._search_alerts(
                search_terms, filters, time_threshold, limit
            )
            results["alerts"] = alerts_results
            total += alerts_results.get("total", 0)

        if "incidents" in entity_types:
            incidents_results = self._search_incidents(
                search_terms, filters, time_threshold, limit
            )
            results["incidents"] = incidents_results
            total += incidents_results.get("total", 0)

        if "logs" in entity_types:
            logs_results = self._search_logs(
                search_terms, filters, time_threshold, limit
            )
            results["logs"] = logs_results
            total += logs_results.get("total", 0)

        if "agents" in entity_types:
            agents_results = self._search_agents(search_terms, filters, limit)
            results["agents"] = agents_results
            total += agents_results.get("total", 0)

        took_ms = round((time.time() - start_time) * 1000, 2)

        return Response(
            {
                "query": query,
                "parsed_search_terms": search_terms,
                "parsed_filters": filters,
                "total_results": total,
                "results": results,
                "took_ms": took_ms,
            }
        )

    @action(detail=False, methods=["post"])
    def quick_search(self, request):
        """Quick search returning only top 5 results per category"""
        query = request.data.get("query", "")

        if not query:
            return Response({"results": []})

        search_terms, filters = self.parse_query(query)

        results = []

        # Search events
        events = self._search_events(search_terms, filters, None, 5)
        for e in events.get("hits", []):
            results.append(
                {
                    "type": "event",
                    "id": e["id"],
                    "title": e["event_type"],
                    "subtitle": e["message"][:100],
                    "severity": e["severity"],
                    "timestamp": e["timestamp"],
                }
            )

        # Search alerts
        alerts = self._search_alerts(search_terms, filters, None, 5)
        for a in alerts.get("hits", []):
            results.append(
                {
                    "type": "alert",
                    "id": a["id"],
                    "title": a["title"],
                    "subtitle": a["description"][:100] if a.get("description") else "",
                    "severity": a["severity"],
                    "timestamp": a["created_at"],
                }
            )

        # Search agents
        agents = self._search_agents(search_terms, filters, 3)
        for ag in agents.get("hits", []):
            results.append(
                {
                    "type": "agent",
                    "id": ag["id"],
                    "title": ag["name"],
                    "subtitle": ag["hostname"],
                    "severity": "info",
                    "timestamp": ag.get("last_heartbeat"),
                }
            )

        # Sort by timestamp
        results.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

        return Response({"results": results[:15]})

    def _get_time_threshold(self, time_range):
        """Convert time range string to datetime threshold"""
        if not time_range or time_range == "all":
            return None

        now = timezone.now()
        ranges = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }

        delta = ranges.get(time_range, timedelta(hours=24))
        return now - delta

    def _search_events(self, search_terms, filters, time_threshold, limit):
        """Search events"""
        org_filter = self._get_org_filter()
        queryset = Event.objects.filter(**org_filter)

        if time_threshold:
            queryset = queryset.filter(timestamp__gte=time_threshold)

        # Apply parsed filters
        for field, value in filters.items():
            if field in [
                "severity__iexact",
                "source__iexact",
                "source_ip__iexact",
                "username__iexact",
                "event_type__iexact",
                "source_port",
            ]:
                queryset = queryset.filter(**{field: value})
            elif field == "source_hostname__icontains":
                queryset = queryset.filter(source_hostname__icontains=value)
            elif field == "agent__name__icontains":
                queryset = queryset.filter(agent__name__icontains=value)

        # Full-text search
        if search_terms:
            queryset = queryset.filter(
                Q(message__icontains=search_terms)
                | Q(event_type__icontains=search_terms)
                | Q(source_ip__icontains=search_terms)
                | Q(username__icontains=search_terms)
                | Q(description__icontains=search_terms)
            )

        total = queryset.count()
        events = queryset.select_related("agent").order_by("-timestamp")[:limit]

        hits = []
        for e in events:
            hits.append(
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "source": e.source,
                    "source_ip": e.source_ip,
                    "username": e.username,
                    "message": e.message[:200],
                    "timestamp": e.timestamp.isoformat(),
                    "agent_name": e.agent.name,
                    "agent_hostname": e.agent.hostname,
                }
            )

        return {"total": total, "hits": hits}

    def _search_alerts(self, search_terms, filters, time_threshold, limit):
        """Search alerts"""
        org_filter = self._get_alert_org_filter()
        queryset = Alert.objects.filter(**org_filter)

        if time_threshold:
            queryset = queryset.filter(created_at__gte=time_threshold)

        # Apply filters
        for field, value in filters.items():
            if field in [
                "severity__iexact",
                "status__iexact",
                "category__iexact",
                "source__iexact",
            ]:
                queryset = queryset.filter(**{field: value})

        if search_terms:
            queryset = queryset.filter(
                Q(title__icontains=search_terms)
                | Q(description__icontains=search_terms)
                | Q(source__icontains=search_terms)
            )

        total = queryset.count()
        alerts = queryset.order_by("-created_at")[:limit]

        hits = []
        for a in alerts:
            hits.append(
                {
                    "id": str(a.id),
                    "title": a.title,
                    "description": a.description[:200] if a.description else "",
                    "severity": a.severity,
                    "status": a.status,
                    "source": a.source,
                    "category": a.category,
                    "created_at": a.created_at.isoformat(),
                    "assigned_to": a.assigned_to.username if a.assigned_to else None,
                }
            )

        return {"total": total, "hits": hits}

    def _search_incidents(self, search_terms, filters, time_threshold, limit):
        """Search incidents"""
        org_filter = self._get_alert_org_filter()
        queryset = Incident.objects.filter(**org_filter)

        if time_threshold:
            queryset = queryset.filter(created_at__gte=time_threshold)

        for field, value in filters.items():
            if field in ["severity__iexact", "status__iexact"]:
                queryset = queryset.filter(**{field: value})
            elif field == "source_ip__iexact":
                queryset = queryset.filter(source_ip__iexact=value)

        if search_terms:
            queryset = queryset.filter(
                Q(title__icontains=search_terms)
                | Q(description__icontains=search_terms)
                | Q(source_ip__icontains=search_terms)
            )

        total = queryset.count()
        incidents = queryset.order_by("-created_at")[:limit]

        hits = []
        for i in incidents:
            hits.append(
                {
                    "id": str(i.id),
                    "title": i.title,
                    "severity": i.severity,
                    "status": i.status,
                    "priority": i.priority,
                    "incident_type": i.incident_type,
                    "source_ip": i.source_ip,
                    "created_at": i.created_at.isoformat(),
                }
            )

        return {"total": total, "hits": hits}

    def _search_logs(self, search_terms, filters, time_threshold, limit):
        """Search raw logs"""
        org_filter = self._get_org_filter()
        queryset = RawLog.objects.filter(**org_filter)

        if time_threshold:
            queryset = queryset.filter(timestamp__gte=time_threshold)

        for field, value in filters.items():
            if field == "source__iexact":
                queryset = queryset.filter(source__iexact=value)

        if search_terms:
            queryset = queryset.filter(raw_message__icontains=search_terms)

        total = queryset.count()
        logs = queryset.select_related("agent").order_by("-timestamp")[:limit]

        hits = []
        for l in logs:
            hits.append(
                {
                    "id": str(l.id),
                    "source": l.source,
                    "log_level": l.log_level,
                    "message": l.raw_message[:200],
                    "timestamp": l.timestamp.isoformat(),
                    "agent_name": l.agent.name,
                    "hostname": l.hostname,
                }
            )

        return {"total": total, "hits": hits}

    def _search_agents(self, search_terms, filters, limit):
        """Search agents"""
        org_filter = self._get_alert_org_filter()
        queryset = Agent.objects.filter(is_active=True, is_deleted=False, **org_filter)

        if search_terms:
            queryset = queryset.filter(
                Q(name__icontains=search_terms)
                | Q(hostname__icontains=search_terms)
                | Q(agent_id__icontains=search_terms)
                | Q(ip_address__icontains=search_terms)
            )

        total = queryset.count()
        agents = queryset[:limit]

        hits = []
        for a in agents:
            hits.append(
                {
                    "id": str(a.id),
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "hostname": a.hostname,
                    "status": a.status,
                    "ip_address": a.ip_address,
                    "cpu_usage": a.cpu_usage,
                    "memory_usage": a.memory_usage,
                    "last_heartbeat": (
                        a.last_heartbeat.isoformat() if a.last_heartbeat else None
                    ),
                }
            )

        return {"total": total, "hits": hits}
