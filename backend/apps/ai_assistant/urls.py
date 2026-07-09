from django.urls import path
from .views import ChatViewSet

app_name = 'ai_assistant'

urlpatterns = [
    path('sessions/', ChatViewSet.as_view({'get': 'sessions'}), name='sessions'),
    path('send/', ChatViewSet.as_view({'post': 'send'}), name='send'),
    path('new-session/', ChatViewSet.as_view({'post': 'new_session'}), name='new-session'),
    path('messages/', ChatViewSet.as_view({'get': 'messages'}), name='messages'),
    path('delete-session/', ChatViewSet.as_view({'post': 'delete_session'}), name='delete-session'),
    path('suggestions/', ChatViewSet.as_view({'get': 'suggestions'}), name='suggestions'),
]