from rest_framework import serializers
from .models import ExportSchedule, ExportRun

class ExportScheduleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ExportSchedule
        fields = '__all__'
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']

class ExportRunSerializer(serializers.ModelSerializer):
    schedule_name = serializers.CharField(source='schedule.name', read_only=True)
    
    class Meta:
        model = ExportRun
        fields = '__all__'