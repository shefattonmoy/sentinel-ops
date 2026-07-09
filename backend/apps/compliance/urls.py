from django.urls import path
from .views import ComplianceViewSet

app_name = 'compliance'

urlpatterns = [
    path('frameworks/', ComplianceViewSet.as_view({'get': 'frameworks'})),
    path('generate-evidence/', ComplianceViewSet.as_view({'post': 'generate_evidence'})),
]