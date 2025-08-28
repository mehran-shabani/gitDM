from rest_framework import generics
from .models import Medication
from .serializers import MedicationSerializer
from records_versioning.utils import create_version
from ai_summarizer.tasks import generate_ai_summary

class MedicationListCreateView(generics.ListCreateAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    
    def perform_create(self, serializer):
        medication = serializer.save()
        # Create version record
        create_version('Medication', medication.id, medication.__dict__)
        # Trigger AI summary generation
        generate_ai_summary.delay(medication.patient.id)

class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer