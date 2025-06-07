def hello_world():
    print("👋 Hello from Django Q!")


def check_all_websites():
    from .models import MonitoredWebsite  # ← importujemy dopiero tutaj!
    from .utils import check_website

    for site in MonitoredWebsite.objects.all():  # 👈 Nie używamy active=True
        print(f"[{site.name}] Checking {site.url} ...")
        check_website(site)
