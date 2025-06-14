import requests
from .models import MonitoringResult, Alert

def check_website(website):
    try:
        response = requests.get(website.url, timeout=10)
        is_up = response.status_code < 500
        MonitoringResult.objects.create(
            website=website,
            status_code=response.status_code,
            response_time=response.elapsed.total_seconds(),
            is_up=is_up
        )
    except Exception as e:
        MonitoringResult.objects.create(
            website=website,
            status_code=None,
            response_time=None,
            is_up=False
        )
        print(f"[{website.name}] Błąd: {e}")

    
    maybe_trigger_alert(website)


def maybe_trigger_alert(website):
    recent = MonitoringResult.objects.filter(website=website).order_by('-timestamp')[:3]
    if all(r.is_up is False for r in recent):
        existing = Alert.objects.filter(website=website, resolved=False).exists()
        if not existing:
            Alert.objects.create(
                website=website,
                message=f"{website.name} padła 3 razy pod rząd. Sprawdź usługę."
            )
            print(f"🚨 ALERT DLA {website.name} – padła 3x pod rząd")
