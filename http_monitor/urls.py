# http_monitor/urls.py
from django.contrib import admin
from django.urls import path, include  # ← NIE ZAPOMNIJ O TYM

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitor.urls')),
]
