from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from collections import defaultdict
from .models import MonitoringResult, MonitoredWebsite, Alert



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

    return render(request, 'monitor/site_monitoring.html', {
        'results': results,
        'websites': websites,
        'selected_website': selected_website,
        'avg_response': round(avg_response, 2),
        'uptime_percent': round(uptime_percent, 1),
        'total_checks': total_checks,
        'active_alerts': active_alerts,
    })


from django.http import HttpResponse
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


def chart_data(request):
    website_id = request.GET.get('website_id')

    if not website_id:
        return JsonResponse({'error': 'Brak website_id'}, status=400)

    try:
        website = MonitoredWebsite.objects.get(id=website_id)
    except MonitoredWebsite.DoesNotExist:
        return JsonResponse({'error': 'Nie znaleziono strony'}, status=404)

    results = MonitoringResult.objects.filter(
        website=website
    ).order_by('-timestamp')[:50][::-1]

    data = {
        'labels': [r.timestamp.strftime("%H:%M:%S") for r in results],
        'response_times': [round(r.response_time or 0, 2) for r in results],
        'label': website.url
    }

    return JsonResponse(data)

