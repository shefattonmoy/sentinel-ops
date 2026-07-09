# apps/dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, DashboardWidgetViewSet

router = DefaultRouter()
router.register(r"widgets", DashboardWidgetViewSet, basename="widget")

app_name = "dashboard"

urlpatterns = [
    # Overview
    path("overview/", DashboardViewSet.as_view({"get": "overview"}), name="overview"),
    # Events
    path(
        "events-chart/",
        DashboardViewSet.as_view({"get": "events_chart"}),
        name="events-chart",
    ),
    path(
        "events-by-type/",
        DashboardViewSet.as_view({"get": "events_by_type"}),
        name="events-by-type",
    ),
    # Alerts
    path(
        "alert-stats/",
        DashboardViewSet.as_view({"get": "alert_stats"}),
        name="alert-stats",
    ),
    # Top lists
    path("top-ips/", DashboardViewSet.as_view({"get": "top_ips"}), name="top-ips"),
    path(
        "top-usernames/",
        DashboardViewSet.as_view({"get": "top_usernames"}),
        name="top-usernames",
    ),
    path(
        "top-servers/",
        DashboardViewSet.as_view({"get": "top_servers"}),
        name="top-servers",
    ),
    # Agent health
    path(
        "agent-health/",
        DashboardViewSet.as_view({"get": "agent_health"}),
        name="agent-health",
    ),
    # Failed logins
    path(
        "failed-logins/",
        DashboardViewSet.as_view({"get": "failed_logins"}),
        name="failed-logins",
    ),
    path(
        "successful-logins/",
        DashboardViewSet.as_view({"get": "successful_logins"}),
        name="successful-logins",
    ),
    # Incidents
    path(
        "incident-stats/",
        DashboardViewSet.as_view({"get": "incident_stats"}),
        name="incident-stats",
    ),
    # Recent activity
    path(
        "recent-activity/",
        DashboardViewSet.as_view({"get": "recent_activity"}),
        name="recent-activity",
    ),
    # Widgets
    path("", include(router.urls)),
]
