# apps/topology/models.py
import uuid
from django.db import models

class NetworkNode(models.Model):
    """A node in the network topology"""
    
    NODE_TYPES = [
        ('server', 'Server'),
        ('container', 'Container'),
        ('service', 'Service'),
        ('database', 'Database'),
        ('load_balancer', 'Load Balancer'),
        ('firewall', 'Firewall'),
        ('external', 'External'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES)
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Position on the map (for manual adjustment)
    x_position = models.FloatField(default=0)
    y_position = models.FloatField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='online')
    
    # Metrics
    cpu_usage = models.FloatField(null=True)
    memory_usage = models.FloatField(null=True)
    connection_count = models.IntegerField(default=0)
    alert_count = models.IntegerField(default=0)
    risk_score = models.FloatField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    labels = models.JSONField(default=list)
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    agent = models.ForeignKey('agents.Agent', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['node_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.node_type})"


class NetworkEdge(models.Model):
    """Connection between two nodes"""
    
    EDGE_TYPES = [
        ('http', 'HTTP/HTTPS'),
        ('ssh', 'SSH'),
        ('database', 'Database'),
        ('api', 'API'),
        ('proxy', 'Proxy'),
        ('dns', 'DNS'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='incoming_edges')
    
    edge_type = models.CharField(max_length=50, choices=EDGE_TYPES, default='unknown')
    protocol = models.CharField(max_length=20, blank=True)
    port = models.IntegerField(null=True)
    
    # Traffic metrics
    bytes_transferred = models.BigIntegerField(default=0)
    request_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    latency_ms = models.FloatField(null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='healthy')  # healthy, degraded, down
    
    # Timestamps
    first_seen = models.DateTimeField(null=True)
    last_seen = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ['source', 'target', 'port']
    
    def __str__(self):
        return f"{self.source.name} → {self.target.name} ({self.edge_type})"


class NetworkScan(models.Model):
    """Network discovery scan results"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    status = models.CharField(max_length=20, default='running')
    nodes_found = models.IntegerField(default=0)
    edges_found = models.IntegerField(default=0)
    
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, null=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-started_at']