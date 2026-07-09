from django.urls import path
from .views import TopologyViewSet

app_name = 'topology'

urlpatterns = [
    path('map/', TopologyViewSet.as_view({'get': 'map'}), name='map'),
    path('discover/', TopologyViewSet.as_view({'post': 'discover'}), name='discover'),
    path('update-position/', TopologyViewSet.as_view({'post': 'update_position'}), name='update-position'),
    path('stats/', TopologyViewSet.as_view({'get': 'stats'}), name='stats'),
    path('node-detail/', TopologyViewSet.as_view({'get': 'node_detail'}), name='node-detail'),
]