from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import Honeypot, HoneypotInteraction

class HoneypotViewSet(viewsets.ViewSet):
    """Honeypot Management API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def honeypots(self, request):
        """List all honeypots"""
        honeypots = Honeypot.objects.filter(organization=request.user.organization)
        return Response([{
            'id': str(h.id),
            'name': h.name,
            'protocol': h.protocol,
            'port': h.port,
            'host': h.host,
            'is_active': h.is_active,
            'interaction_count': h.interactions.count(),
            'last_interaction': h.interactions.order_by('-timestamp').first().timestamp.isoformat() if h.interactions.exists() else None,
        } for h in honeypots])
    
    @action(detail=False, methods=['post'])
    def create_honeypot(self, request):
        """Create a new honeypot"""
        honeypot = Honeypot.objects.create(
            name=request.data.get('name', 'New Honeypot'),
            protocol=request.data.get('protocol', 'ssh'),
            port=request.data.get('port', 2222),
            host=request.data.get('host', '0.0.0.0'),
            organization=request.user.organization,
        )
        return Response({
            'id': str(honeypot.id),
            'name': honeypot.name,
            'protocol': honeypot.protocol,
            'port': honeypot.port,
        }, status=201)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle honeypot active status"""
        honeypot_id = request.data.get('id')
        try:
            honeypot = Honeypot.objects.get(id=honeypot_id)
            honeypot.is_active = not honeypot.is_active
            honeypot.save()
            return Response({'status': 'ok', 'is_active': honeypot.is_active})
        except Honeypot.DoesNotExist:
            return Response({'error': 'Honeypot not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def interactions(self, request):
        """Get recent honeypot interactions"""
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 100))
        ip = request.query_params.get('ip')
        
        since = timezone.now() - timedelta(hours=hours)
        
        interactions = HoneypotInteraction.objects.filter(
            timestamp__gte=since
        ).select_related('honeypot')
        
        if request.user.organization:
            interactions = interactions.filter(honeypot__organization=request.user.organization)
        if ip:
            interactions = interactions.filter(source_ip=ip)
        
        interactions = interactions.order_by('-timestamp')[:limit]
        
        return Response([{
            'id': str(i.id),
            'honeypot_name': i.honeypot.name,
            'protocol': i.honeypot.protocol,
            'port': i.honeypot.port,
            'source_ip': i.source_ip,
            'source_port': i.source_port,
            'interaction_type': i.interaction_type,
            'payload': i.payload[:500] if i.payload else '',
            'threat_level': i.threat_level,
            'is_malicious': i.is_malicious,
            'timestamp': i.timestamp.isoformat(),
        } for i in interactions])
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get honeypot statistics"""
        org = request.user.organization
        since_24h = timezone.now() - timedelta(hours=24)
        since_7d = timezone.now() - timedelta(days=7)
        
        interactions = HoneypotInteraction.objects.filter(honeypot__organization=org)
        
        return Response({
            'total_honeypots': Honeypot.objects.filter(organization=org).count(),
            'active_honeypots': Honeypot.objects.filter(organization=org, is_active=True).count(),
            'interactions_24h': interactions.filter(timestamp__gte=since_24h).count(),
            'interactions_7d': interactions.filter(timestamp__gte=since_7d).count(),
            'unique_ips_24h': interactions.filter(timestamp__gte=since_24h).values('source_ip').distinct().count(),
            'top_ips': list(interactions.filter(timestamp__gte=since_7d).values('source_ip').annotate(
                count=Count('id')
            ).order_by('-count')[:10]),
            'by_protocol': list(interactions.filter(timestamp__gte=since_7d).values('honeypot__protocol').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_type': list(interactions.filter(timestamp__gte=since_7d).values('interaction_type').annotate(
                count=Count('id')
            ).order_by('-count')),
        })
    
    @action(detail=False, methods=['post'])
    def log_interaction(self, request):
        """Log a honeypot interaction (called by honeypot agent)"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Simple token validation (would use proper auth)
        if not token:
            return Response({'error': 'Token required'}, status=401)
        
        interaction = HoneypotInteraction.objects.create(
            honeypot_id=request.data.get('honeypot_id'),
            source_ip=request.data.get('source_ip', '0.0.0.0'),
            source_port=request.data.get('source_port'),
            interaction_type=request.data.get('interaction_type', 'connection'),
            payload=request.data.get('payload', ''),
            headers=request.data.get('headers', {}),
            threat_level=request.data.get('threat_level', 'high'),
        )
        
        return Response({'id': str(interaction.id), 'status': 'logged'}, status=201)