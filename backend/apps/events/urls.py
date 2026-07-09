# apps/events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.EventViewSet, basename='event')

app_name = 'events'

urlpatterns = [
    path('', include(router.urls)),
]