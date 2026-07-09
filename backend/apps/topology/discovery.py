# apps/topology/discovery.py
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from collections import defaultdict
import socket
import logging

logger = logging.getLogger(__name__)


class TopologyDiscovery:
    """Auto-discover network topology from agent data"""

    def __init__(self, organization=None):
        self.organization = organization

    def discover_topology(self):
        """Discover network topology from existing data"""
        from apps.agents.models import Agent
        from apps.events.models import Event
        from .models import NetworkNode, NetworkEdge, NetworkScan

        scan = NetworkScan.objects.create(
            organization=self.organization, status="running"
        )

        agents = Agent.objects.filter(is_active=True)
        if self.organization:
            agents = agents.filter(organization=self.organization)

        # Step 1: Create nodes from agents
        nodes_created = 0
        for agent in agents:
            node, created = NetworkNode.objects.update_or_create(
                name=agent.name,
                organization=self.organization,
                defaults={
                    "node_type": self._determine_node_type(agent),
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "status": agent.status,
                    "cpu_usage": agent.cpu_usage,
                    "memory_usage": agent.memory_usage,
                    "agent": agent,
                    "metadata": {
                        "version": getattr(agent, "version", "1.0.0"),
                        "os_info": getattr(agent, "os_info", {}),
                        "tags": getattr(agent, "tags", []),
                    },
                },
            )
            if created:
                nodes_created += 1

        # Step 2: Discover edges from events (connection patterns)
        edges_created = 0
        since = timezone.now() - timedelta(days=7)

        connections = self._discover_connections(agents, since)

        for conn in connections:
            try:
                source = NetworkNode.objects.filter(
                    ip_address=conn["source_ip"]
                ).first()
                target = NetworkNode.objects.filter(
                    ip_address=conn["target_ip"]
                ).first()

                if not source:
                    # Create external source node
                    source, _ = NetworkNode.objects.get_or_create(
                        name=f"External-{conn['source_ip']}",
                        organization=self.organization,
                        defaults={
                            "node_type": "external",
                            "ip_address": conn["source_ip"],
                            "status": "online",
                        },
                    )

                if not target:
                    target = NetworkNode.objects.filter(
                        Q(ip_address=conn["target_ip"])
                        | Q(hostname=conn.get("target_hostname", ""))
                    ).first()

                if target and source.id != target.id:
                    edge, created = NetworkEdge.objects.update_or_create(
                        source=source,
                        target=target,
                        port=conn.get("port"),
                        defaults={
                            "edge_type": conn.get("type", "unknown"),
                            "protocol": conn.get("protocol", ""),
                            "request_count": conn.get("count", 0),
                            "last_seen": conn.get("last_seen"),
                            "first_seen": (
                                conn.get("first_seen")
                                if not (
                                    edge := NetworkEdge.objects.filter(
                                        source=source,
                                        target=target,
                                        port=conn.get("port"),
                                    ).first()
                                )
                                else None
                            ),
                        },
                    )
                    if created:
                        edges_created += 1
            except Exception as e:
                logger.error(f"Error creating edge: {e}")
                continue

        # Step 3: Auto-position nodes
        self._auto_position_nodes()

        # Update scan
        scan.status = "completed"
        scan.nodes_found = nodes_created
        scan.edges_found = edges_created
        scan.completed_at = timezone.now()
        scan.save()

        return {
            "scan_id": str(scan.id),
            "nodes_found": nodes_created,
            "edges_found": edges_created,
            "total_nodes": NetworkNode.objects.filter(
                organization=self.organization
            ).count(),
            "total_edges": NetworkEdge.objects.filter(
                source__organization=self.organization
            ).count(),
        }

    def _determine_node_type(self, agent):
        """Determine node type from agent data"""
        hostname = getattr(agent, "hostname", "").lower()
        agent_type = getattr(agent, "agent_type", "linux")
        tags = [t.lower() for t in (getattr(agent, "tags", []) or [])]

        if (
            "db" in hostname
            or "database" in hostname
            or "postgres" in hostname
            or "mysql" in hostname
        ):
            return "database"
        elif "lb" in hostname or "proxy" in hostname or "nginx" in hostname:
            return "load_balancer"
        elif "fw" in hostname or "firewall" in hostname:
            return "firewall"
        elif "docker" in agent_type or "container" in agent_type:
            return "container"
        elif "kubernetes" in agent_type:
            return "container"
        else:
            return "server"

    def _discover_connections(self, agents, since):
        """Discover connections between nodes from events"""
        from apps.events.models import Event

        connections = []
        connection_map = {}

        events = Event.objects.filter(
            timestamp__gte=since,
            source_ip__isnull=False,
        )
        if self.organization:
            events = events.filter(agent__organization=self.organization)

        for event in events.select_related("agent"):
            source_ip = event.source_ip
            target_ip = event.target_ip or getattr(event.agent, "ip_address", None)

            if source_ip and target_ip and source_ip != target_ip:
                key = f"{source_ip}:{target_ip}:{event.source_port or 0}"

                if key not in connection_map:
                    connection_map[key] = {
                        "source_ip": source_ip,
                        "target_ip": target_ip,
                        "port": event.source_port,
                        "count": 0,
                        "type": "unknown",
                        "protocol": "",
                        "first_seen": event.timestamp,
                        "last_seen": event.timestamp,
                    }

                conn = connection_map[key]
                conn["count"] += 1
                conn["last_seen"] = event.timestamp

                if event.timestamp < conn["first_seen"]:
                    conn["first_seen"] = event.timestamp

                # Determine connection type
                if event.source == "ssh":
                    conn["type"] = "ssh"
                    conn["protocol"] = "SSH"
                elif event.source in ["nginx", "nginx_access", "nginx_error"]:
                    conn["type"] = "http"
                    conn["protocol"] = "HTTP"
                elif event.source in ["django", "application"]:
                    conn["type"] = "api"
                    conn["protocol"] = "HTTP"

        return list(connection_map.values())

    def _auto_position_nodes(self):
        """Auto-position nodes using circular layout"""
        import math
        from .models import NetworkNode

        nodes = list(NetworkNode.objects.filter(organization=self.organization))
        if not nodes:
            return

        n = len(nodes)
        radius = max(200, n * 35)
        center_x, center_y = 400, 300

        type_groups = defaultdict(list)
        for node in nodes:
            type_groups[node.node_type].append(node)

        types = list(type_groups.keys())
        angle_per_type = 2 * math.pi / max(len(types), 1)

        for type_idx, node_type in enumerate(types):
            group = type_groups[node_type]
            base_angle = type_idx * angle_per_type
            angle_per_node = angle_per_type / max(len(group), 1)

            for node_idx, node in enumerate(group):
                angle = base_angle + node_idx * angle_per_node
                node.x_position = center_x + radius * math.cos(angle)
                node.y_position = center_y + radius * math.sin(angle)
                node.save(update_fields=["x_position", "y_position"])
