from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/metrics/", consumers.MetricsConsumer.as_asgi(), name="ws_metrics"),
    path("ws/ssh-metrics/", consumers.SSHMetricsConsumer.as_asgi(), name="ws_ssh_metrics"),
]
