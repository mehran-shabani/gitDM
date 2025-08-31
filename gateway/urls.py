from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from gitdm.views import PatientViewSet
from encounters.views import EncounterViewSet
from laboratory.views import LabResultViewSet
from pharmacy.views import MedicationOrderViewSet
from references.views import ClinicalReferenceViewSet
from intelligence.views import AISummaryViewSet
from .views import health
from api.views_export import export_patient
from versioning import views as version_views
from django.http import JsonResponse

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'encounters', EncounterViewSet)
router.register(r'labs', LabResultViewSet)
router.register(r'meds', MedicationOrderViewSet)
router.register(r'refs', ClinicalReferenceViewSet)
router.register(r'ai-summaries', AISummaryViewSet)


def api_root_view(request):
    return JsonResponse({"status": "ok"})

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', api_root_view, name='api-root'),
    path('health/', health, name='api-health'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'),
    path('versions/<str:resource_type>/<str:resource_id>/', version_views.versions_list),
    path('versions/<str:resource_type>/<str:resource_id>/revert/', version_views.versions_revert),
    path('export/patient/<str:pk>/', export_patient, name='export_patient'),
]