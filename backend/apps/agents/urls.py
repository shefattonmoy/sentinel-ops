# apps/agents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'manage', views.AgentViewSet, basename='agent')
router.register(r'groups', views.AgentGroupViewSet, basename='agent-group')

app_name = 'agents'

urlpatterns = [
    # Public endpoints (no authentication required)
    path('register/', views.register_agent, name='agent-register'),
    path('heartbeat/', views.agent_heartbeat, name='agent-heartbeat'),
    path('error-report/', views.agent_error_report, name='agent-error-report'),
    
    # Authenticated endpoints
    path('stats/', views.agent_stats, name='agent-stats'),
    path('', include(router.urls)),
]