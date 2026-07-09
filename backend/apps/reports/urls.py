# apps/reports/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')

app_name = 'reports'

urlpatterns = [
    path('generate/', ReportViewSet.as_view({'post': 'generate'}), name='generate'),
    path('list/', ReportViewSet.as_view({'get': 'list_reports'}), name='list'),
    path('<uuid:pk>/pdf/', ReportViewSet.as_view({'get': 'download_pdf'}), name='download-pdf'),
    path('<uuid:pk>/csv/', ReportViewSet.as_view({'get': 'download_csv'}), name='download-csv'),
    path('<uuid:pk>/json/', ReportViewSet.as_view({'get': 'download_json'}), name='download-json'),
    path('', include(router.urls)),
]