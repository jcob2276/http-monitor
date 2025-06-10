# monitor/urls.py
from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include  # ⬅️ TO MUSI BYĆ!


urlpatterns = [
    path('', views.site_monitoring, name='site_monitoring'),
    path('api/chart-data/', views.chart_data, name='chart_data'),
    path("api/sites/", views.get_websites, name="get_sites"),
    path('api/kpi/', views.kpi_summary, name='kpi_summary'),  
    path("api/notifications/", views.notifications_api, name="notifications_api"),
    path("api/statuses/", views.service_statuses, name="service_statuses"),
    path("api/alerts/", views.alerts_api, name="alerts_api"),
    path("api/ssh-hosts/", views.ssh_hosts_api, name="ssh_hosts_api"),
            ]
