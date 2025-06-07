from monitor.models import UptimeCheck
from django.utils.timezone import now
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import json

class MetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.send_task = asyncio.create_task(self.send_metrics())

    async def disconnect(self, close_code):
        if hasattr(self, 'send_task'):
            self.send_task.cancel()

    async def send_metrics(self):
        while True:
            latest = UptimeCheck.objects.select_related('website').order_by('-timestamp').first()

            if latest:
                data = {
                    "timestamp": latest.timestamp.strftime('%H:%M:%S'),
                    "response_time": latest.response_time,
                    "is_up": latest.is_up,
                    "url": latest.website.url,
                    "website_id": latest.website.id  # ⬅️ TO DODAJ
                }
            else:
                data = {
                    "timestamp": now().strftime('%H:%M:%S'),
                    "response_time": 0,
                    "is_up": False,
                    "url": "brak danych",
                    "website_id": None
                }

            await self.send(text_data=json.dumps(data))
            await asyncio.sleep(5)
