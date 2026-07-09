# apps/notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'channels', views.NotificationChannelViewSet, basename='notification-channel')

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationViewSet.as_view({'get': 'list'}), name='list'),
    path('unread/', views.NotificationViewSet.as_view({'get': 'unread'}), name='unread'),
    path('recent/', views.NotificationViewSet.as_view({'get': 'recent'}), name='recent'),
    path('mark-all-read/', views.NotificationViewSet.as_view({'post': 'mark_all_read'}), name='mark-all-read'),
    path('test/', views.NotificationViewSet.as_view({'post': 'test'}), name='test'),
    path('<uuid:pk>/read/', views.NotificationViewSet.as_view({'post': 'mark_read'}), name='mark-read'),
    path('', include(router.urls)),
]