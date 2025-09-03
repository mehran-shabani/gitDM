from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from api.views_export import export_patient
from encounters.views import EncounterViewSet
from gitdm.views import PatientViewSet
from intelligence.views import (
    AISummaryViewSet,
    AnomalyDetectionViewSet,
    BaselineMetricsViewSet,
    PatternAlertViewSet,
    PatternAnalysisViewSet,
)
from laboratory.views import LabResultViewSet
from notifications.views import ClinicalAlertViewSet, NotificationViewSet
from pharmacy.views import MedicationOrderViewSet
from references.views import ClinicalReferenceViewSet
from reminders.views import ReminderViewSet
from versioning import views as version_views

from .views import health

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'encounters', EncounterViewSet, basename='encounters')
router.register(r'labs', LabResultViewSet)
router.register(r'meds', MedicationOrderViewSet)
router.register(r'refs', ClinicalReferenceViewSet)
router.register(r'ai-summaries', AISummaryViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'alerts', ClinicalAlertViewSet, basename='clinicalalert')
router.register(r'pattern-analyses', PatternAnalysisViewSet)
router.register(r'anomaly-detections', AnomalyDetectionViewSet)
router.register(r'pattern-alerts', PatternAlertViewSet)
router.register(r'baseline-metrics', BaselineMetricsViewSet)

router.register(r'reminders', ReminderViewSet, basename='reminder')



def api_root_view(request):  # noqa: ANN001, ANN201
    return JsonResponse({"status": "ok"})

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', include('gateway.simple_patterns')),
    path('', api_root_view, name='api-root'),
    path('health/', health, name='api-health'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'),
    path('versions/<str:resource_type>/<str:resource_id>/',
     version_views.versions_list),
    path('versions/<str:resource_type>/<str:resource_id>/revert/',
     version_views.versions_revert),
    path('export/patient/<str:pk>/', export_patient, name='export_patient'),
    path('analytics/', include('analytics.urls')),
]
