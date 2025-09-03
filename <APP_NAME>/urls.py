from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIDigestViewSet, HealthCheckResultViewSet, ServiceViewSet, health_summary

router = DefaultRouter()
router.register(r"monitor/services", ServiceViewSet)
router.register(r"monitor/results", HealthCheckResultViewSet, basename="results")
router.register(r"monitor/digests", AIDigestViewSet, basename="digests")

urlpatterns = [
    path("", include(router.urls)),
    path("monitor/health/summary", health_summary, name="health-summary"),
]

