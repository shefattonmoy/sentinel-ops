from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Playbook, PlaybookExecution
from .serializers import PlaybookSerializer, PlaybookExecutionSerializer
from .engine import PlaybookEngine

class PlaybookViewSet(viewsets.ModelViewSet):
    """Manage automated playbooks"""
    serializer_class = PlaybookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Playbook.objects.filter(
            organization=self.request.user.organization
        ).order_by('-updated_at')
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a playbook manually"""
        playbook = self.get_object()
        
        trigger_event = request.data.get('trigger_event', {})
        trigger_event['triggered_by'] = request.user.username
        trigger_event['triggered_at'] = timezone.now().isoformat()
        
        engine = PlaybookEngine()
        execution = engine.execute_playbook(playbook, trigger_event)
        
        return Response({
            'execution_id': str(execution.id),
            'status': execution.status,
            'results': execution.results,
        })
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get execution history for a playbook"""
        playbook = self.get_object()
        executions = playbook.executions.all()[:50]
        return Response(PlaybookExecutionSerializer(executions, many=True).data)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Get pre-built playbook templates"""
        templates = [
            {
                'name': 'Brute Force Response',
                'description': 'Automatically respond to brute force attacks',
                'trigger_type': 'alert',
                'trigger_conditions': {
                    'event_type': 'FAILED_LOGIN',
                    'threshold': 5,
                    'timeframe_minutes': 5,
                },
                'actions': [
                    {'type': 'block_ip', 'config': {'ip': '{{source_ip}}'}},
                    {'type': 'create_alert', 'config': {'title': 'Brute Force Blocked', 'severity': 'high'}},
                    {'type': 'send_notification', 'config': {'title': 'IP Blocked', 'message': 'Auto-blocked {{source_ip}} for brute force'}},
                ],
            },
            {
                'name': 'Container Failure Response',
                'description': 'Respond to container crashes',
                'trigger_type': 'threshold',
                'trigger_conditions': {
                    'event_type': 'CONTAINER_CRASH',
                    'threshold': 3,
                    'timeframe_minutes': 10,
                },
                'actions': [
                    {'type': 'create_incident', 'config': {'title': 'Container Crash Loop', 'severity': 'critical'}},
                    {'type': 'send_notification', 'config': {'title': 'Container Failure', 'priority': 'critical'}},
                ],
            },
            {
                'name': 'Suspicious Activity Alert',
                'description': 'Alert on suspicious user activity',
                'trigger_type': 'alert',
                'trigger_conditions': {
                    'event_type': 'SUDO_COMMAND',
                    'threshold': 2,
                    'timeframe_minutes': 10,
                },
                'actions': [
                    {'type': 'create_alert', 'config': {'title': 'Suspicious Sudo Activity', 'severity': 'high'}},
                    {'type': 'webhook', 'config': {'url': '', 'method': 'POST'}},
                ],
            },
        ]
        return Response(templates)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get playbook statistics"""
        playbooks = self.get_queryset()
        
        return Response({
            'total_playbooks': playbooks.count(),
            'active_playbooks': playbooks.filter(is_active=True).count(),
            'total_executions': PlaybookExecution.objects.filter(playbook__in=playbooks).count(),
            'success_rate': 0,  # Calculate from executions
            'recent_executions': PlaybookExecutionSerializer(
                PlaybookExecution.objects.filter(playbook__in=playbooks).order_by('-started_at')[:10],
                many=True
            ).data,
        })