# Refactored version of views.py with logical sections and cleaned imports

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from collections import defaultdict

from rest_framework.decorators import api_view
from rest_framework.response import Response

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from django_q.tasks import async_task

from .models import (
    MonitoringResult, MonitoredWebsite, Alert, Notification, SSHMetric, SSHHost
)


# --------------------------
# DASHBOARD (HTML VIEWS)
# --------------------------

def site_monitoring(request):
    website_id = request.GET.get('website_id')
    selected_website = None
    results = []
    avg_response = 0
    uptime_percent = 0
    total_checks = 0

    websites = MonitoredWebsite.objects.all()
    active_alerts = Alert.objects.filter(resolved=False).order_by('-created_at')

    if website_id:
        selected_website = MonitoredWebsite.objects.filter(id=website_id).first()
        if selected_website:
            results = MonitoringResult.objects.filter(
                website=selected_website
            ).order_by('-timestamp')[:10]

            last_24h = timezone.now() - timedelta(hours=24)
            recent = MonitoringResult.objects.filter(
                website=selected_website,
                timestamp__gte=last_24h
            )
            total_checks = recent.count()
            avg_response = recent.aggregate(Avg('response_time'))['response_time__avg'] or 0
            uptime = recent.filter(is_up=True).count()
            uptime_percent = (uptime / total_checks * 100) if total_checks > 0 else 0

    return render(request, 'monitor/base.html', {
        'results': results,
        'websites': websites,
        'selected_website': selected_website,
        'avg_response': round(avg_response, 2),
        'uptime_percent': round(uptime_percent, 1),
        'total_checks': total_checks,
        'active_alerts': active_alerts,
    })


# --------------------------
# API: HOSTY I WYKRESY
# --------------------------

@api_view(['GET'])
def ssh_hosts_api(request):
    hosts = SSHHost.objects.all().values('hostname')
    return Response(list(hosts))

def chart_data(request):
    website_id = request.GET.get('website_id')
    range_param = request.GET.get('range', '5m')

    if not website_id:
        return JsonResponse({'error': 'Brak website_id'}, status=400)

    try:
        website = MonitoredWebsite.objects.get(id=website_id)
    except MonitoredWebsite.DoesNotExist:
        return JsonResponse({'error': 'Nie znaleziono strony'}, status=404)

    now = timezone.now()
    if range_param == '5m':
        since = now - timedelta(minutes=5)
    elif range_param == '1h':
        since = now - timedelta(hours=1)
    elif range_param == '24h':
        since = now - timedelta(hours=24)
    else:
        since = now - timedelta(minutes=5)

    results = MonitoringResult.objects.filter(
        website=website,
        timestamp__gte=since
    ).order_by('-timestamp')[:100][::-1]

    data = {
        'labels': [r.timestamp.strftime("%H:%M:%S") for r in results],
        'response_times': [round(r.response_time or 0, 2) for r in results],
        'status_codes': [r.status_code or 0 for r in results],
        'label': website.url
    }
    return JsonResponse(data)

def ssh_metrics_view(request):
    host = request.GET.get("host", None)
    if not host:
        return JsonResponse({"error": "No host provided"}, status=400)

    metrics = SSHMetric.objects.filter(host=host).order_by('-timestamp')[:30][::-1]
    data = {
        "timestamps": [m.timestamp.strftime("%H:%M:%S") for m in metrics],
        "cpu": [m.cpu_percent for m in metrics],
        "ram_used": [m.ram_used for m in metrics],
        "ram_total": [m.ram_total for m in metrics],
    }
    return JsonResponse(data)


def get_websites(request):
    websites = MonitoredWebsite.objects.all().values("id", "name")
    return JsonResponse(list(websites), safe=False)


# --------------------------
# API: KPI, STATUSY, ALERTY
# --------------------------

def kpi_summary(request):
    http_count = MonitoredWebsite.objects.count()
    ssh_count = SSHMetric.objects.values('host').distinct().count()
    active_services = http_count + ssh_count

    recent_ssh = SSHMetric.objects.order_by('-timestamp')[:20]
    cpu_avg = recent_ssh.aggregate(avg_cpu=Avg('cpu_percent'))['avg_cpu'] or 0.0
    ram_avg = recent_ssh.aggregate(avg_ram=Avg('ram_used'))['avg_ram'] or 0

    last_24h = timezone.now() - timedelta(hours=24)
    uptime_checks = MonitoringResult.objects.filter(timestamp__gte=last_24h)
    uptime_total = uptime_checks.count()
    uptime_up = uptime_checks.filter(is_up=True).count()
    uptime_avg = (uptime_up / uptime_total * 100) if uptime_total > 0 else 0.0

    return JsonResponse({
        "active_services": active_services,
        "cpu_avg": round(cpu_avg, 1),
        "ram_avg": int(ram_avg),
        "uptime_avg": round(uptime_avg, 1),
    })

def service_statuses(request):
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    websites = MonitoredWebsite.objects.all()
    services = []

    for site in websites:
        results = MonitoringResult.objects.filter(website=site, timestamp__gte=last_24h)
        up_count = results.filter(is_up=True).count()
        total = results.count()
        uptime = (up_count / total * 100) if total else 0
        last_response = results.order_by('-timestamp').first()

        services.append({
            "name": site.name,
            "uptime": round(uptime, 1),
            "response_time": round(last_response.response_time, 2) if last_response else "N/A",
            "status": site.last_status
        })

    return JsonResponse(services, safe=False)

def notifications_api(request):
    data = Notification.objects.filter(resolved=False).order_by('-created_at')[:10].values(
        'level', 'service_name', 'message', 'created_at'
    )
    return JsonResponse(list(data), safe=False)

def alerts_api(request):
    alerts = Alert.objects.order_by('-created_at').values("message", "created_at")[:10]
    return JsonResponse(list(alerts), safe=False)


# --------------------------
# LOGIKA STATUSU USŁUGI
# --------------------------

def evaluate_status_and_notify(website):
    now = timezone.now()
    since = now - timedelta(minutes=5)
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

    if website.last_status != current_status:
        Notification.objects.create(
            service_name=website.name,
            level=current_status if current_status != "healthy" else "info",
            message=f"Status usługi {website.name} zmienił się na {current_status}"
        )
        website.last_status = current_status
        website.save()




