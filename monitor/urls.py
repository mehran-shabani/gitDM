"""URL configuration for monitoring app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ServiceViewSet, HealthCheckResultViewSet, AIDigestViewSet, health_summary_view

app_name = 'monitor'

# DRF Router
router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'results', HealthCheckResultViewSet, basename='healthcheckresult')
router.register(r'digests', AIDigestViewSet, basename='aidigest')

urlpatterns = [
    # DRF routes
    path('api/monitor/', include(router.urls)),
    
    # Custom endpoints
    path('api/monitor/health/summary/', health_summary_view, name='health-summary'),
]