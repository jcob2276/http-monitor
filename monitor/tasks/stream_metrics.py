# monitor/tasks/stream_metrics.py
import asyncio
import json
from channels.layers import get_channel_layer

async def stream_metrics():
    channel_layer = get_channel_layer()
    while True:
        data = {
            "cpu": 23,  # <- na razie na sztywno
            "ram": 62,
            "disk": 88,
        }
        await channel_layer.group_send(
            "metrics_group",
            {
                "type": "send.metrics",
                "data": data
            }
        )
        await asyncio.sleep(5)
