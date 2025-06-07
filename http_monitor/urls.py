from django.contrib import admin
from django.urls import path, include
from monitor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitor.urls')),
    path('', views.dashboard, name='dashboard'),
     path('', include('monitor.urls')),
]
