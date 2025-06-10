# monitor/consumers.py

import asyncio
import json
import time
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import UptimeCheck, SSHHost
from .ssh_metrics import SSHMonitor


class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.send_task = asyncio.create_task(self.send_metrics())

    async def disconnect(self, close_code):
        if hasattr(self, 'send_task'):
            self.send_task.cancel()

    async def send_metrics(self):
        while True:
            latest = await sync_to_async(
                lambda: UptimeCheck.objects.select_related('website').order_by('-timestamp').first()
            )()

            data = {
                "timestamp": latest.timestamp.strftime('%H:%M:%S') if latest else now().strftime('%H:%M:%S'),
                "response_time": latest.response_time if latest else 0,
                "is_up": latest.is_up if latest else False,
                "url": latest.website.url if latest else "brak danych",
                "website_id": latest.website.id if latest else None
            }

            await self.send(text_data=json.dumps(data))
            await asyncio.sleep(5)


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
