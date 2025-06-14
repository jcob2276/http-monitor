import os
from pathlib import Path

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.auth import AuthMiddlewareStack

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'http_monitor.settings')
django.setup()

import monitor.routing  # <- musi być PO setup()

BASE_DIR = Path(__file__).resolve().parent.parent

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(monitor.routing.websocket_urlpatterns)
    ),
})


print("✅ Routing z monitor.routing.websocket_urlpatterns:", monitor.routing.websocket_urlpatterns)
