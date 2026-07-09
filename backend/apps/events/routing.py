# apps/events/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/events/', consumers.EventStreamConsumer.as_asgi()),
    path('ws/events/<str:org_id>/', consumers.EventStreamConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]