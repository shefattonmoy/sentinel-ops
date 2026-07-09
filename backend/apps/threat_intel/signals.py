from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.events.models import Event
from .scoring import ThreatScoringEngine

@receiver(post_save, sender=Event)
def update_threat_score(sender, instance, created, **kwargs):
    """Update threat score when new event is created"""
    if created and instance.source_ip:
        try:
            engine = ThreatScoringEngine()
            engine.calculate_threat_score(instance.source_ip)
        except Exception as e:
            pass 