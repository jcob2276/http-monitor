# monitor/consumers.py

import asyncio
import json
import time
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import MonitoringResult, SSHHost
from .ssh_metrics import SSHMonitor


class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("http_metrics_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("http_metrics_group", self.channel_name)

    async def send_http_metrics(self, event):
        await self.send(text_data=json.dumps(event["data"]))


class SSHMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_streaming = True
        self.stream_task = asyncio.create_task(self.stream_metrics_loop())

    async def disconnect(self, close_code):
        self.keep_streaming = False
        if hasattr(self, "stream_task"):
            self.stream_task.cancel()

    async def stream_metrics_loop(self):
        while self.keep_streaming:
            try:
                hosts = await sync_to_async(list)(SSHHost.objects.all())
            except Exception as e:
                await self.send(text_data=json.dumps({"error": f"Błąd ładowania hostów: {str(e)}"}))
                await asyncio.sleep(10)
                continue

            for host in hosts:
                ssh = SSHMonitor(
                    host=host.hostname,
                    username=host.username,
                    password=host.password,
                    port=host.port
                )
                try:
                    metrics = ssh.collect_metrics()
                    await self.send(text_data=json.dumps({
                        "host": host.hostname,
                        "cpu": metrics["cpu_percent"],
                        "ram_used": metrics["ram_used"],
                        "ram_total": metrics["ram_total"],
                        "timestamp": time.strftime("%H:%M:%S")
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "host": host.hostname,
                        "error": f"Błąd pobierania danych: {str(e)}"
                    }))
                finally:
                    ssh.close()

            await asyncio.sleep(10)
