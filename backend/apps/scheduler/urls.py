from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExportScheduleViewSet

router = DefaultRouter()
router.register(r'', ExportScheduleViewSet, basename='schedule')

app_name = 'scheduler'

urlpatterns = [
    path('', include(router.urls)),
]