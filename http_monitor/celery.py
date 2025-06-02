from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Ustawienia Django jako źródło konfiguracji
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'http_monitor.settings')

app = Celery('http_monitor')

# 🔧 RĘCZNIE ustawiamy broker
app.conf.broker_url = 'redis://localhost:6379/0'

# Wczytanie ustawień z settings.py z prefiksem CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatyczne wykrywanie tasków
app.autodiscover_tasks()
