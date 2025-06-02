from django.urls import path
from .views import site_monitoring, generate_report, chart_data, prometheus_metrics
from . import views


urlpatterns = [
    path('', views.site_monitoring, name='site_monitoring'),
    path('report/', views.generate_report, name='generate_report'),
    path('api/chart-data/', views.chart_data, name='chart_data'),
    path('metrics/', views.prometheus_metrics, name='prometheus_metrics'),
    path('generate-report/', generate_report, name='generate_report'),


]
