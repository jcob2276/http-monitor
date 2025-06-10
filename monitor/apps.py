from django.apps import AppConfig
import os


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        if "runserver" in os.sys.argv:  # tylko gdy uruchamiasz serwer
            try:
                from .periodic import start_ssh_monitoring_task
                start_ssh_monitoring_task()
            except ImportError:
                print("⚠️ ssh_collector nie istnieje – pomijam zadanie.")
            except Exception as e:
                print("⛔️ Błąd inicjalizacji zadania SSH:", e)
