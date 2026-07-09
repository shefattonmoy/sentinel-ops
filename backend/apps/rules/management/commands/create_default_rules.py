# apps/rules/management/commands/create_default_rules.py
from django.core.management.base import BaseCommand
from apps.rules.models import DetectionRule, RuleTemplate

DEFAULT_RULES = [
    {
        'name': 'SSH Brute Force Detection',
        'description': 'Detects multiple failed SSH login attempts from the same IP',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'FAILED_LOGIN',
            'timeframe_minutes': 5,
            'threshold': 5,
            'group_by': ['source_ip'],
            'filters': {
                'source': ['ssh']
            }
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'SSH Brute Force Attack Detected from {source_ip}',
            'alert_severity': 'high',
            'alert_category': 'security',
            'auto_escalate': True,
            'notify_channels': ['email'],
        },
        'severity': 'high',
        'category': 'authentication',
        'cooldown_minutes': 5,
    },
    {
        'name': 'Container Crash Loop',
        'description': 'Detects containers that are continuously crashing/restarting',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'CONTAINER_RESTART',
            'timeframe_minutes': 10,
            'threshold': 3,
            'group_by': ['service'],
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'Container Crash Loop Detected - {service}',
            'alert_severity': 'critical',
            'alert_category': 'infrastructure',
        },
        'severity': 'critical',
        'category': 'container',
        'cooldown_minutes': 10,
    },
    {
        'name': 'High Web Server Error Rate',
        'description': 'Detects high rate of 500 errors in web applications',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'SERVER_ERROR',
            'timeframe_minutes': 5,
            'threshold': 10,
            'group_by': ['source_ip'],
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'High Server Error Rate from {source_ip}',
            'alert_severity': 'high',
            'alert_category': 'application',
        },
        'severity': 'high',
        'category': 'application',
        'cooldown_minutes': 5,
    },
    {
        'name': 'Multiple User Creation',
        'description': 'Detects multiple user accounts being created in short time',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'USER_CREATED',
            'timeframe_minutes': 10,
            'threshold': 2,
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'Multiple User Accounts Created',
            'alert_severity': 'high',
            'alert_category': 'security',
            'create_incident': True,
        },
        'severity': 'high',
        'category': 'authorization',
        'cooldown_minutes': 15,
    },
    {
        'name': 'Container Out of Memory',
        'description': 'Detects containers killed due to out of memory',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'CONTAINER_OOM',
            'timeframe_minutes': 5,
            'threshold': 1,
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'Container Out of Memory - {service}',
            'alert_severity': 'critical',
            'alert_category': 'infrastructure',
            'notify_channels': ['email', 'slack'],
        },
        'severity': 'critical',
        'category': 'container',
        'cooldown_minutes': 5,
    },
    {
        'name': 'Access Denied Spike',
        'description': 'Detects spike in 401/403 responses',
        'rule_type': 'threshold',
        'conditions': {
            'event_type': 'ACCESS_DENIED',
            'timeframe_minutes': 5,
            'threshold': 10,
            'group_by': ['source_ip'],
        },
        'actions': {
            'create_alert': True,
            'alert_title': 'Access Denied Spike from {source_ip}',
            'alert_severity': 'medium',
            'alert_category': 'security',
        },
        'severity': 'medium',
        'category': 'security',
        'cooldown_minutes': 10,
    },
]

class Command(BaseCommand):
    help = 'Create default detection rules'

    def handle(self, *args, **options):
        for rule_data in DEFAULT_RULES:
            rule, created = DetectionRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created rule: {rule.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Rule already exists: {rule.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Default rules creation complete')
        )