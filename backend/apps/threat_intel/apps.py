from django.apps import AppConfig

class ThreatIntelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.threat_intel'
    label = 'threat_intel'
    
    def ready(self):
        import apps.threat_intel.signals