from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PatientViewSet, EncounterViewSet, LabResultViewSet,
    MedicationOrderViewSet, ClinicalReferenceViewSet
)

router = SimpleRouter()
router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'encounters', EncounterViewSet, basename='encounters')
router.register(r'labs', LabResultViewSet, basename='labs')
router.register(r'meds', MedicationOrderViewSet, basename='meds')
router.register(r'refs', ClinicalReferenceViewSet, basename='refs')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
