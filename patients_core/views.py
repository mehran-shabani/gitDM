from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Patient
from .serializers import PatientSerializer
from ai_summarizer.models import AISummary
from ai_summarizer.serializers import AISummarySerializer
from diab_encounters.models import Encounter
from diab_labs.models import Lab
from diab_medications.models import Medication
from records_versioning.utils import create_version

class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    
    def perform_create(self, serializer):
        patient = serializer.save()
        # Create version record
        create_version('Patient', patient.id, serializer.data)

class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

@api_view(['GET'])
def patient_timeline(request, pk):
    patient = Patient.objects.get(pk=pk)
    
    # Get all related data
    encounters = patient.encounters.all().order_by('-occurred_at')
    labs = patient.labs.all().order_by('-taken_at')
    medications = patient.medications.all().order_by('-start_date')
    ai_summaries = patient.ai_summaries.all().order_by('-created_at')
    
    data = {
        'patient': PatientSerializer(patient).data,
        'encounters': [{'id': str(e.id), 'occurred_at': e.occurred_at, 'subjective': e.subjective} for e in encounters],
        'labs': [{'id': str(l.id), 'loinc': l.loinc, 'value': l.value, 'taken_at': l.taken_at} for l in labs],
        'medications': [{'id': str(m.id), 'name': m.name, 'dose': m.dose, 'start_date': m.start_date} for m in medications],
        'ai_summaries': AISummarySerializer(ai_summaries, many=True).data,
    }
    
    return Response(data)