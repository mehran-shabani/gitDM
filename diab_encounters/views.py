from rest_framework import generics
from .models import Encounter
from .serializers import EncounterSerializer
from records_versioning.utils import create_version
from ai_summarizer.tasks import generate_ai_summary

class EncounterListCreateView(generics.ListCreateAPIView):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    
    def perform_create(self, serializer):
        encounter = serializer.save()
        # Create version record
        create_version('Encounter', encounter.id, encounter.__dict__)
        # Trigger AI summary generation
        generate_ai_summary.delay(encounter.patient.id)

class EncounterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer