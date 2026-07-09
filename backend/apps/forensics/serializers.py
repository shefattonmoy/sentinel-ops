from rest_framework import serializers
from .models import ForensicTimeline, TimelineEntry

class TimelineEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineEntry
        fields = '__all__'

class ForensicTimelineSerializer(serializers.ModelSerializer):
    entries = TimelineEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = ForensicTimeline
        fields = '__all__'