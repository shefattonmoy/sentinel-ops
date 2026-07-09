from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import ExportSchedule, ExportRun
from .serializers import ExportScheduleSerializer, ExportRunSerializer
from .tasks import execute_export

class ExportScheduleViewSet(viewsets.ModelViewSet):
    """Manage scheduled exports"""
    serializer_class = ExportScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ExportSchedule.objects.filter(
            organization=self.request.user.organization
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        schedule = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user,
        )
        # Set initial next_run
        from .tasks import calculate_next_run
        schedule.next_run = calculate_next_run(schedule)
        schedule.save()
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Execute a scheduled export immediately"""
        schedule = self.get_object()
        
        try:
            execute_export(str(schedule.id))
            return Response({'status': 'Export executed successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """Get execution history"""
        schedule = self.get_object()
        runs = schedule.runs.all()[:50]
        return Response(ExportRunSerializer(runs, many=True).data)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle schedule active status"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save()
        return Response({
            'status': 'ok',
            'is_active': schedule.is_active,
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get scheduler statistics"""
        schedules = self.get_queryset()
        runs = ExportRun.objects.filter(schedule__in=schedules)
        
        return Response({
            'total_schedules': schedules.count(),
            'active_schedules': schedules.filter(is_active=True).count(),
            'total_runs': runs.count(),
            'successful_runs': runs.filter(status='completed').count(),
            'failed_runs': runs.filter(status='failed').count(),
            'upcoming': ExportScheduleSerializer(
                schedules.filter(is_active=True).order_by('next_run')[:5],
                many=True
            ).data,
        })