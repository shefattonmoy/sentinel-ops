# apps/notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from .models import Notification, NotificationChannel
from .serializers import NotificationSerializer, NotificationChannelSerializer
from .service import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for user notifications"""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        ).order_by("-created_at")

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get unread notifications count and list"""
        unread = self.get_queryset().filter(is_read=False)
        return Response(
            {
                "count": unread.count(),
                "notifications": NotificationSerializer(unread[:20], many=True).data,
            }
        )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recent notifications"""
        limit = int(request.query_params.get("limit", 10))
        recent = self.get_queryset()[:limit]
        return Response(NotificationSerializer(recent, many=True).data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({"status": "ok"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"status": "ok", "message": "All notifications marked as read"})

    @action(detail=False, methods=["post"])
    def test(self, request):
        """Send a test notification"""
        service = NotificationService()
        notification = service.send_notification(
            user=request.user,
            organization=request.user.organization,
            title="Test Notification",
            message="This is a test notification from SentinelOps.",
            priority="medium",
            trigger_type="test",
        )
        return Response(
            {
                "status": "sent",
                "notification": NotificationSerializer(notification).data,
            }
        )


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notification channels"""

    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationChannel.objects.filter(
            organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test a notification channel"""
        channel = self.get_object()
        service = NotificationService()

        success = service.test_channel(channel)

        return Response(
            {
                "channel": channel.name,
                "channel_type": channel.channel_type,
                "success": success,
            }
        )

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle channel active status"""
        channel = self.get_object()
        channel.is_active = not channel.is_active
        channel.save()
        return Response(
            {
                "status": "ok",
                "is_active": channel.is_active,
            }
        )
