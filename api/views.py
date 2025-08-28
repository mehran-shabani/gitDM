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
    MedicationOrderSerializer, ClinicalReferenceSerializer
)

SYSTEM_USER_ID = UUID(getattr(settings, 'SYSTEM_USER_ID'))


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        p = self.get_object()
        enc = Encounter.objects.filter(patient=p).order_by('-occurred_at')
        labs = LabResult.objects.filter(patient=p).order_by('-taken_at')
        meds = MedicationOrder.objects.filter(patient=p).order_by('-start_date')
        summaries = AISummary.objects.filter(patient=p).order_by('-created_at')[:5]
        return Response({
            'patient': PatientSerializer(p).data,
            'encounters': EncounterSerializer(enc, many=True).data,
            'labs': LabResultSerializer(labs, many=True).data,
            'medications': MedicationOrderSerializer(meds, many=True).data,
            'ai_summaries': [
                {
                    'resource_type': s.resource_type,
                    'resource_id': str(s.resource_id),
                    'summary': s.summary,
                    'created_at': s.created_at,
                } for s in summaries
            ]
        })


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=SYSTEM_USER_ID)


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer


class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer