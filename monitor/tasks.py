# monitor/tasks.py

def check_all_websites():
    from .models import MonitoredWebsite
    from .utils import check_website

    for site in MonitoredWebsite.objects.all():
        print(f"[{site.name}] Checking {site.url} ...")
        check_website(site)


def test_redis_task():
    print("✅ Test Redis działa!")
