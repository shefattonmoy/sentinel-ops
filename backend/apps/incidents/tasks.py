# apps/incidents/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .correlation import CorrelationEngine
from .models import Incident

@shared_task
def run_correlation_engine():
    """
    Periodic task to run the correlation engine.
    Should run every 5-10 minutes.
    """
    engine = CorrelationEngine()
    incidents = engine.correlate_alerts()
    
    return f"Correlation complete: {len(incidents)} incidents created"

@shared_task
def check_sla_compliance():
    """
    Check SLA compliance and mark overdue incidents.
    Runs every 5 minutes.
    """
    now = timezone.now()
    
    overdue_count = Incident.objects.filter(
        sla_deadline__lt=now,
        is_overdue=False,
        status__in=['new', 'triaging', 'investigating', 'containment']
    ).update(is_overdue=True)
    
    return f"Marked {overdue_count} incidents as overdue"

@shared_task
def generate_daily_incident_report():
    """
    Generate daily incident summary report.
    Runs at midnight.
    """
    yesterday = timezone.now() - timedelta(days=1)
    
    incidents = Incident.objects.filter(created_at__gte=yesterday)
    
    report = {
        'date': yesterday.date().isoformat(),
        'total': incidents.count(),
        'by_severity': {
            'critical': incidents.filter(severity='critical').count(),
            'high': incidents.filter(severity='high').count(),
            'medium': incidents.filter(severity='medium').count(),
            'low': incidents.filter(severity='low').count(),
        },
        'resolved': incidents.filter(
            status__in=['resolved', 'closed']
        ).count(),
        'still_open': incidents.filter(
            status__in=['new', 'triaging', 'investigating', 'containment']
        ).count(),
    }
    
    # Store report or send via email
    # This could be saved to a Report model or sent via notification service
    
    return f"Daily report generated: {report}"