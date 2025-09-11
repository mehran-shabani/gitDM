from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import LabResult
from .serializers import LabResultSerializer
from security.mixins import OwnedByCurrentDoctorQuerysetMixin
from security.permissions import IsOwnerDoctorOrReadOnly


class LabResultViewSet(OwnedByCurrentDoctorQuerysetMixin, viewsets.ModelViewSet):
    queryset = LabResult.objects.select_related('patient', 'encounter').order_by('-taken_at')
    serializer_class = LabResultSerializer
    permission_classes = [IsOwnerDoctorOrReadOnly]

    def perform_create(self, serializer) -> None:
        user = self.request.user
        self.enforce_patient_ownership(serializer, "You do not have permission to add records for this patient.")
        patient = serializer.validated_data.get("patient")
        encounter = serializer.validated_data.get("encounter")
        if encounter is not None:
            enc_patient = getattr(encounter, "patient", None)
            if enc_patient is not None and enc_patient != patient:
                raise PermissionDenied("Encounter does not belong to the selected patient.")
            if enc_patient is not None and getattr(enc_patient, "primary_doctor", None) != user:
                raise PermissionDenied("You do not have permission to link to this encounter.")
        serializer.save()

    def perform_update(self, serializer) -> None:
        user = self.request.user
        # enforce using provided patient if present; otherwise instance.patient
        if "patient" in serializer.validated_data:
            self.enforce_patient_ownership(serializer, "You do not have permission to modify records for this patient.")
        patient = serializer.validated_data.get(
            "patient",
            getattr(serializer.instance, "patient", None)
        )
        encounter = serializer.validated_data.get(
            "encounter",
            getattr(serializer.instance, "encounter", None)
        )
        if encounter is not None:
            enc_patient = getattr(encounter, "patient", None)
            if enc_patient is not None and enc_patient != patient:
                raise PermissionDenied("Encounter does not belong to the selected patient.")
            if enc_patient is not None and getattr(enc_patient, "primary_doctor", None) != user:
                raise PermissionDenied("You do not have permission to link to this encounter.")
        serializer.save()