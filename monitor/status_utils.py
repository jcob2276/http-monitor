# monitor/status_utils.py

from monitor.models import MonitoredWebsite, Alert, MonitoringResult, Notification
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta

# --------------------------------------------
# Prosta logika: czy strona działa (is_up)
# --------------------------------------------

def update_status_from_availability(website, is_up):
    """
    Aktualizuje status serwisu na podstawie binarnego is_up.
    """
    new_status = "healthy" if is_up else "critical"

    if website.last_status != new_status:
        Alert.objects.create(
            website=website,
            message=f"Zmiana statusu: {website.last_status} → {new_status}"
        )
        print(f"⚠️ ALERT: {website.name} zmienił status z {website.last_status} na {new_status}")

    website.last_status = new_status
    website.save()

# --------------------------------------------
# Rozbudowana logika: analiza ostatnich pomiarów
# --------------------------------------------

def evaluate_status_from_recent_checks(website, minutes=5):
    """
    Analizuje ostatnie wyniki monitoringu, aby określić stan usługi:
    - critical: < 80% up lub > 1000 ms
    - warning: < 95% up lub > 500 ms
    - healthy: reszta
    """
    now = timezone.now()
    since = now - timedelta(minutes=minutes)

    checks = MonitoringResult.objects.filter(website=website, timestamp__gte=since)
    if not checks.exists():
        return

    up_ratio = checks.filter(is_up=True).count() / checks.count()
    avg_response = checks.aggregate(Avg("response_time"))["response_time__avg"] or 0

    if up_ratio < 0.80 or avg_response > 1000:
        current_status = "critical"
    elif up_ratio < 0.95 or avg_response > 500:
        current_status = "warning"
    else:
        current_status = "healthy"

    # Jeśli status się zmienił, zapisz i wygeneruj powiadomienie
    if website.last_status != current_status:
        Notification.objects.create(
            service_name=website.name,
            level=current_status if current_status != "healthy" else "info",
            message=f"Status usługi {website.name} zmienił się na {current_status}"
        )
        website.last_status = current_status
        website.save()
