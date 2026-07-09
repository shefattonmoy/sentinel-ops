from django.urls import path
from .views import HoneypotViewSet

app_name = 'honeypot'

urlpatterns = [
    path('interactions/', HoneypotViewSet.as_view({'get': 'interactions'}), name='interactions'),
    path('stats/', HoneypotViewSet.as_view({'get': 'stats'}), name='stats'),
    path('honeypots/', HoneypotViewSet.as_view({'get': 'honeypots'}), name='honeypots'),
    path('create/', HoneypotViewSet.as_view({'post': 'create_honeypot'}), name='create'),
    path('toggle/', HoneypotViewSet.as_view({'post': 'toggle'}), name='toggle'),
]