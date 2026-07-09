# apps/logs/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'raw-logs', views.RawLogViewSet, basename='rawlog')
router.register(r'batches', views.LogBatchViewSet, basename='logbatch')

app_name = 'logs'

urlpatterns = [
    # Public endpoints
    path('ingest/', views.ingest_logs, name='log-ingest'),
    
    # Authenticated endpoints
    path('sources/', views.log_sources, name='log-sources'),
    path('', include(router.urls)),
]