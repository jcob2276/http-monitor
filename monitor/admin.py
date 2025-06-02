from django.contrib import admin
from .models import MonitoredWebsite, MonitoringResult

admin.site.register(MonitoredWebsite)
admin.site.register(MonitoringResult)
