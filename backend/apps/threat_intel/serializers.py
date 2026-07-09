from rest_framework import serializers
from .models import ThreatScore, IPReputation

class ThreatScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatScore
        fields = '__all__'

class IPReputationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPReputation
        fields = '__all__'