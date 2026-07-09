# apps/logs/views.py
import time
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum, Max
from django.db import transaction
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.agents.models import Agent
from .models import RawLog, LogBatch
from .serializers import (
    RawLogSerializer,
    LogIngestionSerializer,
    LogBatchSerializer,
    LogSearchSerializer,
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class RawLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing raw logs"""
    serializer_class = RawLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = RawLog.objects.select_related('agent')
        
        # Filter by organization
        if self.request.user.organization:
            queryset = queryset.filter(
                agent__organization=self.request.user.organization
            )
        
        # Filter by agent
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent__agent_id=agent_id)
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by log level
        log_level = self.request.query_params.get('log_level')
        if log_level:
            queryset = queryset.filter(log_level=log_level.upper())
        
        # Filter by parsing status
        is_parsed = self.request.query_params.get('is_parsed')
        if is_parsed is not None:
            queryset = queryset.filter(is_parsed=is_parsed.lower() == 'true')
        
        # Date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(raw_message__icontains=search)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get log statistics"""
        organization = request.user.organization
        
        queryset = RawLog.objects.all()
        if organization:
            queryset = queryset.filter(agent__organization=organization)
        
        # Time ranges
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            'total_logs': queryset.count(),
            'logs_last_hour': queryset.filter(timestamp__gte=last_hour).count(),
            'logs_last_24h': queryset.filter(timestamp__gte=last_24h).count(),
            'logs_last_7d': queryset.filter(timestamp__gte=last_7d).count(),
            
            # By source
            'logs_by_source': list(
                queryset.values('source').annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
            ),
            
            # By log level
            'logs_by_level': list(
                queryset.values('log_level').annotate(
                    count=Count('id')
                ).order_by('-count')
            ),
            
            # By agent
            'logs_by_agent': list(
                queryset.values(
                    'agent__name', 'agent__hostname'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
            ),
            
            # Parsing status
            'parsed_logs': queryset.filter(is_parsed=True).count(),
            'unparsed_logs': queryset.filter(is_parsed=False).count(),
            
            # Hourly breakdown for last 24h
            'hourly_breakdown': self._get_hourly_breakdown(queryset, last_24h),
        }
        
        return Response(stats)
    
    def _get_hourly_breakdown(self, queryset, since):
        """Get hourly log counts for the last 24 hours"""
        breakdown = []
        for i in range(24):
            hour_start = since + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            count = queryset.filter(
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            ).count()
            breakdown.append({
                'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                'count': count
            })
        return breakdown
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced log search"""
        serializer = LogSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        data = serializer.validated_data
        
        queryset = RawLog.objects.all()
        if request.user.organization:
            queryset = queryset.filter(
                agent__organization=request.user.organization
            )
        
        # Apply filters
        if data.get('query'):
            queryset = queryset.filter(
                Q(raw_message__icontains=data['query']) |
                Q(source__icontains=data['query']) |
                Q(hostname__icontains=data['query'])
            )
        
        if data.get('sources'):
            queryset = queryset.filter(source__in=data['sources'])
        
        if data.get('log_levels'):
            queryset = queryset.filter(log_level__in=data['log_levels'])
        
        if data.get('agent_ids'):
            queryset = queryset.filter(agent__agent_id__in=data['agent_ids'])
        
        if data.get('date_from'):
            queryset = queryset.filter(timestamp__gte=data['date_from'])
        
        if data.get('date_to'):
            queryset = queryset.filter(timestamp__lte=data['date_to'])
        
        # Paginate
        page = data.get('page', 1)
        page_size = data.get('page_size', 50)
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        logs = queryset[start:end]
        
        serializer = RawLogSerializer(logs, many=True)
        
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': serializer.data
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def ingest_logs(request):
    """
    Main log ingestion endpoint.
    Receives logs from agents, validates, stores, and queues for processing.
    """
    start_time = time.time()
    
    # Authenticate agent via token
    token = request.headers.get('Authorization', '').replace('Token ', '').replace('Bearer ', '')
    
    if not token:
        return Response(
            {'error': 'Authentication token required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        agent = Agent.objects.get(token=token, is_active=True)
    except Agent.DoesNotExist:
        return Response(
            {'error': 'Invalid or inactive agent token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request data
    serializer = LogIngestionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    logs = validated_data['logs']
    hostname = validated_data.get('hostname', agent.hostname)
    
    # Create log batch record
    batch = LogBatch.objects.create(
        agent=agent,
        batch_size=len(logs),
        status='processing'
    )
    
    # Process logs in bulk
    raw_logs = []
    duplicates = 0
    
    try:
        with transaction.atomic():
            for log_entry in logs:
                # Generate hash for deduplication
                content = f"{agent.id}:{log_entry['source']}:{log_entry.get('timestamp')}:{log_entry['message']}"
                log_hash = hashlib.sha256(content.encode()).hexdigest()
                
                # Check for duplicates (last 1 hour)
                if RawLog.objects.filter(
                    log_hash=log_hash,
                    created_at__gte=timezone.now() - timedelta(hours=1)
                ).exists():
                    duplicates += 1
                    continue
                
                # Parse timestamp
                timestamp = log_entry.get('timestamp')
                if timestamp:
                    try:
                        from dateutil.parser import parse
                        timestamp = parse(timestamp)
                    except:
                        timestamp = timezone.now()
                else:
                    timestamp = timezone.now()
                
                raw_log = RawLog(
                    agent=agent,
                    timestamp=timestamp,
                    source=log_entry.get('source', 'unknown'),
                    log_level=log_entry.get('level', 'INFO').upper(),
                    raw_message=log_entry['message'],
                    file_path=log_entry.get('path'),
                    hostname=hostname,
                    service=log_entry.get('service'),
                    log_hash=log_hash,
                )
                raw_logs.append(raw_log)
            
            # Bulk create logs
            if raw_logs:
                RawLog.objects.bulk_create(raw_logs)
        
        # Update batch status
        processing_time = time.time() - start_time
        
        batch.status = 'completed'
        batch.logs_processed = len(raw_logs)
        batch.processing_time = processing_time
        batch.completed_at = timezone.now()
        batch.save()
        
        # Update agent statistics
        agent.total_logs_collected += len(raw_logs)
        agent.last_heartbeat = timezone.now()
        agent.status = 'online'
        agent.save(update_fields=['total_logs_collected', 'last_heartbeat', 'status'])
        
        # Queue logs for parsing (async)
        from .tasks import parse_logs_async
        log_ids = [str(log.id) for log in raw_logs]
        parse_logs_async.delay(log_ids, str(agent.agent_id))
        
        return Response({
            'status': 'success',
            'message': f'Ingested {len(raw_logs)} logs',
            'logs_received': len(logs),
            'logs_ingested': len(raw_logs),
            'duplicates_skipped': duplicates,
            'processing_time_ms': round(processing_time * 1000, 2),
            'batch_id': str(batch.id)
        })
        
    except Exception as e:
        # Update batch with error
        batch.status = 'failed'
        batch.error_details = {'error': str(e)}
        batch.completed_at = timezone.now()
        batch.save()
        
        return Response(
            {'error': f'Ingestion failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def log_sources(request):
    """Get available log sources with counts"""
    organization = request.user.organization
    
    queryset = RawLog.objects.all()
    if organization:
        queryset = queryset.filter(agent__organization=organization)
    
    sources = queryset.values('source').annotate(
        count=Count('id'),
        last_seen=Max('timestamp')
    ).order_by('-count')
    
    return Response(list(sources))


class LogBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log batches"""
    serializer_class = LogBatchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = LogBatch.objects.select_related('agent')
        if self.request.user.organization:
            queryset = queryset.filter(
                agent__organization=self.request.user.organization
            )
        return queryset.order_by('-created_at')