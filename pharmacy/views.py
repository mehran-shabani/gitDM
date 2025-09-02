from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import MedicationOrder
from .serializers import MedicationOrderSerializer
from security.mixins import OwnedByCurrentDoctorQuerysetMixin
from security.permissions import IsOwnerDoctorOrReadOnly


class MedicationOrderViewSet(OwnedByCurrentDoctorQuerysetMixin, viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer
    permission_classes = [IsOwnerDoctorOrReadOnly]

    def perform_create(self, serializer) -> None:
        patient = serializer.validated_data.get("patient")
        if patient is not None and getattr(patient, "primary_doctor", None) != self.request.user:
            raise PermissionDenied("You do not have permission to add records for this patient.")
        serializer.save()

    def perform_update(self, serializer) -> None:
        patient = serializer.validated_data.get("patient")
        if patient is not None and getattr(patient, "primary_doctor", None) != self.request.user:
            raise PermissionDenied("You do not have permission to modify records for this patient.")
        serializer.save()