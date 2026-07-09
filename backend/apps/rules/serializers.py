# apps/rules/serializers.py
from rest_framework import serializers
from .models import DetectionRule, RuleExecution, RuleTemplate

class DetectionRuleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DetectionRule
        fields = [
            'id', 'name', 'description', 'rule_type',
            'conditions', 'actions', 'severity', 'category',
            'status', 'priority', 'cooldown_minutes',
            'times_triggered', 'last_triggered', 'alerts_generated',
            'apply_to_all_agents', 'agents', 'agent_groups',
            'organization', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'times_triggered', 'last_triggered',
            'alerts_generated', 'created_at', 'updated_at'
        ]

class RuleExecutionSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = RuleExecution
        fields = '__all__'

class RuleTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleTemplate
        fields = '__all__'