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

from .models import SSHHost

from .models import (
    MonitoringResult, MonitoredWebsite, Alert, Notification, SSHMetric, SSHHost
)

@api_view(['GET'])
def ssh_hosts_api(request):
    hosts = SSHHost.objects.all().values('id', 'hostname')
    return Response(list(hosts))


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


def ssh_chart_data(request):
    host = request.GET.get('host')
    time_range = request.GET.get('range')

    now = timezone.now()

    if time_range == '5m':
        start_time = now - timedelta(minutes=5)
    elif time_range == '1h':
        start_time = now - timedelta(hours=1)
    elif time_range == '24h':
        start_time = now - timedelta(hours=24)
    else:
        return JsonResponse({'error': 'Niepoprawny zakres czasu'}, status=400)

    queryset = SSHMetric.objects.filter(host__hostname=host, timestamp__gte=start_time).order_by('timestamp')

    labels = [m.timestamp.strftime('%H:%M:%S') for m in queryset]
    cpu = [m.cpu_percent for m in queryset]
    ram = [(m.ram_used / m.ram_total * 100) for m in queryset]

    return JsonResponse({
        'labels': labels,
        'cpu': cpu,
        'ram': ram
    })

# --------------------------
# API: KPI, STATUSY, ALERTY
# --------------------------

from django.http import JsonResponse
from django.utils.timezone import now, timedelta
from .models import SSHMetric

def ssh_metrics_api(request):
    hostname = request.GET.get('hostname')
    time_range = request.GET.get('range', '5')

    if not hostname:
        return JsonResponse({'error': 'Brak hosta'}, status=400)

    now_time = now()
    if time_range == '5m':
        since = now_time - timedelta(minutes=5)
    elif time_range == '1h':
        since = now_time - timedelta(hours=1)
    else:
        since = now_time - timedelta(hours=24)

    data = SSHMetric.objects.filter(
        host__hostname=hostname,
        timestamp__gte=since
    ).order_by('timestamp')

    response_data = [
        {
            'timestamp': metric.timestamp.isoformat(),
            'cpu_percent': metric.cpu_percent,
            'ram_used': metric.ram_used,
            'ram_total': metric.ram_total,
        }
        for metric in data
    ]

    return JsonResponse(response_data, safe=False)



def kpi_summary(request):
    host = request.GET.get('host')
    http_count = MonitoredWebsite.objects.count()
    ssh_count = SSHMetric.objects.values('host').distinct().count()
    active_services = http_count + ssh_count

    cpu_avg = 0.0
    ram_avg = 0
    if host:
        recent_ssh = SSHMetric.objects.filter(host__hostname=host).order_by('-timestamp')[:20]
        cpu_avg = recent_ssh.aggregate(avg_cpu=Avg('cpu_percent'))['avg_cpu'] or 0.0
        ram_avg = recent_ssh.aggregate(avg_ram=Avg('ram_used'))['avg_ram'] or 0
    else:
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






