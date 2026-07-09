from django.urls import path
from .views import ThreatIntelViewSet

app_name = 'threat_intel'

urlpatterns = [
    path('top-threats/', ThreatIntelViewSet.as_view({'get': 'top_threats'}), name='top-threats'),
    path('threat-map/', ThreatIntelViewSet.as_view({'get': 'threat_map'}), name='threat-map'),
    path('score-ip/', ThreatIntelViewSet.as_view({'post': 'score_ip'}), name='score-ip'),
    path('bulk-score/', ThreatIntelViewSet.as_view({'post': 'bulk_score'}), name='bulk-score'),
    path('ip-lookup/', ThreatIntelViewSet.as_view({'get': 'ip_lookup'}), name='ip-lookup'),
    path('stats/', ThreatIntelViewSet.as_view({'get': 'stats'}), name='stats'),
    path('add-reputation/', ThreatIntelViewSet.as_view({'post': 'add_reputation'}), name='add-reputation'),
    path('recent/', ThreatIntelViewSet.as_view({'get': 'recent'}), name='recent'),
]