from django.core.management.base import BaseCommand
from monitor.scheduler import start_scheduler
import time

class Command(BaseCommand):
    help = 'Uruchamia monitorowanie wszystkich stron z indywidualnym interwałem.'

    def handle(self, *args, **kwargs):
        start_scheduler()
        while True:
            time.sleep(60)  # główny wątek musi żyć
