from rest_framework import serializers
from .models import Playbook, PlaybookExecution

class PlaybookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playbook
        fields = '__all__'
        read_only_fields = ['id', 'times_executed', 'last_executed', 'created_at', 'updated_at']

class PlaybookExecutionSerializer(serializers.ModelSerializer):
    playbook_name = serializers.CharField(source='playbook.name', read_only=True)
    
    class Meta:
        model = PlaybookExecution
        fields = '__all__'