from django.urls import path, include
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_safe
from django.views.decorators.cache import never_cache
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PatientViewSet, EncounterViewSet, LabResultViewSet,
    MedicationOrderViewSet, ClinicalReferenceViewSet
)
from .root_view import api_root


@never_cache
@require_safe
def health(_request: HttpRequest) -> JsonResponse:
    """Health check endpoint: Returns JSON {"status": "ok"} with HTTP 200. No caching."""
    return JsonResponse({"status": "ok"})

router = SimpleRouter()
router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'encounters', EncounterViewSet, basename='encounters')
router.register(r'labs', LabResultViewSet, basename='labs')
router.register(r'meds', MedicationOrderViewSet, basename='meds')
router.register(r'refs', ClinicalReferenceViewSet, basename='refs')

urlpatterns = [
    path('', api_root, name='api-root'),
    path('health/', health, name='api-health'),
    path('', include(router.urls)),
    # JWT login endpoints (also aliased in root urls)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Convenience: expose also under /api prefix when included at project root
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'),
]
