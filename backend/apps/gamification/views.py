from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AnalystProfile, Badge, Leaderboard
from .engine import GamificationEngine
from django.utils import timezone
from django.db.models import Sum

class GamificationViewSet(viewsets.ViewSet):
    """Gamification API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user's gamification profile"""
        profile, _ = AnalystProfile.objects.get_or_create(user=request.user)
        return Response({
            'username': request.user.username,
            'total_points': profile.total_points,
            'weekly_points': profile.weekly_points,
            'level': profile.level,
            'title': profile.title,
            'alerts_resolved': profile.alerts_resolved,
            'incidents_closed': profile.incidents_closed,
            'threats_detected': profile.threats_detected,
            'achievements': profile.achievements,
        })
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get current leaderboard"""
        period = request.query_params.get('period', 'weekly')
        engine = GamificationEngine()
        
        # Get latest snapshot or generate new one
        leaderboard = Leaderboard.objects.filter(period=period).order_by('-created_at').first()
        
        if leaderboard and leaderboard.created_at.date() == timezone.now().date():
            rankings = leaderboard.rankings
        else:
            rankings = engine.generate_leaderboard(period)
        
        return Response({
            'period': period,
            'rankings': rankings,
        })
    
    @action(detail=False, methods=['get'])
    def badges(self, request):
        """Get all available badges"""
        badges = Badge.objects.all()
        profile, _ = AnalystProfile.objects.get_or_create(user=request.user)
        earned = profile.achievements or []
        
        return Response([{
            'name': b.name, 'description': b.description,
            'icon': b.icon, 'points': b.points,
            'earned': b.name in earned,
        } for b in badges])
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get gamification statistics"""
        profiles = AnalystProfile.objects.all()
        return Response({
            'total_analysts': profiles.count(),
            'total_points_awarded': profiles.aggregate(total=Sum('total_points'))['total'] or 0,
            'top_analyst': profiles.order_by('-total_points').first().user.username if profiles.exists() else None,
            'badges_awarded': sum(len(p.achievements or []) for p in profiles),
        })