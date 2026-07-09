# apps/events/views.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum, Max
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Event
from .serializers import EventSerializer, EventListSerializer

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing events"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def get_queryset(self):
        queryset = Event.objects.select_related('agent', 'raw_log')
        
        # Filter by organization
        if self.request.user.organization:
            queryset = queryset.filter(
                agent__organization=self.request.user.organization
            )
        
        # Apply filters
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        source_ip = self.request.query_params.get('source_ip')
        if source_ip:
            queryset = queryset.filter(source_ip=source_ip)
        
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username=username)
        
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent__agent_id=agent_id)
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) |
                Q(source_ip__icontains=search) |
                Q(username__icontains=search)
            )
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get event statistics"""
        organization = request.user.organization
        
        queryset = Event.objects.all()
        if organization:
            queryset = queryset.filter(agent__organization=organization)
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        stats = {
            'total_events': queryset.count(),
            'events_last_24h': queryset.filter(timestamp__gte=last_24h).count(),
            
            'by_severity': list(
                queryset.filter(timestamp__gte=last_24h)
                .values('severity')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            
            'by_type': list(
                queryset.filter(timestamp__gte=last_24h)
                .values('event_type')
                .annotate(count=Count('id'))
                .order_by('-count')[:20]
            ),
            
            'top_source_ips': list(
                queryset.filter(
                    timestamp__gte=last_24h,
                    source_ip__isnull=False
                )
                .values('source_ip')
                .annotate(count=Count('id'))
                .order_by('-count')[:20]
            ),
            
            'top_usernames': list(
                queryset.filter(
                    timestamp__gte=last_24h,
                    username__isnull=False
                )
                .values('username')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def top_ips(self, request):
        """Get top attacking/active IPs"""
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 20))
        
        since = timezone.now() - timedelta(hours=hours)
        
        queryset = Event.objects.filter(
            timestamp__gte=since,
            source_ip__isnull=False
        )
        
        if request.user.organization:
            queryset = queryset.filter(
                agent__organization=request.user.organization
            )
        
        top_ips = queryset.values('source_ip').annotate(
            count=Count('id'),
            last_seen=Max('timestamp')
        ).order_by('-count')[:limit]
        
        return Response(list(top_ips))
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get event timeline for visualization"""
        hours = int(request.query_params.get('hours', 24))
        interval = request.query_params.get('interval', 'hour')  # hour, minute
        
        since = timezone.now() - timedelta(hours=hours)
        
        queryset = Event.objects.filter(timestamp__gte=since)
        if request.user.organization:
            queryset = queryset.filter(
                agent__organization=request.user.organization
            )
        
        # Group by interval
        from django.db.models.functions import TruncHour, TruncMinute
        
        if interval == 'minute':
            timeline = queryset.annotate(
                period=TruncMinute('timestamp')
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
        else:
            timeline = queryset.annotate(
                period=TruncHour('timestamp')
            ).values('period').annotate(
                count=Count('id')
            ).order_by('period')
        
        return Response(list(timeline))