from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientAnalyticsViewSet,
    DoctorAnalyticsViewSet,
    SystemAnalyticsViewSet,
    ReportViewSet,
    DashboardViewSet
)

router = DefaultRouter()
router.register(r'patient-analytics', PatientAnalyticsViewSet, basename='patient-analytics')
router.register(r'doctor-analytics', DoctorAnalyticsViewSet, basename='doctor-analytics')
router.register(r'system-analytics', SystemAnalyticsViewSet, basename='system-analytics')
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]