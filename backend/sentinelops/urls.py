from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/agents/', include('apps.agents.urls')),
    path('api/logs/', include('apps.logs.urls')),
    path('api/events/', include('apps.events.urls')),
    path('api/rules/', include('apps.rules.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/incidents/', include('apps.incidents.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/threat-intel/', include('apps.threat_intel.urls')),
    path('api/playbooks/', include('apps.playbooks.urls')),
    path('api/scheduler/', include('apps.scheduler.urls')),
    path('api/mitre/', include('apps.mitre.urls')),
    path('api/forensics/', include('apps.forensics.urls')),
    path('api/risks/', include('apps.risks.urls')),
    path('api/honeypot/', include('apps.honeypot.urls')),
    path('api/compliance/', include('apps.compliance.urls')),
    path('api/topology/', include('apps.topology.urls')),
    path('api/chat/', include('apps.ai_assistant.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/gamification/', include('apps.gamification.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)