# monitor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.site_monitoring, name='site_monitoring'),
    path('report/', views.generate_report, name='generate_report'),
    path('api/chart-data/', views.chart_data, name='chart_data'),
    path('metrics/', views.prometheus_metrics, name='prometheus_metrics'),
    path("api/sites/", views.get_websites, name="get_sites"),
    path("chart_data", views.chart_data, name="chart_data"),
    path('api/kpi/', views.kpi_summary, name='kpi_summary'),  # ✅ ten zostaw!
]
