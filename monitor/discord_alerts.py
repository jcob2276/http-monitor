# monitor/discord_alerts.py
import requests
from django.conf import settings

def send_discord_alert(message):
    webhook_url = settings.DISCORD_WEBHOOK_URL
    data = {"content": f"🚨 {message}"}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"❌ Discord webhook error: {e}")
