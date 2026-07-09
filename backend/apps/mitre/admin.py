from django.contrib import admin
from .models import MitreTechnique, EventTechniqueMapping, MitreCoverage

@admin.register(MitreTechnique)
class MitreTechniqueAdmin(admin.ModelAdmin):
    list_display = ['technique_id', 'name', 'tactic', 'platform']
    list_filter = ['tactic', 'platform']
    search_fields = ['technique_id', 'name', 'description']

@admin.register(EventTechniqueMapping)
class EventTechniqueMappingAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'technique', 'confidence']
    list_filter = ['technique__tactic']

@admin.register(MitreCoverage)
class MitreCoverageAdmin(admin.ModelAdmin):
    list_display = ['technique', 'organization', 'is_covered', 'detected_events', 'last_detected']
    list_filter = ['is_covered', 'technique__tactic']