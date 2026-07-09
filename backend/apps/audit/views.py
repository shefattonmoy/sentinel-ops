# apps/audit/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogListView(generics.ListAPIView):
    """List audit logs"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'severity', 'user']
    search_fields = ['description', 'username', 'object_repr']
    ordering_fields = ['timestamp', 'action', 'severity']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type')
        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)
        return queryset