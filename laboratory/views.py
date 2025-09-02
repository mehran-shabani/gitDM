from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import LabResult
from .serializers import LabResultSerializer
from security.mixins import OwnedByCurrentDoctorQuerysetMixin
from security.permissions import IsOwnerDoctorOrReadOnly


class LabResultViewSet(OwnedByCurrentDoctorQuerysetMixin, viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer
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