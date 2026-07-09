from django.core.management.base import BaseCommand
from apps.mitre.importer import import_mitre_data, import_event_mappings

class Command(BaseCommand):
    help = 'Import MITRE ATT&CK framework data'

    def handle(self, *args, **options):
        self.stdout.write('Importing MITRE ATT&CK data...')
        count = import_mitre_data()
        self.stdout.write(self.style.SUCCESS(f'Imported {count} techniques'))
        
        self.stdout.write('Creating event mappings...')
        mappings = import_event_mappings()
        self.stdout.write(self.style.SUCCESS(f'Created {mappings} event mappings'))