from .models import MonitoredWebsite, MonitoringResult
from .utils import check_website
from django_q.tasks import schedule
from django_q.models import Schedule
from .ssh_metrics import SSHMonitor
from datetime import datetime
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer




def check_all_websites(*args, **kwargs):
    from .models import MonitoredWebsite, MonitoringResult
    from .utils import check_website

    for site in MonitoredWebsite.objects.all():
        print(f"[{site.name}] Checking {site.url} ...")
        result = check_website(site)

        if result:
            MonitoringResult.objects.create(
                website=site,
                response_time=result["response_time"],
                status_code=result["status_code"]
            )


def test_redis_task():
    print("✅ Test Redis działa!")

from django_q.models import Schedule
from django_q.tasks import schedule


def check_all_ssh_hosts():
    for host in SSHHost.objects.all():
        monitor = SSHMonitor(host=host.hostname, username=host.username, password=host.password)
        try:
            data = monitor.collect_metrics()
            if data:
                SSHMetric.objects.create(
                    host=host,
                    cpu_percent=data["cpu_percent"],
                    ram_used=data["ram_used"],
                    ram_total=data["ram_total"],
                    timestamp=datetime.utcnow()
                )
                print(f"✅ SSH data saved for {host.hostname}")
        except Exception as e:
            print(f"❌ Błąd dla {host.hostname}: {e}")
            

def schedule_http_broadcast():
    if not Schedule.objects.filter(name="broadcast_http_metrics").exists():
        schedule(
            'monitor.tasks.broadcast_latest_http_metrics',
            name='broadcast_http_metrics',
            schedule_type=Schedule.MINUTES,   # Możesz dać SECONDS dla testu!
            minutes=1,
            repeat=None,
            q_options={'timeout': 30}
        )
        print("✅ Zaplanowano broadcast HTTP co minutę.")
    else:
        print("ℹ️ Harmonogram HTTP już istnieje.")



def schedule_ssh_checks():
    if not Schedule.objects.filter(name="check_ssh_hosts_every_minute").exists():
        schedule(
            'monitor.tasks.check_all_ssh_hosts',
            name='check_ssh_hosts_every_minute',
            schedule_type=Schedule.MINUTES,
            minutes=1,
            repeat=None,
            q_options={'timeout': 30}
        )
        print("✅ Zaplanowano harmonogram monitorowania SSH co minutę.")
    else:
        print("ℹ️ Harmonogram SSH już istnieje.")
        
        
        # monitor/tasks.py
from django.utils.timezone import localtime
def broadcast_latest_http_metrics(*args, **kwargs):
    from .models import MonitoringResult
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    latest = MonitoringResult.objects.select_related("website").order_by("-timestamp").first()
    if not latest:
        return

    data = {
        "timestamp": localtime(latest.timestamp).strftime('%H:%M:%S'),
        "response_time": latest.response_time,
        "is_up": latest.is_up,
        "url": latest.website.url,
        "website_id": latest.website.id
    }

    channel_layer = get_channel_layer()
    print("[WS_HTTP_BROADCAST]", data)
    async_to_sync(channel_layer.group_send)(
        "http_metrics_group",
        {
            "type": "send_http_metrics",
            "data": data
        }
    )

