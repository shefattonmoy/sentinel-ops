# apps/incidents/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from datetime import timedelta
from apps.audit.models import log_action

from .models import Incident, IncidentTimeline, IncidentNote
from .serializers import (
    IncidentSerializer,
    IncidentListSerializer,
    IncidentTimelineSerializer,
    IncidentNoteSerializer,
    IncidentStatusUpdateSerializer,
    CorrelateAlertsSerializer,
)
from .correlation import CorrelationEngine, IncidentManager


class IncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing incidents"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return IncidentListSerializer
        return IncidentSerializer

    def get_queryset(self):
        queryset = Incident.objects.select_related(
            "assigned_to", "created_by", "correlation_rule"
        ).prefetch_related("alerts", "events", "timeline", "notes")

        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        incident_type = self.request.query_params.get("incident_type")
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)

        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(source_ip__icontains=search)
            )

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        incident = serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
            detected_at=timezone.now(),
        )

        log_action(
            user=self.request.user,
            action="INCIDENT_CREATE",
            description=f"Incident created: {incident.title}",
            obj=incident,
            severity="critical" if incident.severity == "critical" else "warning",
            request=self.request,
        )

        return incident

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update incident status"""
        incident = self.get_object()
        serializer = IncidentStatusUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        old_status = incident.status
        new_status = data["status"]

        incident.status = new_status

        if new_status == "containment":
            incident.contained_at = timezone.now()
        elif new_status == "eradication":
            incident.eradicated_at = timezone.now()
        elif new_status == "recovery":
            incident.recovered_at = timezone.now()
        elif new_status == "resolved":
            incident.resolved_at = timezone.now()
            incident.resolution = data.get("resolution", "")
            if incident.resolved_at and incident.detected_at:
                incident.time_to_resolve = int(
                    (incident.resolved_at - incident.detected_at).total_seconds() / 60
                )
        elif new_status == "closed":
            incident.closed_at = timezone.now()

        if data.get("assigned_to"):
            from apps.accounts.models import User

            incident.assigned_to = User.objects.get(id=data["assigned_to"])

        incident.save()

        IncidentTimeline.objects.create(
            incident=incident,
            entry_type="status_change",
            timestamp=timezone.now(),
            description=f"Status changed from {old_status} to {new_status}",
            user=request.user,
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "note": data.get("note", ""),
            },
        )

        log_action(
            user=request.user,
            action="STATUS_CHANGE",
            description=f'Incident "{incident.title}" status changed from {old_status} to {new_status}',
            obj=incident,
            severity="info",
            request=request,
            changes={"status": {"old": old_status, "new": new_status}},
        )

        return Response(IncidentSerializer(incident).data)

    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        """Add a note to incident"""
        incident = self.get_object()

        note = IncidentNote.objects.create(
            incident=incident,
            user=request.user,
            note_type=request.data.get("note_type", "general"),
            content=request.data.get("content", ""),
            is_private=request.data.get("is_private", False),
        )

        IncidentTimeline.objects.create(
            incident=incident,
            entry_type="comment",
            description=f"Note added: {note.content[:100]}",
            user=request.user,
        )

        log_action(
            user=request.user,
            action="UPDATE",
            description=f'Note added to incident "{incident.title}"',
            obj=incident,
            severity="info",
            request=request,
        )

        return Response(IncidentNoteSerializer(note).data, status=201)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Get incident timeline"""
        incident = self.get_object()
        timeline = incident.timeline.all()
        serializer = IncidentTimelineSerializer(timeline, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def notes(self, request, pk=None):
        """Get incident notes"""
        incident = self.get_object()
        notes = incident.notes.filter(Q(is_private=False) | Q(user=request.user))
        serializer = IncidentNoteSerializer(notes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_ioc(self, request, pk=None):
        """Add Indicator of Compromise"""
        incident = self.get_object()
        manager = IncidentManager()
        incident = manager.add_ioc(
            incident,
            ioc_type=request.data.get("ioc_type", "ip"),
            ioc_value=request.data.get("ioc_value", ""),
            description=request.data.get("description", ""),
        )

        log_action(
            user=request.user,
            action="UPDATE",
            description=f'IOC added to incident "{incident.title}"',
            obj=incident,
            severity="warning",
            request=request,
        )

        return Response(IncidentSerializer(incident).data)

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        """Escalate incident priority"""
        incident = self.get_object()
        new_priority = request.data.get("priority", "p1")
        reason = request.data.get("reason", "")
        old_priority = incident.priority

        manager = IncidentManager()
        incident = manager.escalate_incident(incident, new_priority, reason)

        log_action(
            user=request.user,
            action="STATUS_CHANGE",
            description=f'Incident "{incident.title}" escalated from {old_priority} to {new_priority}',
            obj=incident,
            severity="critical",
            request=request,
            changes={"priority": {"old": old_priority, "new": new_priority}},
        )

        return Response(IncidentSerializer(incident).data)

    @action(detail=False, methods=["post"])
    def correlate(self, request):
        """Run correlation engine to create incidents from alerts"""
        engine = CorrelationEngine()
        incidents = engine.correlate_alerts(request.user.organization)

        for incident in incidents:
            log_action(
                user=request.user,
                action="INCIDENT_CREATE",
                description=f"Incident auto-created by correlation: {incident.title}",
                obj=incident,
                severity="warning",
                request=request,
            )

        return Response(
            {
                "message": f"Created {len(incidents)} incidents from correlated alerts",
                "incidents": IncidentListSerializer(incidents, many=True).data,
            }
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get incident statistics"""
        organization = request.user.organization
        queryset = Incident.objects.all()
        if organization:
            queryset = queryset.filter(organization=organization)

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        stats = {
            "total_incidents": queryset.count(),
            "open_incidents": queryset.filter(
                status__in=["new", "triaging", "investigating"]
            ).count(),
            "critical_incidents": queryset.filter(
                severity="critical",
                status__in=["new", "triaging", "investigating", "containment"],
            ).count(),
            "incidents_last_24h": queryset.filter(created_at__gte=last_24h).count(),
            "incidents_last_7d": queryset.filter(created_at__gte=last_7d).count(),
            "incidents_last_30d": queryset.filter(created_at__gte=last_30d).count(),
            "by_severity": list(
                queryset.filter(status__in=["new", "triaging", "investigating"])
                .values("severity")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "by_status": list(
                queryset.values("status").annotate(count=Count("id")).order_by("-count")
            ),
            "by_type": list(
                queryset.values("incident_type")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
            "avg_time_to_detect": queryset.filter(
                time_to_detect__isnull=False
            ).aggregate(avg=Avg("time_to_detect"))["avg"],
            "avg_time_to_resolve": queryset.filter(
                time_to_resolve__isnull=False
            ).aggregate(avg=Avg("time_to_resolve"))["avg"],
        }

        return Response(stats)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get incident dashboard data"""
        organization = request.user.organization
        queryset = Incident.objects.all()
        if organization:
            queryset = queryset.filter(organization=organization)

        open_incidents = queryset.filter(
            status__in=["new", "triaging", "investigating", "containment"]
        ).order_by("-severity", "-created_at")
        recent_resolved = queryset.filter(status__in=["resolved", "closed"]).order_by(
            "-resolved_at"
        )[:10]

        return Response(
            {
                "open_incidents": IncidentListSerializer(
                    open_incidents[:20], many=True
                ).data,
                "recently_resolved": IncidentListSerializer(
                    recent_resolved, many=True
                ).data,
                "critical_count": open_incidents.filter(severity="critical").count(),
                "overdue_count": open_incidents.filter(is_overdue=True).count(),
            }
        )
