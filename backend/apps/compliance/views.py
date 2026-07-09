from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ComplianceFramework, ComplianceControl, ComplianceEvidence
from .importer import import_compliance_data

class ComplianceViewSet(viewsets.ViewSet):
    """Compliance Management API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def frameworks(self, request):
        """Get all compliance frameworks with coverage"""
        frameworks = ComplianceFramework.objects.prefetch_related('controls__evidence')
        
        data = []
        for fw in frameworks:
            controls = []
            covered_count = 0
            
            for ctrl in fw.controls.all():
                evidence = ComplianceEvidence.objects.filter(
                    control=ctrl,
                    organization=request.user.organization
                )
                is_covered = evidence.exists()
                if is_covered:
                    covered_count += 1
                
                controls.append({
                    'control_id': ctrl.control_id,
                    'title': ctrl.title,
                    'category': ctrl.category,
                    'description': ctrl.description,
                    'covered': is_covered,
                    'evidence_count': evidence.count(),
                    'last_evidence': evidence.order_by('-collected_at').first().collected_at.isoformat() if evidence.exists() else None,
                })
            
            total = len(controls)
            data.append({
                'id': str(fw.id),
                'name': fw.name,
                'description': fw.description,
                'total_controls': total,
                'covered_controls': covered_count,
                'compliance_pct': round(covered_count / total * 100, 1) if total > 0 else 0,
                'controls': controls,
            })
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def generate_evidence(self, request):
        """Auto-generate compliance evidence from events"""
        framework_name = request.data.get('framework', 'SOC2')
        days = int(request.data.get('days', 30))
        
        # Case-insensitive lookup with fallbacks
        try:
            framework = ComplianceFramework.objects.get(name__iexact=framework_name)
        except ComplianceFramework.DoesNotExist:
            # Try multiple variations
            framework = ComplianceFramework.objects.filter(
                Q(name__iexact=framework_name) |
                Q(name__iexact=framework_name.upper()) |
                Q(name__iexact=framework_name.lower()) |
                Q(name__icontains=framework_name)
            ).first()
            
            if not framework:
                return Response({
                    'error': f'Framework "{framework_name}" not found',
                    'available_frameworks': list(
                        ComplianceFramework.objects.values_list('name', flat=True)
                    ),
                }, status=404)
        
        # Check if framework has controls
        if not framework.controls.exists():
            return Response({
                'error': f'Framework "{framework.name}" has no controls defined',
                'message': 'Import compliance data first using /api/compliance/import-frameworks/',
            }, status=400)
        
        from apps.events.models import Event
        now = timezone.now()
        period_start = now - timedelta(days=days)
        
        evidence_created = 0
        evidence_skipped = 0
        errors = []
        
        for control in framework.controls.all():
            for event_type in control.mapped_events:
                try:
                    events = Event.objects.filter(
                        event_type=event_type,
                        timestamp__gte=period_start,
                    )
                    if request.user.organization:
                        events = events.filter(agent__organization=request.user.organization)
                    
                    count = events.count()
                    if count > 0:
                        # Check if evidence already exists for this period
                        existing = ComplianceEvidence.objects.filter(
                            control=control,
                            organization=request.user.organization,
                            evidence_type='event_log',
                            period_start=period_start,
                            period_end=now,
                        ).first()
                        
                        if not existing:
                            ComplianceEvidence.objects.create(
                                control=control,
                                organization=request.user.organization,
                                evidence_type='event_log',
                                description=f'{count} {event_type} events detected in {days} days',
                                data={
                                    'event_type': event_type,
                                    'count': count,
                                    'first_seen': events.first().timestamp.isoformat() if events.first() else None,
                                    'last_seen': events.last().timestamp.isoformat() if events.last() else None,
                                },
                                period_start=period_start,
                                period_end=now,
                            )
                            evidence_created += 1
                        else:
                            evidence_skipped += 1
                except Exception as e:
                    errors.append(f'{control.control_id}/{event_type}: {str(e)}')
        
        return Response({
            'framework': framework.name,
            'framework_id': str(framework.id),
            'total_controls': framework.controls.count(),
            'evidence_created': evidence_created,
            'evidence_skipped': evidence_skipped,
            'errors': errors[:10] if errors else [],
            'period_days': days,
            'period_start': period_start.isoformat(),
            'period_end': now.isoformat(),
        })
    
    
    @action(detail=False, methods=['get'])
    def evidence(self, request):
        """Get evidence for a specific control"""
        control_id = request.query_params.get('control_id')
        framework = request.query_params.get('framework', 'SOC2')
        
        queryset = ComplianceEvidence.objects.filter(
            organization=request.user.organization
        )
        
        if control_id:
            queryset = queryset.filter(control__control_id=control_id)
        if framework:
            queryset = queryset.filter(control__framework__name__iexact=framework)
        
        return Response([{
            'id': str(e.id),
            'control_id': e.control.control_id,
            'control_title': e.control.title,
            'framework': e.control.framework.name,
            'evidence_type': e.evidence_type,
            'description': e.description,
            'data': e.data,
            'collected_at': e.collected_at.isoformat(),
            'period': {'start': e.period_start.isoformat(), 'end': e.period_end.isoformat()},
        } for e in queryset.order_by('-collected_at')[:100]])
    
    @action(detail=False, methods=['post'])
    def import_frameworks(self, request):
        """Import compliance frameworks"""
        import_compliance_data()
        return Response({'status': 'imported'})
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Generate compliance report"""
        framework_name = request.query_params.get('framework', 'SOC2')
        
        try:
            framework = ComplianceFramework.objects.get(name__iexact=framework_name)
        except ComplianceFramework.DoesNotExist:
            return Response({'error': 'Framework not found'}, status=404)
        
        org = request.user.organization
        report = {
            'framework': framework.name,
            'generated_at': timezone.now().isoformat(),
            'organization': org.name if org else 'N/A',
            'controls': [],
            'summary': {'total': 0, 'compliant': 0, 'non_compliant': 0},
        }
        
        for control in framework.controls.all():
            evidence = ComplianceEvidence.objects.filter(
                control=control, organization=org
            ).order_by('-collected_at')
            
            is_compliant = evidence.exists()
            report['summary']['total'] += 1
            if is_compliant:
                report['summary']['compliant'] += 1
            else:
                report['summary']['non_compliant'] += 1
            
            report['controls'].append({
                'control_id': control.control_id,
                'title': control.title,
                'category': control.category,
                'compliant': is_compliant,
                'evidence_count': evidence.count(),
                'latest_evidence': evidence.first().description if evidence.exists() else 'No evidence',
            })
        
        report['summary']['compliance_pct'] = round(
            report['summary']['compliant'] / report['summary']['total'] * 100, 1
        ) if report['summary']['total'] > 0 else 0
        
        return Response(report)