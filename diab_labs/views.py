from rest_framework import generics
from .models import Lab
from .serializers import LabSerializer
from records_versioning.utils import create_version
from ai_summarizer.tasks import generate_ai_summary

class LabListCreateView(generics.ListCreateAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabSerializer
    
    def perform_create(self, serializer):
        lab = serializer.save()
        # Create version record
        create_version('Lab', lab.id, lab.__dict__)
        # Trigger AI summary generation
        generate_ai_summary.delay(lab.patient.id)

class LabDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabSerializer