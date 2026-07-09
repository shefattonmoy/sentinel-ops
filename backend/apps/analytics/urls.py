# apps/analytics/urls.py
from django.urls import path
from .views import AnalyticsViewSet

app_name = 'analytics'

urlpatterns = [
    path('users/', AnalyticsViewSet.as_view({'get': 'users'}), name='users'),
    path('anomalies/', AnalyticsViewSet.as_view({'get': 'anomalies'}), name='anomalies'),
    path('analyze/', AnalyticsViewSet.as_view({'post': 'analyze'}), name='analyze'),
    path('resolve/', AnalyticsViewSet.as_view({'post': 'resolve_anomaly'}), name='resolve'),
    path('stats/', AnalyticsViewSet.as_view({'get': 'stats'}), name='stats'),
    path('user-detail/', AnalyticsViewSet.as_view({'get': 'user_detail'}), name='user-detail'),
]