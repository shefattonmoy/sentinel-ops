from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import MitreTechnique, EventTechniqueMapping, MitreCoverage
from .importer import import_mitre_data, import_event_mappings

class MitreViewSet(viewsets.ViewSet):
    """MITRE ATT&CK Framework API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def techniques(self, request):
        """Get all MITRE techniques with coverage status"""
        org = request.user.organization
        tactic = request.query_params.get('tactic')
        
        techniques = MitreTechnique.objects.all()
        if tactic:
            techniques = techniques.filter(tactic__iexact=tactic)
        
        data = []
        for tech in techniques:
            coverage = MitreCoverage.objects.filter(
                technique=tech, organization=org
            ).first()
            
            data.append({
                'technique_id': tech.technique_id,
                'name': tech.name,
                'tactic': tech.tactic,
                'platform': tech.platform,
                'description': tech.description[:300],
                'is_covered': coverage.is_covered if coverage else False,
                'detected_events': coverage.detected_events if coverage else 0,
                'last_detected': coverage.last_detected.isoformat() if coverage and coverage.last_detected else None,
            })
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def matrix(self, request):
        """Get ATT&CK matrix grouped by tactic"""
        org = request.user.organization
        techniques = MitreTechnique.objects.all()
        
        matrix = {}
        for tech in techniques:
            tactic = tech.tactic or 'Unknown'
            if tactic not in matrix:
                matrix[tactic] = []
            
            coverage = MitreCoverage.objects.filter(
                technique=tech, organization=org, is_covered=True
            ).exists()
            
            matrix[tactic].append({
                'id': tech.technique_id,
                'name': tech.name,
                'covered': coverage,
            })
        
        # Calculate stats per tactic
        result = {}
        for tactic, techs in matrix.items():
            covered = sum(1 for t in techs if t['covered'])
            result[tactic] = {
                'total': len(techs),
                'covered': covered,
                'percentage': round(covered / len(techs) * 100, 1) if techs else 0,
                'techniques': techs,
            }
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def mappings(self, request):
        """Get event-to-MITRE mappings"""
        mappings = EventTechniqueMapping.objects.select_related('technique').all()
        return Response([{
            'event_type': m.event_type,
            'technique_id': m.technique.technique_id,
            'technique_name': m.technique.name,
            'tactic': m.technique.tactic,
            'confidence': m.confidence,
        } for m in mappings])
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get MITRE coverage statistics"""
        org = request.user.organization
        total = MitreTechnique.objects.count()
        covered = MitreCoverage.objects.filter(organization=org, is_covered=True).count()
        
        # By tactic
        by_tactic = MitreTechnique.objects.values('tactic').annotate(
            total=Count('id')
        )
        
        tactic_stats = []
        for item in by_tactic:
            covered_count = MitreCoverage.objects.filter(
                technique__tactic=item['tactic'],
                organization=org,
                is_covered=True
            ).count()
            tactic_stats.append({
                'tactic': item['tactic'],
                'total': item['total'],
                'covered': covered_count,
                'percentage': round(covered_count / item['total'] * 100, 1),
            })
        
        # Recent detections
        recent = MitreCoverage.objects.filter(
            organization=org, last_detected__isnull=False
        ).select_related('technique').order_by('-last_detected')[:10]
        
        return Response({
            'total_techniques': total,
            'covered_techniques': covered,
            'coverage_pct': round(covered / total * 100, 1) if total > 0 else 0,
            'by_tactic': tactic_stats,
            'recent_detections': [{
                'technique_id': r.technique.technique_id,
                'name': r.technique.name,
                'tactic': r.technique.tactic,
                'detected_events': r.detected_events,
                'last_detected': r.last_detected.isoformat() if r.last_detected else None,
            } for r in recent],
        })
    
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """Import/refresh MITRE ATT&CK data"""
        techniques = import_mitre_data()
        mappings = import_event_mappings()
        return Response({
            'techniques_imported': techniques,
            'mappings_created': mappings,
        })
    
    @action(detail=False, methods=['get'])
    def tactics(self, request):
        """Get list of all tactics"""
        tactics = MitreTechnique.objects.values_list('tactic', flat=True).distinct()
        return Response(sorted(list(tactics)))