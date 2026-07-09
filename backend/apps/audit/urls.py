# apps/audit/urls.py
from django.urls import path
from .views import AuditLogListView

app_name = 'apps.audit'

urlpatterns = [
    path('', AuditLogListView.as_view(), name='audit-list'),
]