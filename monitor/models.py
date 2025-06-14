from django.db import models

# ============================
# 🌐 HTTP Monitoring
# ============================

class MonitoredWebsite(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    check_interval = models.IntegerField(default=60)
    last_status = models.CharField(max_length=10, default='unknown')  # "healthy", "warning", "critical"

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


# ============================
# 💻 SSH Monitoring
# ============================

class SSHHost(models.Model):
    hostname = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    port = models.IntegerField(default=22)

    def __str__(self):
        return f"{self.username}@{self.hostname}"

class SSHMetric(models.Model):
    host = models.ForeignKey(SSHHost, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_percent = models.FloatField()
    ram_used = models.IntegerField()
    ram_total = models.IntegerField()

    def __str__(self):
        return f"{self.host} @ {self.timestamp}"


# ============================
# 🔔 Notyfikacje i alerty
# ============================

class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Informacja'),
        ('warning', 'Ostrzeżenie'),
        ('critical', 'Krytyczny'),
    ]

    service_name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.level.upper()}] {self.service_name}: {self.message}"
