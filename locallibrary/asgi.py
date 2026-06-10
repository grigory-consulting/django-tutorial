"""
ASGI config for locallibrary project.

Routet je nach Protokoll:
- normale HTTP-Anfragen -> Djangos ASGI-Anwendung (Views wie gewohnt)
- WebSocket-Anfragen    -> Channels-Routing aus catalog/routing.py
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "locallibrary.settings")

# Django zuerst initialisieren, dann erst Channels-Importe (Reihenfolge wichtig).
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from catalog.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
