# apps/rules/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Sum

from .models import DetectionRule, RuleExecution, RuleTemplate
from .serializers import (
    DetectionRuleSerializer,
    RuleExecutionSerializer,
    RuleTemplateSerializer
)
from .engine import RuleEngine, AlertGenerator

class DetectionRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing detection rules"""
    serializer_class = DetectionRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DetectionRule.objects.prefetch_related('agents', 'agent_groups')
        
        if self.request.user.organization:
            queryset = queryset.filter(
                Q(organization=self.request.user.organization) |
                Q(organization__isnull=True)
            )
        
        # Filters
        rule_type = self.request.query_params.get('rule_type')
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('priority', '-created_at')
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization
        )
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a rule against current events"""
        rule = self.get_object()
        
        engine = RuleEngine()
        is_triggered, context = engine.evaluate_rule(rule)
        
        return Response({
            'rule_id': str(rule.id),
            'rule_name': rule.name,
            'is_triggered': is_triggered,
            'context': context,
        })
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a rule and generate alert if triggered"""
        rule = self.get_object()
        
        engine = RuleEngine()
        is_triggered, context = engine.evaluate_rule(rule)
        
        if is_triggered:
            generator = AlertGenerator()
            alert = generator.generate_alert(rule, context)
            
            return Response({
                'triggered': True,
                'alert_id': str(alert.id) if alert else None,
                'context': context,
            })
        
        return Response({
            'triggered': False,
            'context': context,
        })
    
    @action(detail=False, methods=['post'])
    def execute_all(self, request):
        """Execute all active rules"""
        organization = request.user.organization
        
        engine = RuleEngine()
        triggered = engine.evaluate_all_active_rules(organization)
        
        generator = AlertGenerator()
        alerts_created = []
        
        for rule, context in triggered:
            alert = generator.generate_alert(rule, context)
            if alert:
                alerts_created.append({
                    'alert_id': str(alert.id),
                    'rule_name': rule.name,
                    'severity': alert.severity,
                })
        
        return Response({
            'rules_evaluated': DetectionRule.objects.filter(status='active').count(),
            'rules_triggered': len(triggered),
            'alerts_created': len(alerts_created),
            'alerts': alerts_created,
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get rule statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_rules': queryset.count(),
            'active_rules': queryset.filter(status='active').count(),
            'paused_rules': queryset.filter(status='paused').count(),
            'by_type': list(
                queryset.values('rule_type').annotate(
                    count=Count('id')
                ).order_by('-count')
            ),
            'by_severity': list(
                queryset.values('severity').annotate(
                    count=Count('id')
                ).order_by('-count')
            ),
            'total_alerts_generated': queryset.aggregate(
                total=Sum('alerts_generated')
            )['total'] or 0,
            'recent_executions': RuleExecution.objects.filter(
                rule__in=queryset
            ).order_by('-executed_at')[:10].values(
                'rule__name', 'is_triggered', 'executed_at'
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def create_from_template(self, request):
        """Create a rule from a template"""
        template_id = request.data.get('template_id')
        
        try:
            template = RuleTemplate.objects.get(id=template_id)
        except RuleTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=404
            )
        
        rule = DetectionRule.objects.create(
            name=request.data.get('name', template.name),
            description=template.description,
            rule_type=template.rule_type,
            conditions=template.conditions,
            actions=template.actions,
            severity=template.severity,
            category=template.category,
            created_by=request.user,
            organization=request.user.organization,
        )
        
        template.use_count += 1
        template.save()
        
        serializer = self.get_serializer(rule)
        return Response(serializer.data, status=201)


class RuleTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing rule templates"""
    serializer_class = RuleTemplateSerializer
    permission_classes = [IsAuthenticated]
    queryset = RuleTemplate.objects.all()