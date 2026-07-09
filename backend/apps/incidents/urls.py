# apps/incidents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.IncidentViewSet, basename='incident')

app_name = 'incidents'

urlpatterns = [
    path('', include(router.urls)),
]