from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gitdm.views import PatientViewSet
from encounters.views import EncounterViewSet
from laboratory.views import LabResultViewSet
from pharmacy.views import MedicationOrderViewSet
from references.views import ClinicalReferenceViewSet
from intelligence.views import AISummaryViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'encounters', EncounterViewSet)
router.register(r'labs', LabResultViewSet)
router.register(r'medications', MedicationOrderViewSet)
router.register(r'references', ClinicalReferenceViewSet)
router.register(r'ai-summaries', AISummaryViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]