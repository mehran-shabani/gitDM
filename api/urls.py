from django.urls import path
from patients_core.views import PatientListCreateView, PatientDetailView, patient_timeline
from diab_encounters.views import EncounterListCreateView, EncounterDetailView
from diab_labs.views import LabListCreateView, LabDetailView
from diab_medications.views import MedicationListCreateView, MedicationDetailView
from .views import export_patient

urlpatterns = [
    # Patient endpoints
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<uuid:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('patients/<uuid:pk>/timeline/', patient_timeline, name='patient-timeline'),
    
    # Encounter endpoints
    path('encounters/', EncounterListCreateView.as_view(), name='encounter-list-create'),
    path('encounters/<uuid:pk>/', EncounterDetailView.as_view(), name='encounter-detail'),
    
    # Lab endpoints
    path('labs/', LabListCreateView.as_view(), name='lab-list-create'),
    path('labs/<uuid:pk>/', LabDetailView.as_view(), name='lab-detail'),
    
    # Medication endpoints
    path('meds/', MedicationListCreateView.as_view(), name='medication-list-create'),
    path('meds/<uuid:pk>/', MedicationDetailView.as_view(), name='medication-detail'),
    
    # Export endpoint
    path('export/patient/<uuid:patient_id>/', export_patient, name='export-patient'),
]