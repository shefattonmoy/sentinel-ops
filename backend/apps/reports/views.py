# apps/reports/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q, Max, Min
from django.db.models.functions import TruncDay, TruncHour
from datetime import datetime, timedelta
from apps.audit.models import log_action
import io
import csv
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponse

from .models import Report
from apps.events.models import Event
from apps.alerts.models import Alert
from apps.incidents.models import Incident
from apps.agents.models import Agent
from apps.logs.models import RawLog


class ReportViewSet(viewsets.ModelViewSet):
    """Generate and manage reports"""

    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get_queryset(self):
        return Report.objects.filter(
            organization=self.request.user.organization
        ).order_by("-created_at")

    def _get_org_filter(self):
        if self.request.user.organization:
            return {"agent__organization": self.request.user.organization}
        return {}

    def _get_alert_org_filter(self):
        if self.request.user.organization:
            return {"organization": self.request.user.organization}
        return {}

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate a new report"""
        report_type = request.data.get("report_type", "daily_soc")
        date_str = request.data.get("date")

        generator = ReportGenerator(request.user.organization)

        if report_type == "daily_soc":
            date = (
                datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_str
                else timezone.now().date()
            )
            data = generator.generate_daily_soc_report(date)
            name = f"Daily SOC Report - {date.isoformat()}"
        elif report_type == "weekly":
            end_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_str
                else timezone.now().date()
            )
            data = generator.generate_weekly_report(end_date)
            name = f"Weekly Report - {end_date.isoformat()}"
        elif report_type == "monthly":
            end_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_str
                else timezone.now().date()
            )
            data = generator.generate_monthly_report(end_date)
            name = f"Monthly Report - {end_date.isoformat()}"
        elif report_type == "executive":
            data = generator.generate_executive_summary()
            name = f"Executive Summary - {timezone.now().date().isoformat()}"
        elif report_type == "incident_summary":
            incident_id = request.data.get("incident_id")
            data = generator.generate_incident_summary(incident_id)
            name = f"Incident Summary - {incident_id}"
        else:
            return Response({"error": "Invalid report type"}, status=400)

        if not data:
            return Response({"error": "Failed to generate report"}, status=400)

        report = Report.objects.create(
            name=name,
            report_type=report_type,
            format="json",
            data=data,
            status="completed",
            generated_at=timezone.now(),
            organization=request.user.organization,
            created_by=request.user,
        )

        log_action(
            user=request.user,
            action="REPORT_GENERATE",
            description=f'{report_type.replace("_", " ").title()} generated: {name}',
            obj=report,
            severity="info",
            request=request,
        )

        return Response(
            {
                "id": str(report.id),
                "name": report.name,
                "type": report.report_type,
                "data": data,
                "generated_at": report.generated_at.isoformat(),
            }
        )

    @action(detail=False, methods=["get"])
    def list_reports(self, request):
        """List generated reports"""
        reports = self.get_queryset()[:50]
        return Response(
            [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "report_type": r.report_type,
                    "format": r.format,
                    "status": r.status,
                    "generated_at": (
                        r.generated_at.isoformat() if r.generated_at else None
                    ),
                    "created_at": r.created_at.isoformat(),
                }
                for r in reports
            ]
        )

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        """Download report as PDF"""
        report = self.get_object()
        data = report.data

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=20,
            spaceAfter=20,
            textColor=colors.HexColor("#6366f1"),
        )
        elements.append(Paragraph(f"SentinelOps - {report.name}", title_style))
        elements.append(
            Paragraph(
                f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M') if report.generated_at else 'N/A'}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # Summary
        if "summary" in data:
            elements.append(Paragraph("Summary", styles["Heading2"]))
            summary_data = [["Metric", "Value"]]
            for key, value in data["summary"].items():
                summary_data.append([key.replace("_", " ").title(), str(value)])
            table = Table(summary_data, colWidths=[250, 200])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 20))

        # Top Events
        if "top_events" in data:
            elements.append(Paragraph("Top Events", styles["Heading2"]))
            event_data = [["Event Type", "Count"]]
            for event in data["top_events"][:10]:
                event_data.append(
                    [event.get("event_type", "N/A"), str(event.get("count", 0))]
                )
            table = Table(event_data, colWidths=[250, 200])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 20))

        # Top IPs
        if "top_ips" in data:
            elements.append(Paragraph("Top Source IPs", styles["Heading2"]))
            ip_data = [["IP Address", "Count"]]
            for ip in data["top_ips"][:10]:
                ip_data.append([ip.get("source_ip", "N/A"), str(ip.get("count", 0))])
            table = Table(ip_data, colWidths=[250, 200])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            elements.append(table)

        # Footer
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph("Generated by SentinelOps Security Platform", styles["Normal"])
        )

        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{report.name}.pdf"'
        return response

    @action(detail=True, methods=["get"])
    def download_csv(self, request, pk=None):
        """Download report as CSV"""
        report = self.get_object()
        data = report.data

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{report.name}.csv"'

        writer = csv.writer(response)

        if "summary" in data:
            writer.writerow(["Metric", "Value"])
            for key, value in data["summary"].items():
                writer.writerow([key.replace("_", " ").title(), str(value)])
            writer.writerow([])

        if "top_events" in data:
            writer.writerow(["Top Events"])
            writer.writerow(["Event Type", "Count"])
            for event in data["top_events"]:
                writer.writerow([event.get("event_type", "N/A"), event.get("count", 0)])
            writer.writerow([])

        if "top_ips" in data:
            writer.writerow(["Top Source IPs"])
            writer.writerow(["IP Address", "Count"])
            for ip in data["top_ips"]:
                writer.writerow([ip.get("source_ip", "N/A"), ip.get("count", 0)])

        return response

    @action(detail=True, methods=["get"])
    def download_json(self, request, pk=None):
        """Download report as JSON"""
        report = self.get_object()
        response_data = {
            "report": {
                "id": str(report.id),
                "name": report.name,
                "type": report.report_type,
                "generated_at": (
                    report.generated_at.isoformat() if report.generated_at else None
                ),
            },
            "data": report.data,
        }
        response = HttpResponse(
            json.dumps(response_data, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = f'attachment; filename="{report.name}.json"'
        return response

    @action(detail=False, methods=["post"])
    def export(self, request):
        """Export data in various formats"""
        export_type = request.data.get("type", "events")
        fmt = request.data.get("format", "csv")
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")

        data = self._get_export_data(export_type, date_from, date_to)

        if fmt == "csv":
            return self._export_csv(export_type, data)
        elif fmt == "json":
            return Response({"data": data})

        return Response({"error": "Unsupported format"}, status=400)

    def _get_export_data(self, export_type, date_from, date_to):
        """Get data for export"""
        org_filter = self._get_org_filter()
        alert_org_filter = self._get_alert_org_filter()

        if date_from:
            date_from = timezone.make_aware(datetime.fromisoformat(date_from))
        if date_to:
            date_to = timezone.make_aware(datetime.fromisoformat(date_to))

        if export_type == "events":
            queryset = Event.objects.filter(**org_filter)
            if date_from:
                queryset = queryset.filter(timestamp__gte=date_from)
            if date_to:
                queryset = queryset.filter(timestamp__lte=date_to)
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "source": e.source,
                    "source_ip": e.source_ip,
                    "username": e.username,
                    "message": e.message,
                }
                for e in queryset[:10000]
            ]

        elif export_type == "alerts":
            queryset = Alert.objects.filter(**alert_org_filter)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            return [
                {
                    "created_at": a.created_at.isoformat(),
                    "title": a.title,
                    "severity": a.severity,
                    "status": a.status,
                    "source": a.source,
                    "category": a.category,
                }
                for a in queryset[:10000]
            ]

        return []

    def _export_csv(self, export_type, data):
        """Export data as CSV"""
        if not data:
            return Response({"error": "No data"}, status=400)

        output = io.StringIO()
        writer = csv.writer(output)
        if data:
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{export_type}_export.csv"'
        )
        return response


class ReportGenerator:
    """Generate various security reports"""

    def __init__(self, organization=None):
        self.organization = organization
        self.org_filter = {"agent__organization": organization} if organization else {}
        self.alert_org_filter = {"organization": organization} if organization else {}

    def generate_daily_soc_report(self, date):
        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)

        events = Event.objects.filter(
            timestamp__gte=start_of_day, timestamp__lt=end_of_day, **self.org_filter
        )
        alerts = Alert.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            **self.alert_org_filter,
        )
        incidents = Incident.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            **self.alert_org_filter,
        )
        agents = Agent.objects.filter(
            is_active=True,
            **({"organization": self.organization} if self.organization else {}),
        )

        return {
            "report_type": "daily_soc",
            "date": date.isoformat(),
            "generated_at": timezone.now().isoformat(),
            "summary": {
                "total_events": events.count(),
                "total_alerts": alerts.count(),
                "critical_alerts": alerts.filter(severity="critical").count(),
                "total_incidents": incidents.count(),
                "agents_online": agents.filter(status="online").count(),
                "agents_total": agents.count(),
                "failed_logins": events.filter(event_type="FAILED_LOGIN").count(),
            },
            "top_events": list(
                events.values("event_type")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
            "top_ips": list(
                events.filter(source_ip__isnull=False)
                .values("source_ip")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
            "alerts_by_severity": list(
                alerts.values("severity").annotate(count=Count("id"))
            ),
            "hourly_events": list(
                events.annotate(hour=TruncHour("timestamp"))
                .values("hour")
                .annotate(count=Count("id"))
                .order_by("hour")
            ),
        }

    def generate_weekly_report(self, end_date):
        start_date = end_date - timedelta(days=7)
        start_dt = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))

        events = Event.objects.filter(
            timestamp__gte=start_dt, timestamp__lt=end_dt, **self.org_filter
        )
        alerts = Alert.objects.filter(
            created_at__gte=start_dt, created_at__lt=end_dt, **self.alert_org_filter
        )
        incidents = Incident.objects.filter(
            created_at__gte=start_dt, created_at__lt=end_dt, **self.alert_org_filter
        )

        return {
            "report_type": "weekly",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": timezone.now().isoformat(),
            "summary": {
                "total_events": events.count(),
                "avg_events_per_day": round(events.count() / 7),
                "total_alerts": alerts.count(),
                "total_incidents": incidents.count(),
                "incidents_resolved": incidents.filter(
                    status__in=["resolved", "closed"]
                ).count(),
            },
            "daily_breakdown": list(
                events.annotate(day=TruncDay("timestamp"))
                .values("day")
                .annotate(count=Count("id"))
                .order_by("day")
            ),
            "top_event_types": list(
                events.values("event_type")
                .annotate(count=Count("id"))
                .order_by("-count")[:15]
            ),
            "top_ips": list(
                events.filter(source_ip__isnull=False)
                .values("source_ip")
                .annotate(count=Count("id"))
                .order_by("-count")[:20]
            ),
        }

    def generate_monthly_report(self, end_date):
        start_date = end_date - timedelta(days=30)
        start_dt = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))

        events = Event.objects.filter(
            timestamp__gte=start_dt, timestamp__lt=end_dt, **self.org_filter
        )
        alerts = Alert.objects.filter(
            created_at__gte=start_dt, created_at__lt=end_dt, **self.alert_org_filter
        )

        return {
            "report_type": "monthly",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": timezone.now().isoformat(),
            "days": 30,
            "summary": {
                "total_events": events.count(),
                "avg_events_per_day": round(events.count() / 30),
                "total_alerts": alerts.count(),
            },
        }

    def generate_executive_summary(self):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        mid_point = now - timedelta(days=15)

        events = Event.objects.filter(timestamp__gte=thirty_days_ago, **self.org_filter)
        alerts = Alert.objects.filter(
            created_at__gte=thirty_days_ago, **self.alert_org_filter
        )
        incidents = Incident.objects.filter(
            created_at__gte=thirty_days_ago, **self.alert_org_filter
        )
        agents = Agent.objects.filter(
            is_active=True,
            **({"organization": self.organization} if self.organization else {}),
        )

        events_first_half = events.filter(timestamp__lt=mid_point).count()
        events_second_half = events.filter(timestamp__gte=mid_point).count()

        return {
            "report_type": "executive_summary",
            "period": {
                "start": thirty_days_ago.date().isoformat(),
                "end": now.date().isoformat(),
            },
            "generated_at": now.isoformat(),
            "key_metrics": {
                "total_events_30d": events.count(),
                "total_alerts_30d": alerts.count(),
                "total_incidents_30d": incidents.count(),
                "critical_incidents": incidents.filter(severity="critical").count(),
                "avg_daily_events": round(events.count() / 30),
                "agents_online_pct": round(
                    agents.filter(status="online").count()
                    / max(agents.count(), 1)
                    * 100,
                    1,
                ),
            },
            "trends": {
                "events_trend": (
                    "increasing"
                    if events_second_half > events_first_half
                    else "decreasing"
                ),
                "events_change_pct": round(
                    (events_second_half - events_first_half)
                    / max(events_first_half, 1)
                    * 100,
                    1,
                ),
            },
            "top_risks": self._identify_risks(alerts, incidents),
            "recommendations": self._get_recommendations(alerts, incidents),
        }

    def generate_incident_summary(self, incident_id):
        try:
            incident = Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            return None
        return {
            "report_type": "incident_summary",
            "incident": {
                "id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
                "status": incident.status,
                "priority": incident.priority,
                "type": incident.incident_type,
                "source_ip": incident.source_ip,
                "detected_at": (
                    incident.detected_at.isoformat() if incident.detected_at else None
                ),
                "resolved_at": (
                    incident.resolved_at.isoformat() if incident.resolved_at else None
                ),
                "time_to_detect_min": incident.time_to_detect,
                "time_to_resolve_min": incident.time_to_resolve,
                "alerts_count": incident.alerts.count(),
                "events_count": incident.events.count(),
                "resolution": incident.resolution,
                "root_cause": incident.root_cause,
            },
            "timeline": list(
                incident.timeline.values(
                    "entry_type", "description", "timestamp"
                ).order_by("timestamp")[:50]
            ),
        }

    def _identify_risks(self, alerts, incidents):
        risks = []
        critical_count = incidents.filter(severity="critical").count()
        if critical_count > 0:
            risks.append(
                {
                    "risk": "Critical Incidents",
                    "count": critical_count,
                    "level": "critical",
                }
            )
        brute_force = alerts.filter(
            category="authentication", severity__in=["high", "critical"]
        ).count()
        if brute_force > 10:
            risks.append(
                {"risk": "Brute Force Activity", "count": brute_force, "level": "high"}
            )
        overdue = alerts.filter(is_overdue=True).count()
        if overdue > 5:
            risks.append({"risk": "Overdue Alerts", "count": overdue, "level": "high"})
        return risks

    def _get_recommendations(self, alerts, incidents):
        recommendations = []
        if incidents.filter(incident_type="brute_force").count() > 0:
            recommendations.append("Implement MFA and rate limiting for SSH access")
        if alerts.filter(category="container").count() > 10:
            recommendations.append("Review container resource limits and health checks")
        if alerts.filter(is_overdue=True).count() > 5:
            recommendations.append("Review alert response procedures and staffing")
        if not recommendations:
            recommendations.append(
                "Continue current security posture - no critical issues detected"
            )
        return recommendations
