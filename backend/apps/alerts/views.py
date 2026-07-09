# apps/alerts/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from datetime import timedelta
from apps.audit.models import log_action

from .models import Alert, AlertComment, AlertHistory
from .serializers import (
    AlertSerializer,
    AlertListSerializer,
    AlertCommentSerializer,
    AlertHistorySerializer,
    AlertStatusUpdateSerializer,
)


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for managing alerts"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return AlertListSerializer
        return AlertSerializer

    def get_queryset(self):
        queryset = Alert.objects.select_related(
            "assigned_to", "resolved_by", "related_rule"
        ).prefetch_related("related_events", "comments")

        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source=source)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

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
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update alert status"""
        alert = self.get_object()
        serializer = AlertStatusUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        new_status = data["status"]
        note = data.get("note", "")
        old_status = alert.status

        alert.status = new_status

        if new_status == "acknowledged":
            alert.acknowledged_at = timezone.now()
            if data.get("assigned_to"):
                from apps.accounts.models import User

                alert.assigned_to = User.objects.get(id=data["assigned_to"])

        elif new_status == "investigating":
            pass

        elif new_status == "resolved":
            alert.resolved_at = timezone.now()
            alert.resolution = data.get("resolution", "")
            alert.resolved_by = request.user

        elif new_status == "closed":
            alert.closed_at = timezone.now()

        elif new_status == "false_positive":
            alert.resolved_at = timezone.now()

        alert.save()

        AlertHistory.objects.create(
            alert=alert,
            user=request.user,
            from_status=old_status,
            to_status=new_status,
            note=note,
        )

        log_action(
            user=request.user,
            action="STATUS_CHANGE",
            description=f'Alert "{alert.title}" status changed from {old_status} to {new_status}',
            obj=alert,
            severity="info",
            request=request,
            changes={"status": {"old": old_status, "new": new_status}},
        )

        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        """Add a comment to an alert"""
        alert = self.get_object()

        comment = AlertComment.objects.create(
            alert=alert, user=request.user, comment=request.data.get("comment", "")
        )

        log_action(
            user=request.user,
            action="UPDATE",
            description=f'Comment added to alert "{alert.title}"',
            obj=alert,
            severity="info",
            request=request,
        )

        return Response(AlertCommentSerializer(comment).data, status=201)

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        """Get alert comments"""
        alert = self.get_object()
        comments = alert.comments.all()
        serializer = AlertCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Get alert history"""
        alert = self.get_object()
        history = alert.history.all()
        serializer = AlertHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def link_events(self, request, pk=None):
        """Link events to alert"""
        alert = self.get_object()
        event_ids = request.data.get("event_ids", [])

        from apps.events.models import Event

        events = Event.objects.filter(id__in=event_ids)
        alert.related_events.add(*events)

        log_action(
            user=request.user,
            action="UPDATE",
            description=f'Linked {len(event_ids)} events to alert "{alert.title}"',
            obj=alert,
            severity="info",
            request=request,
        )

        return Response(
            {
                "message": f"Linked {len(event_ids)} events",
                "total_events": alert.related_events.count(),
            }
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get alert statistics"""
        organization = request.user.organization

        queryset = Alert.objects.all()
        if organization:
            queryset = queryset.filter(organization=organization)

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        stats = {
            "total_alerts": queryset.count(),
            "open_alerts": queryset.filter(status="open").count(),
            "critical_alerts": queryset.filter(
                severity="critical",
                status__in=["open", "acknowledged", "investigating"],
            ).count(),
            "alerts_last_24h": queryset.filter(created_at__gte=last_24h).count(),
            "alerts_last_7d": queryset.filter(created_at__gte=last_7d).count(),
            "alerts_last_30d": queryset.filter(created_at__gte=last_30d).count(),
            "by_severity": list(
                queryset.filter(status__in=["open", "acknowledged", "investigating"])
                .values("severity")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "by_status": list(
                queryset.values("status").annotate(count=Count("id")).order_by("-count")
            ),
            "by_source": list(
                queryset.values("source")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
            "avg_resolution_time": queryset.filter(
                status__in=["resolved", "closed"], resolved_at__isnull=False
            ).aggregate(avg_time=Avg(F("resolved_at") - F("created_at")))["avg_time"],
            "sla_compliance": {
                "total_with_sla": queryset.filter(sla_deadline__isnull=False).count(),
                "overdue": queryset.filter(is_overdue=True).count(),
            },
        }

        return Response(stats)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recent alerts"""
        limit = int(request.query_params.get("limit", 10))
        queryset = self.get_queryset()
        recent = queryset.order_by("-created_at")[:limit]
        serializer = AlertListSerializer(recent, many=True)
        return Response(serializer.data)
