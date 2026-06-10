from django.urls import path

from . import consumers

# WebSocket-Routen (analog zu urlpatterns, aber fuer das ws-Protokoll).
websocket_urlpatterns = [
    path("ws/checklist/", consumers.ChecklistConsumer.as_asgi()),
]
