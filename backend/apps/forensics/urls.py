from django.urls import path
from .views import ForensicsViewSet

app_name = 'forensics'

urlpatterns = [
    path('timeline/', ForensicsViewSet.as_view({'get': 'host_timeline'}), name='timeline'),
    path('attack-chain/', ForensicsViewSet.as_view({'get': 'attack_chain'}), name='attack-chain'),
    path('hosts/', ForensicsViewSet.as_view({'get': 'hosts'}), name='hosts'),
    path('stats/', ForensicsViewSet.as_view({'get': 'stats'}), name='stats'), 
]