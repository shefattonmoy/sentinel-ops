from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count, Q
from datetime import timedelta
import requests

from .models import ThreatScore, IPReputation
from .serializers import ThreatScoreSerializer, IPReputationSerializer
from .scoring import ThreatScoringEngine


class ThreatIntelViewSet(viewsets.ViewSet):
    """Threat Intelligence API"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def top_threats(self, request):
        """Get top threats by score"""
        limit = int(request.query_params.get("limit", 20))
        engine = ThreatScoringEngine(request.user.organization)
        threats = engine.get_top_threats(limit)
        return Response(threats)

    @action(detail=False, methods=["get"])
    def threat_map(self, request):
        """Get threat data for attack map visualization"""
        engine = ThreatScoringEngine(request.user.organization)
        threats = engine.get_top_threats(50)

        # Enrich with geo data (simulated)
        threat_locations = []
        for threat in threats:
            threat_locations.append(
                {
                    "ip": threat["source_ip"],
                    "score": threat["threat_score"],
                    "risk_level": threat["risk_level"],
                    "total_events": threat["total_events"],
                    "lat": None,  # Would come from GeoIP
                    "lon": None,
                }
            )

        return Response(threat_locations)

    @action(detail=False, methods=["post"])
    def score_ip(self, request):
        """Score a specific IP address"""
        ip = request.data.get("ip")
        if not ip:
            return Response({"error": "IP address required"}, status=400)

        engine = ThreatScoringEngine(request.user.organization)
        score = engine.calculate_threat_score(ip)
        return Response(score)

    @action(detail=False, methods=["post"])
    def bulk_score(self, request):
        """Score multiple IPs"""
        ips = request.data.get("ips", [])
        if not ips:
            return Response({"error": "IP list required"}, status=400)

        engine = ThreatScoringEngine(request.user.organization)
        results = {}
        for ip in ips[:50]:  # Limit to 50
            results[ip] = engine.calculate_threat_score(ip)

        return Response(results)

    @action(detail=False, methods=["get"])
    def ip_lookup(self, request):
        """Look up IP reputation"""
        ip = request.query_params.get("ip")
        if not ip:
            return Response({"error": "IP required"}, status=400)

        try:
            reputation = IPReputation.objects.get(ip_address=ip)
            return Response(IPReputationSerializer(reputation).data)
        except IPReputation.DoesNotExist:
            # Return basic info
            return Response(
                {
                    "ip_address": ip,
                    "found": False,
                    "reputation_score": 50,
                    "abuse_confidence": 0,
                    "message": "No reputation data available for this IP",
                }
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get threat intelligence statistics"""
        organization = request.user.organization

        threats = ThreatScore.objects.all()
        if organization:
            threats = threats.filter(organization=organization)

        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        stats = {
            "total_threats": threats.count(),
            "critical_threats": threats.filter(risk_level="critical").count(),
            "high_threats": threats.filter(risk_level="high").count(),
            "known_attackers": threats.filter(is_known_attacker=True).count(),
            "avg_threat_score": threats.aggregate(Avg("threat_score"))[
                "threat_score__avg"
            ]
            or 0,
            "top_ips": list(
                threats.order_by("-threat_score")[:10].values(
                    "source_ip", "threat_score", "risk_level"
                )
            ),
            "by_risk_level": list(
                threats.values("risk_level").annotate(count=Count("id"))
            ),
        }

        return Response(stats)

    @action(detail=False, methods=["post"])
    def add_reputation(self, request):
        """Add or update IP reputation manually"""
        ip = request.data.get("ip")
        if not ip:
            return Response({"error": "IP required"}, status=400)

        reputation, created = IPReputation.objects.update_or_create(
            ip_address=ip,
            defaults={
                "reputation_score": request.data.get("reputation_score", 50),
                "abuse_confidence": request.data.get("abuse_confidence", 0),
                "is_tor": request.data.get("is_tor", False),
                "is_proxy": request.data.get("is_proxy", False),
                "is_vpn": request.data.get("is_vpn", False),
                "country": request.data.get("country"),
                "isp": request.data.get("isp"),
            },
        )

        return Response(
            {
                "status": "created" if created else "updated",
                "reputation": IPReputationSerializer(reputation).data,
            }
        )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recently scored threats"""
        threats = ThreatScore.objects.order_by("-updated_at")[:20]
        if request.user.organization:
            threats = threats.filter(organization=request.user.organization)

        return Response(ThreatScoreSerializer(threats, many=True).data)
