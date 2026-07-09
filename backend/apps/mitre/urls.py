from django.urls import path
from .views import MitreViewSet

app_name = 'mitre'

urlpatterns = [
    path('techniques/', MitreViewSet.as_view({'get': 'techniques'}), name='techniques'),
    path('matrix/', MitreViewSet.as_view({'get': 'matrix'}), name='matrix'),
    path('coverage/', MitreViewSet.as_view({'get': 'matrix'}), name='coverage'),
    path('mappings/', MitreViewSet.as_view({'get': 'mappings'}), name='mappings'),
    path('stats/', MitreViewSet.as_view({'get': 'stats'}), name='stats'),
]