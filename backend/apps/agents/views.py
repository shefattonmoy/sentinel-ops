# apps/agents/views.py
import uuid
import hashlib
import secrets
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from .models import Agent, AgentHeartbeat, AgentConfiguration, AgentGroup
from apps.audit.models import log_action
from .serializers import (
    AgentSerializer,
    AgentRegistrationSerializer,
    AgentRegistrationResponseSerializer,
    AgentUpdateSerializer,
    AgentConfigurationSerializer,
    AgentGroupSerializer,
    AgentStatsSerializer,
    HeartbeatSerializer,
    AgentHeartbeatSerializer,
)


def generate_token():
    """Generate a secure token for agent authentication"""
    return secrets.token_hex(32)


def generate_agent_id():
    """Generate a unique agent ID"""
    return f"agent-{uuid.uuid4().hex[:12]}"


class AgentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing agents"""

    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "agent_id"

    def get_queryset(self):
        queryset = Agent.objects.filter(is_deleted=False).select_related(
            "configuration"
        )

        # Filter by organization if user has one
        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by agent type
        agent_type = self.request.query_params.get("agent_type")
        if agent_type:
            queryset = queryset.filter(agent_type=agent_type)

        # Search by name or hostname
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(hostname__icontains=search)
                | Q(agent_id__icontains=search)
            )

        # Filter by tags
        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        return queryset.order_by("-last_heartbeat")

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.deactivated_at = timezone.now()
        instance.save()
        
        log_action(
            user=self.request.user,
            action='AGENT_DELETE',
            description=f'Agent {instance.name} ({instance.hostname}) deleted',
            obj=instance,
            severity='warning',
            request=self.request,
        )
    
    @action(detail=True, methods=["get"])
    def heartbeats(self, request, agent_id=None):
        """Get agent heartbeat history"""
        agent = self.get_object()
        limit = request.query_params.get("limit", 100)

        heartbeats = agent.heartbeats.all()[: int(limit)]
        serializer = AgentHeartbeatSerializer(heartbeats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, agent_id=None):
        """Get agent statistics"""
        agent = self.get_object()

        last_24h = timezone.now() - timedelta(hours=24)

        stats = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "hostname": agent.hostname,
            "status": agent.status,
            "is_online": agent.is_online(),
            "uptime": agent.get_uptime(),
            "total_logs_collected": agent.total_logs_collected,
            "total_events_generated": agent.total_events_generated,
            "total_alerts_triggered": agent.total_alerts_triggered,
            "heartbeats_last_24h": agent.heartbeats.filter(
                timestamp__gte=last_24h
            ).count(),
            "logs_last_24h": agent.raw_logs.filter(created_at__gte=last_24h).count(),
            "events_last_24h": agent.events.filter(created_at__gte=last_24h).count(),
        }

        return Response(stats)

    @action(detail=True, methods=["post"])
    def update_config(self, request, agent_id=None):
        """Update agent configuration"""
        agent = self.get_object()

        config, created = AgentConfiguration.objects.get_or_create(agent=agent)
        serializer = AgentConfigurationSerializer(
            config, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def restart(self, request, agent_id=None):
        """Request agent restart"""
        agent = self.get_object()
        # This would send a restart command to the agent
        # For now, just record the request
        agent.tags.append(f"restart_requested_{timezone.now().isoformat()}")
        agent.save()

        return Response(
            {
                "message": f"Restart command queued for agent {agent.name}",
                "agent_id": agent.agent_id,
            }
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_agent(request):
    """
    Register a new agent.
    This endpoint is called by the agent when it starts for the first time.
    """
    serializer = AgentRegistrationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    # Check if agent with this hostname already exists
    existing_agent = Agent.objects.filter(
        hostname=validated_data["hostname"], is_deleted=False
    ).first()

    if existing_agent:
        # Return existing agent credentials
        return Response(
            {
                "agent_id": existing_agent.agent_id,
                "token": existing_agent.token,
                "status": "existing",
                "message": "Agent already registered",
                "server_url": request.build_absolute_uri("/")[:-1],
                "config": (
                    existing_agent.config if hasattr(existing_agent, "config") else {}
                ),
            }
        )

    # Create new agent
    agent = Agent.objects.create(
        agent_id=generate_agent_id(),
        name=validated_data["name"],
        hostname=validated_data["hostname"],
        version=validated_data.get("version", "1.0.0"),
        agent_type=validated_data.get("agent_type", "linux"),
        token=generate_token(),
        os_info=validated_data.get("os_info", {}),
        ip_address=validated_data.get("ip_address"),
        mac_address=validated_data.get("mac_address"),
        monitored_logs=validated_data.get("monitored_logs", []),
        tags=validated_data.get("tags", []),
        organization_id=request.data.get("organization_id"),
    )

    log_action(
        user=None,
        action="AGENT_REGISTER",
        description=f"Agent {agent.name} ({agent.hostname}) registered",
        obj=agent,
        severity="info",
        request=request,
    )

    # Create default configuration
    AgentConfiguration.objects.create(agent=agent)

    return Response(
        {
            "agent_id": agent.agent_id,
            "token": agent.token,
            "status": "registered",
            "message": f"Agent {agent.name} registered successfully",
            "server_url": request.build_absolute_uri("/")[:-1],
            "config": {
                "heartbeat_interval": agent.heartbeat_interval,
                "log_batch_size": 100,
                "max_buffer_size": 10000,
                "max_retries": 5,
                "retry_delay": 5,
                "retry_backoff": 2.0,
                "collect_metrics": True,
                "metrics_interval": 60,
                "monitored_logs": agent.monitored_logs,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def agent_heartbeat(request):
    """
    Receive heartbeat from agent.
    This is called every heartbeat_interval seconds by the agent.
    """
    # Authenticate agent via token
    token = (
        request.headers.get("Authorization", "")
        .replace("Token ", "")
        .replace("Bearer ", "")
    )

    if not token:
        # Also check request body for token
        token = request.data.get("token")

    if not token:
        return Response(
            {"error": "Authentication token required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        agent = Agent.objects.select_related("configuration").get(
            token=token, is_active=True
        )
    except Agent.DoesNotExist:
        return Response(
            {"error": "Invalid agent token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # Update agent status
    agent.last_heartbeat = timezone.now()
    agent.status = "online"
    agent.missed_heartbeats = 0

    # Update metrics if provided
    metrics = request.data.get("metrics", {})

    if metrics:
        agent.cpu_usage = metrics.get("cpu_usage")
        agent.memory_usage = metrics.get("memory_usage")
        agent.disk_usage = metrics.get("disk_usage")
        agent.network_status = metrics.get("network_status", "healthy")

    agent.save()

    # Create detailed heartbeat record
    heartbeat = AgentHeartbeat.objects.create(
        agent=agent,
        cpu_usage=metrics.get("cpu_usage"),
        cpu_cores=metrics.get("cpu_cores"),
        cpu_model=metrics.get("cpu_model"),
        memory_usage=metrics.get("memory_usage"),
        memory_total=metrics.get("memory_total"),
        memory_used=metrics.get("memory_used"),
        memory_free=metrics.get("memory_free"),
        disk_usage=metrics.get("disk_usage"),
        disk_total=metrics.get("disk_total"),
        disk_used=metrics.get("disk_used"),
        disk_free=metrics.get("disk_free"),
        disk_partitions=metrics.get("disk_partitions", []),
        network_io=metrics.get("network_io", {}),
        network_interfaces=metrics.get("network_interfaces", []),
        network_connections=metrics.get("network_connections"),
        process_count=metrics.get("process_count"),
        zombie_processes=metrics.get("zombie_processes"),
        uptime=metrics.get("uptime"),
        load_average=metrics.get("load_average", {}),
        boot_time=metrics.get("boot_time"),
        buffer_size=metrics.get("buffer_size"),
        logs_collected=metrics.get("logs_collected", 0),
        events_generated=metrics.get("events_generated", 0),
        errors_encountered=metrics.get("errors_encountered", 0),
    )

    # Update agent statistics
    agent.total_logs_collected += metrics.get("logs_collected", 0)
    agent.total_events_generated += metrics.get("events_generated", 0)
    agent.save(update_fields=["total_logs_collected", "total_events_generated"])

    # Check thresholds and generate alerts if needed
    check_agent_health(agent, metrics)

    return Response(
        {
            "status": "ok",
            "message": "Heartbeat received",
            "server_time": timezone.now().isoformat(),
            "agent_id": agent.agent_id,
            "next_heartbeat_in": agent.heartbeat_interval,
        }
    )


def check_agent_health(agent, metrics):
    """Check agent health and generate alerts if thresholds exceeded"""
    alerts = []

    # Check CPU threshold
    cpu_usage = metrics.get("cpu_usage", 0)
    if cpu_usage and cpu_usage > 90:
        alerts.append(f"High CPU usage: {cpu_usage}%")

    # Check memory threshold
    memory_usage = metrics.get("memory_usage", 0)
    if memory_usage and memory_usage > 90:
        alerts.append(f"High memory usage: {memory_usage}%")

    # Check disk threshold
    disk_usage = metrics.get("disk_usage", 0)
    if disk_usage and disk_usage > 90:
        alerts.append(f"High disk usage: {disk_usage}%")

    # Check for zombie processes
    zombie_processes = metrics.get("zombie_processes", 0)
    if zombie_processes and zombie_processes > 10:
        alerts.append(f"High zombie process count: {zombie_processes}")

    if alerts:
        agent.record_error("; ".join(alerts))

        # Create alert if configured (this would call the alerts app)
        # create_agent_alert(agent, alerts)


@api_view(["POST"])
@permission_classes([AllowAny])
def agent_error_report(request):
    """
    Report agent errors.
    """
    token = (
        request.headers.get("Authorization", "")
        .replace("Token ", "")
        .replace("Bearer ", "")
    )

    try:
        agent = Agent.objects.get(token=token, is_active=True)
    except Agent.DoesNotExist:
        return Response(
            {"error": "Invalid agent token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    error_message = request.data.get("error", "Unknown error")
    agent.record_error(error_message)

    return Response(
        {"status": "ok", "message": "Error reported", "agent_id": agent.agent_id}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agent_stats(request):
    """
    Get overall agent statistics.
    """
    organization = request.user.organization

    agents = Agent.objects.filter(is_deleted=False)
    if organization:
        agents = agents.filter(organization=organization)

    total = agents.count()
    online = agents.filter(status="online").count()
    offline = agents.filter(status="offline").count()
    degraded = agents.filter(status="degraded").count()
    error = agents.filter(status="error").count()

    stats = {
        "total_agents": total,
        "online_agents": online,
        "offline_agents": offline,
        "degraded_agents": degraded,
        "error_agents": error,
        "total_logs_collected": agents.aggregate(total=Sum("total_logs_collected"))[
            "total"
        ]
        or 0,
        "total_events_generated": agents.aggregate(total=Sum("total_events_generated"))[
            "total"
        ]
        or 0,
        "total_alerts_triggered": agents.aggregate(total=Sum("total_alerts_triggered"))[
            "total"
        ]
        or 0,
        "avg_cpu_usage": agents.filter(cpu_usage__isnull=False).aggregate(
            avg=Avg("cpu_usage")
        )["avg"]
        or 0,
        "avg_memory_usage": agents.filter(memory_usage__isnull=False).aggregate(
            avg=Avg("memory_usage")
        )["avg"]
        or 0,
        "avg_disk_usage": agents.filter(disk_usage__isnull=False).aggregate(
            avg=Avg("disk_usage")
        )["avg"]
        or 0,
    }

    return Response(stats)


class AgentGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing agent groups"""

    serializer_class = AgentGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AgentGroup.objects.prefetch_related("agents")
        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)
        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    @action(detail=True, methods=["post"])
    def add_agents(self, request, pk=None):
        """Add agents to group"""
        group = self.get_object()
        agent_ids = request.data.get("agent_ids", [])

        agents = Agent.objects.filter(agent_id__in=agent_ids)
        group.agents.add(*agents)

        return Response(
            {
                "message": f"Added {len(agent_ids)} agents to group",
                "agent_count": group.agents.count(),
            }
        )

    @action(detail=True, methods=["post"])
    def remove_agents(self, request, pk=None):
        """Remove agents from group"""
        group = self.get_object()
        agent_ids = request.data.get("agent_ids", [])

        agents = Agent.objects.filter(agent_id__in=agent_ids)
        group.agents.remove(*agents)

        return Response(
            {
                "message": f"Removed {len(agent_ids)} agents from group",
                "agent_count": group.agents.count(),
            }
        )
