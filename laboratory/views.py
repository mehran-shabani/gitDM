from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import LabResult
from .serializers import LabResultSerializer


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return LabResult.objects.none()
        if getattr(user, 'is_superuser', False):
            return super().get_queryset()
        return super().get_queryset().filter(patient__primary_doctor=user)

    def perform_create(self, serializer) -> None:
        patient = serializer.validated_data.get('patient')
        user = self.request.user
        if (not getattr(user, 'is_superuser', False)) and (not patient or patient.primary_doctor_id != user.id):
            raise PermissionDenied("You do not have permission to add labs for this patient.")
        serializer.save()