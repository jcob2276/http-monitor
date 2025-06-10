from django.contrib import admin
from .models import MonitoredWebsite, MonitoringResult, SSHHost

@admin.register(MonitoredWebsite)
class MonitoredWebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'check_interval', 'last_status')
    search_fields = ('name', 'url')

@admin.register(MonitoringResult)
class MonitoringResultAdmin(admin.ModelAdmin):
    list_display = ('website', 'status_code', 'response_time', 'timestamp', 'is_up')
    list_filter = ('is_up', 'timestamp')
    search_fields = ('website__name',)

@admin.register(SSHHost)
class SSHHostAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'username', 'port')
    search_fields = ('hostname', 'username')
