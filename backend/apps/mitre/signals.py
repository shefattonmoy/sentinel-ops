from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.events.models import Event
from .models import EventTechniqueMapping, MitreCoverage
from django.utils import timezone

@receiver(post_save, sender=Event)
def update_mitre_coverage(sender, instance, created, **kwargs):
    """Update MITRE coverage when events occur"""
    if not created:
        return
    
    try:
        mapping = EventTechniqueMapping.objects.filter(
            event_type=instance.event_type
        ).select_related('technique').first()
        
        if mapping and instance.agent and instance.agent.organization:
            coverage, _ = MitreCoverage.objects.get_or_create(
                technique=mapping.technique,
                organization=instance.agent.organization,
            )
            coverage.detected_events += 1
            coverage.last_detected = timezone.now()
            coverage.is_covered = True
            coverage.save()
    except Exception:
        pass