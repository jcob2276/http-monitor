from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from collections import defaultdict
from .models import MonitoringResult, MonitoredWebsite, Alert
from django.http import HttpResponse
from monitor.models import SSHMetric
from django.http import JsonResponse
from django.db.models import Avg
from monitor.models import MonitoredWebsite, SSHMetric

def dashboard(request):
    return HttpResponse("Hello from dashboard!")



# Widok do monitorowania stron (HTML)
def site_monitoring(request):
    website_id = request.GET.get('website_id')
    selected_website = None
    results = []
    avg_response = 0
    uptime_percent = 0
    total_checks = 0

    websites = MonitoredWebsite.objects.all()
    active_alerts = Alert.objects.filter(resolved=False).order_by('-created_at')  # ⬅️ przesunięte wyżej

    print(">>> Websites loaded:", list(websites))

    if website_id:
        selected_website = MonitoredWebsite.objects.filter(id=website_id).first()
        if selected_website:
            results = MonitoringResult.objects.filter(
                website=selected_website
            ).order_by('-timestamp')[:10]

            # KPI: dane z ostatnich 24h
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



from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import MonitoringResult



def generate_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monitoring_report.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Tytuł
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 50, "📊 Raport monitorowania stron HTTP")

    # Nagłówki kolumn
    def draw_headers(y):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "URL")
        p.drawString(230, y, "Status")
        p.drawString(290, y, "Czas [s]")
        p.drawString(370, y, "Data")

    y = height - 80
    draw_headers(y)

    # Dane
    p.setFont("Helvetica", 10)
    y -= 20
    results = MonitoringResult.objects.select_related('website').order_by('-timestamp')[:100]

    for result in results:
        url = result.website.url[:35] if result.website and result.website.url else "Brak"
        status = result.status_code if result.status_code is not None else "-"
        response_time = f"{result.response_time:.2f}" if result.response_time is not None else "-"
        timestamp = result.timestamp.strftime("%Y-%m-%d %H:%M") if result.timestamp else "-"

        p.drawString(50, y, url)
        p.drawString(230, y, str(status))
        p.drawString(290, y, response_time)
        p.drawString(370, y, timestamp)

        y -= 18
        if y < 60:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width / 2, y, "📊 Raport monitorowania stron HTTP (kontynuacja)")
            y -= 30
            draw_headers(y)
            y -= 20
            p.setFont("Helvetica", 10)

    p.save()
    return response


def prometheus_metrics(request):
    output = []

    websites = MonitoredWebsite.objects.all()

    for website in websites:
        latest = MonitoringResult.objects.filter(website=website).order_by('-timestamp').first()

        if not latest:
            continue  # brak danych, pomiń

        url = website.url
        response_time = latest.response_time or 0
        is_up = 1 if latest.is_up else 0

        output.append(f'http_response_time_seconds{{url="{url}"}} {response_time}')
        output.append(f'http_up{{url="{url}"}} {is_up}')

    return HttpResponse("\n".join(output), content_type="text/plain")

def get_websites(request):
    websites = MonitoredWebsite.objects.all().values("id", "name")
    return JsonResponse(list(websites), safe=False)

# views.py
from django.http import JsonResponse
from .models import SSHMetric

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



from monitor.models import MonitoringResult

def kpi_summary(request):
    from django.utils import timezone
    from datetime import timedelta

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
    'status_codes': [r.status_code or 0 for r in results],  # 👈 DODAJ TO
    'label': website.url
}


    return JsonResponse(data)

