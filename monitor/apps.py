from django.apps import AppConfig
from importlib import import_module

class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        try:
            start_task = import_module("monitor.periodic").start_ssh_monitoring_task
            start_task()
        except Exception as e:
            print("⛔️ Błąd inicjalizacji zadania SSH:", e)
