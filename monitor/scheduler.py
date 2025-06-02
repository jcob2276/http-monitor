import time
import threading
from .models import MonitoredWebsite
from .utils import check_website

# Słownik monitorowanych stron {id: thread}
running_threads = {}

def monitor_target(website):
    while True:
        print(f"[{website.name}] Checking {website.url} ...")
        check_website(website)
        time.sleep(website.check_interval)

def start_scheduler(poll_interval=30):
    print("🔄 Uruchamiam dynamiczny scheduler...")

    while True:
        websites = MonitoredWebsite.objects.all()
        for site in websites:
            if site.id not in running_threads:
                print(f"▶️ Dodaję nowy wątek dla: {site.name}")
                t = threading.Thread(target=monitor_target, args=(site,))
                t.daemon = True
                t.start()
                running_threads[site.id] = t
        time.sleep(poll_interval)
