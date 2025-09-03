"""
URL configuration for apimonitor project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/monitor/', include('monitor.urls')),
]