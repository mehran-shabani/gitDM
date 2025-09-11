from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import MedicationOrder
from .serializers import MedicationOrderSerializer
from security.mixins import OwnedByCurrentDoctorQuerysetMixin
from security.permissions import IsOwnerDoctorOrReadOnly


class MedicationOrderViewSet(OwnedByCurrentDoctorQuerysetMixin, viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.select_related('patient', 'encounter').order_by('-start_date')
    serializer_class = MedicationOrderSerializer
    permission_classes = [IsOwnerDoctorOrReadOnly]

    def perform_create(self, serializer) -> None:
        self.enforce_patient_ownership(serializer, "You do not have permission to add records for this patient.")
        serializer.save()

    def perform_update(self, serializer) -> None:
        if "patient" in serializer.validated_data:
            self.enforce_patient_ownership(serializer, "You do not have permission to modify records for this patient.")
        serializer.save()