from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import NetworkNode, NetworkEdge, NetworkScan
from .discovery import TopologyDiscovery

class TopologyViewSet(viewsets.ViewSet):
    """Network Topology API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def map(self, request):
        """Get network topology map data"""
        org = request.user.organization
        
        nodes = NetworkNode.objects.filter(organization=org, is_active=True)
        edges = NetworkEdge.objects.filter(source__organization=org, is_active=True)
        
        return Response({
            'nodes': [{
                'id': str(n.id),
                'name': n.name,
                'type': n.node_type,
                'hostname': n.hostname,
                'ip': n.ip_address,
                'status': n.status,
                'x': n.x_position,
                'y': n.y_position,
                'cpu_usage': n.cpu_usage,
                'memory_usage': n.memory_usage,
                'alert_count': n.alert_count,
                'risk_score': n.risk_score,
                'connection_count': n.connection_count,
                'metadata': n.metadata,
                'labels': n.labels,
            } for n in nodes],
            'edges': [{
                'id': str(e.id),
                'source': str(e.source_id),
                'target': str(e.target_id),
                'type': e.edge_type,
                'protocol': e.protocol,
                'port': e.port,
                'status': e.status,
                'request_count': e.request_count,
                'error_count': e.error_count,
                'latency_ms': e.latency_ms,
                'last_seen': e.last_seen.isoformat() if e.last_seen else None,
            } for e in edges],
        })
    
    @action(detail=False, methods=['post'])
    def discover(self, request):
        """Run network discovery"""
        discovery = TopologyDiscovery(request.user.organization)
        result = discovery.discover_topology()
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def update_position(self, request):
        """Update node position on map"""
        node_id = request.data.get('node_id')
        x = request.data.get('x')
        y = request.data.get('y')
        
        try:
            node = NetworkNode.objects.get(id=node_id)
            node.x_position = x
            node.y_position = y
            node.save(update_fields=['x_position', 'y_position'])
            return Response({'status': 'ok'})
        except NetworkNode.DoesNotExist:
            return Response({'error': 'Node not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get topology statistics"""
        org = request.user.organization
        
        nodes = NetworkNode.objects.filter(organization=org, is_active=True)
        edges = NetworkEdge.objects.filter(source__organization=org, is_active=True)
        
        last_scan = NetworkScan.objects.filter(
            organization=org, status='completed'
        ).first()
        
        return Response({
            'total_nodes': nodes.count(),
            'total_edges': edges.count(),
            'online_nodes': nodes.filter(status='online').count(),
            'offline_nodes': nodes.filter(status='offline').count(),
            'nodes_by_type': list(nodes.values('node_type').annotate(count=Count('id'))),
            'edges_by_type': list(edges.values('edge_type').annotate(count=Count('id'))),
            'healthy_edges': edges.filter(status='healthy').count(),
            'degraded_edges': edges.filter(status='degraded').count(),
            'down_edges': edges.filter(status='down').count(),
            'last_scan': last_scan.started_at.isoformat() if last_scan else None,
            'last_scan_nodes': last_scan.nodes_found if last_scan else 0,
        })
    
    @action(detail=False, methods=['get'])
    def node_detail(self, request):
        """Get detailed node information"""
        node_id = request.query_params.get('id')
        try:
            node = NetworkNode.objects.get(id=node_id)
            
            outgoing = NetworkEdge.objects.filter(source=node)[:20]
            incoming = NetworkEdge.objects.filter(target=node)[:20]
            
            from apps.events.models import Event
            recent_events = Event.objects.filter(
                Q(source_ip=node.ip_address) | Q(source_hostname=node.hostname)
            ).order_by('-timestamp')[:20]
            
            return Response({
                'node': {
                    'id': str(node.id), 'name': node.name, 'type': node.node_type,
                    'hostname': node.hostname, 'ip': node.ip_address,
                    'status': node.status, 'cpu_usage': node.cpu_usage,
                    'memory_usage': node.memory_usage, 'risk_score': node.risk_score,
                    'alert_count': node.alert_count, 'metadata': node.metadata,
                },
                'connections': {
                    'outgoing': [{'id': str(e.id), 'target': e.target.name, 'type': e.edge_type, 'port': e.port, 'status': e.status} for e in outgoing],
                    'incoming': [{'id': str(e.id), 'source': e.source.name, 'type': e.edge_type, 'port': e.port, 'status': e.status} for e in incoming],
                },
                'recent_events': [{
                    'id': str(e.id), 'event_type': e.event_type, 'severity': e.severity,
                    'message': e.message[:200], 'timestamp': e.timestamp.isoformat(),
                } for e in recent_events],
            })
        except NetworkNode.DoesNotExist:
            return Response({'error': 'Node not found'}, status=404)