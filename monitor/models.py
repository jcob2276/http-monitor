from django.db import models

class MonitoredWebsite(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    check_interval = models.IntegerField(default=60)  # w sekundach

    def __str__(self):
        return self.name

class MonitoringResult(models.Model):
    website = models.ForeignKey(MonitoredWebsite, on_delete=models.CASCADE, related_name='results')
    status_code = models.IntegerField(null=True)
    response_time = models.FloatField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_up = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.website.name} - {self.timestamp}"

class Alert(models.Model):
    website = models.ForeignKey(MonitoredWebsite, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    message = models.TextField()

    def __str__(self):
        return f"ALERT: {self.website.name} @ {self.created_at}"

class UptimeCheck(models.Model):
    website = models.ForeignKey(MonitoredWebsite, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField()
    is_up = models.BooleanField()
