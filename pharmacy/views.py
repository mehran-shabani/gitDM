from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import MedicationOrder
from .serializers import MedicationOrderSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return MedicationOrder.objects.none()
        if getattr(user, 'is_superuser', False):
            return super().get_queryset()
        return super().get_queryset().filter(patient__primary_doctor=user)

    def perform_create(self, serializer) -> None:
        patient = serializer.validated_data.get('patient')
        user = self.request.user
        if (not getattr(user, 'is_superuser', False)) and (not patient or patient.primary_doctor_id != user.id):
            raise PermissionDenied("You do not have permission to prescribe medications for this patient.")
        serializer.save()