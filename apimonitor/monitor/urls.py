"""
URL configuration for monitor app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from monitor.views import (
    ServiceViewSet,
    HealthCheckResultViewSet,
    AIDigestViewSet,
    HealthSummaryView
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'results', HealthCheckResultViewSet, basename='healthcheckresult')
router.register(r'digests', AIDigestViewSet, basename='aidigest')

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Custom health summary endpoint
    path('health/summary/', HealthSummaryView.as_view({'get': 'list'}), name='health-summary'),
]