# apps/incidents/management/commands/run_correlation.py
from django.core.management.base import BaseCommand
from apps.incidents.correlation import CorrelationEngine

class Command(BaseCommand):
    help = 'Run the correlation engine to create incidents from alerts'

    def handle(self, *args, **options):
        self.stdout.write('Running correlation engine...')
        
        engine = CorrelationEngine()
        incidents = engine.correlate_alerts()
        
        if incidents:
            self.stdout.write(
                self.style.SUCCESS(f'Created {len(incidents)} incidents:')
            )
            for incident in incidents:
                self.stdout.write(
                    f'  - {incident.title} ({incident.severity}) - '
                    f'{incident.alerts.count()} alerts'
                )
        else:
            self.stdout.write(
                self.style.WARNING('No new incidents created')
            )