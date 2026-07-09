import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinelops.settings')

app = Celery('sentinelops')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'check-agent-health': {
        'task': 'apps.agents.tasks.monitor_agent_health',
        'schedule': crontab(minute='*/2'),  # Every 2 minutes
    },
    'check-missed-heartbeats': {
        'task': 'apps.agents.tasks.check_agent_heartbeats',
        'schedule': crontab(minute='*/1'),  # Every minute
    },
    'evaluate-rules': {
        'task': 'apps.rules.tasks.evaluate_all_rules',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'run-correlation': {
        'task': 'apps.incidents.tasks.run_correlation_engine',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'check-sla': {
        'task': 'apps.incidents.tasks.check_sla_compliance',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate-daily-report': {
        'task': 'apps.reports.tasks.generate_daily_reports',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
    'cleanup-old-logs': {
        'task': 'apps.logs.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # 2 AM
    },
}