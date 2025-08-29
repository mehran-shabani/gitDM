from uuid import UUID
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from clinical_refs.models import ClinicalReference
from ai_summarizer.models import AISummary
from .serializers import (
    PatientSerializer, EncounterSerializer, LabResultSerializer,
    MedicationOrderSerializer, ClinicalReferenceSerializer, AISummarySerializer
)

SYSTEM_USER_ID = UUID(getattr(settings, 'SYSTEM_USER_ID'))


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        p = self.get_object()
        # Limit results to prevent performance issues
        limit = int(request.query_params.get('limit', 100))
        limit = min(limit, 500)  # Max 500 items per type
        
        enc = Encounter.objects.filter(patient=p).order_by('-occurred_at')[:limit]
        labs = LabResult.objects.filter(patient=p).order_by('-taken_at')[:limit]
        meds = MedicationOrder.objects.filter(patient=p).order_by('-start_date')[:limit]
        summaries = AISummary.objects.filter(patient=p).order_by('-created_at')[:5]
        
        return Response({
            'patient': PatientSerializer(p).data,
            'encounters': EncounterSerializer(enc, many=True).data,
            'labs': LabResultSerializer(labs, many=True).data,
            'medications': MedicationOrderSerializer(meds, many=True).data,
            'ai_summaries': AISummarySerializer(summaries, many=True).data
        })


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer

    def perform_create(self, serializer):
        # Use the authenticated user if available, otherwise use system user
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            serializer.save(created_by=user)
        else:
            # Fallback to system user ID - this should ideally be a proper User instance
            serializer.save(created_by_id=SYSTEM_USER_ID)


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer


class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer
