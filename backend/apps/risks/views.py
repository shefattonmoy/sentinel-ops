from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
from .models import AssetRiskScore
from .scoring import RiskScoringEngine

class RiskViewSet(viewsets.ViewSet):
    """Risk Scoring API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def assets(self, request):
        """Get risk scores for all assets"""
        engine = RiskScoringEngine()
        risks = engine.get_all_asset_risks(request.user.organization)
        return Response(risks)
    
    @action(detail=False, methods=['post'])
    def score_asset(self, request):
        """Score a specific asset"""
        hostname = request.data.get('hostname', '')
        ip = request.data.get('ip')
        
        if not hostname:
            return Response({'error': 'Hostname required'}, status=400)
        
        engine = RiskScoringEngine()
        score = engine.calculate_asset_risk(hostname, ip)
        return Response(score)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Risk dashboard summary"""
        org = request.user.organization
        
        scores = AssetRiskScore.objects.filter(organization=org)
        
        return Response({
            'total_assets': scores.count(),
            'high_risk': scores.filter(overall_risk__gte=70).count(),
            'medium_risk': scores.filter(overall_risk__gte=40, overall_risk__lt=70).count(),
            'low_risk': scores.filter(overall_risk__lt=40).count(),
            'avg_risk': scores.aggregate(avg=Avg('overall_risk'))['avg'] or 0,
            'highest_risk': scores.order_by('-overall_risk').first().overall_risk if scores.exists() else 0,
            'top_risks': list(scores.order_by('-overall_risk')[:5].values('asset_name', 'hostname', 'overall_risk', 'threat_risk')),
            'trend': [],  # Would store historical scores
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get risk score history for an asset"""
        hostname = request.query_params.get('hostname')
        if not hostname:
            return Response({'error': 'Hostname required'}, status=400)
        
        # Return historical scores (simplified - would come from time-series DB)
        engine = RiskScoringEngine()
        current = engine.calculate_asset_risk(hostname)
        
        return Response({
            'hostname': hostname,
            'current': current,
            'history': [current],
        })