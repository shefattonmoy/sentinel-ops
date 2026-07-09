from django.urls import path
from .views import RiskViewSet

app_name = 'risks'

urlpatterns = [
    path('assets/', RiskViewSet.as_view({'get': 'assets'}), name='assets'),
    path('score/', RiskViewSet.as_view({'post': 'score_asset'}), name='score'),
    path('dashboard/', RiskViewSet.as_view({'get': 'dashboard'}), name='dashboard'),
    path('history/', RiskViewSet.as_view({'get': 'history'}), name='history'),
]