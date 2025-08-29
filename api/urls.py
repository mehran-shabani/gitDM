from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PatientViewSet, EncounterViewSet, LabResultViewSet,
    MedicationOrderViewSet, ClinicalReferenceViewSet
)
from .root_view import api_root

router = SimpleRouter()
router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'encounters', EncounterViewSet, basename='encounters')
router.register(r'labs', LabResultViewSet, basename='labs')
router.register(r'meds', MedicationOrderViewSet, basename='meds')
router.register(r'refs', ClinicalReferenceViewSet, basename='refs')

urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
    # JWT login endpoints (also aliased in root urls)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Convenience: expose also under /api prefix when included at project root
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'),
]
