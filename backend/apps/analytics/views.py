# apps/analytics/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from .models import UserBehaviorProfile, BehaviorAnomaly
from .analyzer import AnalyticsEngine

class AnalyticsViewSet(viewsets.ViewSet):
    """Analytics API - User Behavior & Anomaly Detection"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Get user behavior profiles"""
        profiles = UserBehaviorProfile.objects.all()
        if request.user.organization:
            profiles = profiles.filter(user__organization=request.user.organization)
        
        return Response([{
            'user': p.user.username,
            'anomaly_score': p.anomaly_score,
            'risk_level': p.risk_level,
            'sudo_frequency': round(p.sudo_frequency, 2),
            'total_events': p.total_events_analyzed,
            'common_ips': p.common_ips[:5],
            'last_analyzed': p.last_analyzed.isoformat() if p.last_analyzed else None,
        } for p in profiles.select_related('user')])
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Get detected anomalies"""
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 50))
        
        engine = AnalyticsEngine(request.user.organization)
        anomalies = engine.get_anomalies(hours)[:limit]
        
        return Response([{
            'id': str(a.id),
            'user': a.user.username,
            'type': a.anomaly_type,
            'description': a.description,
            'severity': a.severity,
            'confidence': a.confidence,
            'is_resolved': a.is_resolved,
            'detected_at': a.detected_at.isoformat(),
            'metadata': a.metadata,
        } for a in anomalies])
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Run behavior analysis on all users"""
        from apps.accounts.models import User
        
        engine = AnalyticsEngine(request.user.organization)
        users = User.objects.all()
        if request.user.organization:
            users = users.filter(organization=request.user.organization)
        
        analyzed = 0
        anomalies_found = 0
        for user in users:
            result = engine.analyze_user(user)
            if result:
                analyzed += 1
                if result.anomaly_score > 0:
                    anomalies_found += 1
        
        return Response({
            'users_analyzed': analyzed,
            'anomalies_found': anomalies_found,
            'total_anomalies': BehaviorAnomaly.objects.filter(is_resolved=False).count(),
        })
    
    @action(detail=False, methods=['post'])
    def resolve_anomaly(self, request):
        """Mark an anomaly as resolved"""
        anomaly_id = request.data.get('anomaly_id')
        try:
            anomaly = BehaviorAnomaly.objects.get(id=anomaly_id)
            anomaly.is_resolved = True
            anomaly.save()
            return Response({'status': 'resolved'})
        except BehaviorAnomaly.DoesNotExist:
            return Response({'error': 'Anomaly not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get analytics statistics"""
        org = request.user.organization
        
        profiles = UserBehaviorProfile.objects.all()
        anomalies = BehaviorAnomaly.objects.filter(is_resolved=False)
        
        if org:
            profiles = profiles.filter(user__organization=org)
            anomalies = anomalies.filter(user__organization=org)
        
        return Response({
            'total_profiles': profiles.count(),
            'high_risk_users': profiles.filter(risk_level='high').count(),
            'medium_risk_users': profiles.filter(risk_level='medium').count(),
            'total_anomalies': anomalies.count(),
            'recent_anomalies_24h': anomalies.filter(
                detected_at__gte=timezone.now()-timezone.timedelta(hours=24)
            ).count(),
            'top_anomaly_types': list(anomalies.values('anomaly_type').annotate(
                count=Count('id')
            ).order_by('-count')[:5]),
        })
    
    @action(detail=False, methods=['get'])
    def user_detail(self, request):
        """Get detailed analytics for a specific user"""
        username = request.query_params.get('username')
        if not username:
            return Response({'error': 'Username required'}, status=400)
        
        from apps.accounts.models import User
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        profile = UserBehaviorProfile.objects.filter(user=user).first()
        anomalies = BehaviorAnomaly.objects.filter(user=user).order_by('-detected_at')[:20]
        
        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
                'role': user.role,
            },
            'profile': {
                'anomaly_score': profile.anomaly_score if profile else 0,
                'risk_level': profile.risk_level if profile else 'low',
                'sudo_frequency': profile.sudo_frequency if profile else 0,
                'common_ips': profile.common_ips[:10] if profile else [],
                'total_events': profile.total_events_analyzed if profile else 0,
            } if profile else None,
            'anomalies': [{
                'id': str(a.id),
                'type': a.anomaly_type,
                'description': a.description,
                'severity': a.severity,
                'confidence': a.confidence,
                'detected_at': a.detected_at.isoformat(),
            } for a in anomalies],
        })