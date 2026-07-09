# apps/scheduler/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import ExportSchedule, ExportRun
from apps.reports.views import ReportGenerator

@shared_task
def run_scheduled_exports():
    """Run all due export schedules"""
    now = timezone.now()
    
    schedules = ExportSchedule.objects.filter(
        is_active=True,
        next_run__lte=now
    )
    
    for schedule in schedules:
        execute_export.delay(str(schedule.id))

@shared_task
def execute_export(schedule_id):
    """Execute a single export schedule"""
    from .models import ExportSchedule, ExportRun
    
    try:
        schedule = ExportSchedule.objects.get(id=schedule_id)
    except ExportSchedule.DoesNotExist:
        return
    
    run = ExportRun.objects.create(schedule=schedule, status='running')
    
    try:
        # Generate export based on type
        data = generate_export_data(schedule)
        
        # Format and deliver
        if schedule.destination == 'email':
            send_export_email(schedule, data)
        elif schedule.destination == 'webhook':
            send_export_webhook(schedule, data)
        elif schedule.destination == 'local':
            save_export_local(schedule, data, run)
        
        run.status = 'completed'
        run.record_count = len(data) if isinstance(data, list) else 1
        run.completed_at = timezone.now()
        run.save()
        
        # Schedule next run
        schedule.last_run = timezone.now()
        schedule.next_run = calculate_next_run(schedule)
        schedule.save()
        
    except Exception as e:
        run.status = 'failed'
        run.error_message = str(e)
        run.completed_at = timezone.now()
        run.save()

def generate_export_data(schedule):
    """Generate data for export"""
    from apps.events.models import Event
    from apps.alerts.models import Alert
    
    date_from = schedule.filters.get('date_from')
    date_to = schedule.filters.get('date_to')
    
    if not date_from:
        date_from = timezone.now() - timedelta(days=7)
    
    if schedule.export_type == 'events':
        queryset = Event.objects.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        return list(queryset.values()[:10000])
    
    elif schedule.export_type == 'alerts':
        queryset = Alert.objects.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        return list(queryset.values()[:10000])
    
    elif schedule.export_type == 'report':
        generator = ReportGenerator(schedule.organization)
        return generator.generate_daily_soc_report(timezone.now().date())
    
    return []

def send_export_email(schedule, data):
    """Send export via email"""
    from django.core.mail import EmailMessage
    import json, csv, io
    
    emails = schedule.destination_config.get('emails', [])
    if not emails:
        return
    
    subject = f'SentinelOps - {schedule.export_type.title()} Export'
    body = f'Attached is your scheduled {schedule.export_type} export.'
    
    email = EmailMessage(subject, body, to=emails)
    
    if schedule.format == 'json':
        content = json.dumps(data, indent=2)
        email.attach(f'{schedule.export_type}_export.json', content, 'application/json')
    elif schedule.format == 'csv':
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        email.attach(f'{schedule.export_type}_export.csv', output.getvalue(), 'text/csv')
    
    email.send()

def send_export_webhook(schedule, data):
    """Send export via webhook"""
    import requests
    
    url = schedule.destination_config.get('url')
    if not url:
        return
    
    requests.post(url, json={'data': data}, timeout=30)

def save_export_local(schedule, data, run):
    """Save export to local storage"""
    import json
    
    filename = f'exports/{schedule.export_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
    # Save to file storage
    run.file_url = filename

def calculate_next_run(schedule):
    """Calculate next run time"""
    now = timezone.now()
    
    if schedule.frequency == 'hourly':
        return now + timedelta(hours=1)
    elif schedule.frequency == 'daily':
        return now + timedelta(days=1)
    elif schedule.frequency == 'weekly':
        return now + timedelta(weeks=1)
    elif schedule.frequency == 'monthly':
        return now + timedelta(days=30)
    
    return now + timedelta(days=1)