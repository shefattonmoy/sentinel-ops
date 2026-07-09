from django.urls import path
from .views import GamificationViewSet

app_name = 'gamification'

urlpatterns = [
    path('profile/', GamificationViewSet.as_view({'get': 'profile'})),
    path('leaderboard/', GamificationViewSet.as_view({'get': 'leaderboard'})),
    path('badges/', GamificationViewSet.as_view({'get': 'badges'})),
    path('stats/', GamificationViewSet.as_view({'get': 'stats'})),
]