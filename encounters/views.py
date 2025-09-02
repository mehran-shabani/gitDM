from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Encounter
from .serializers import EncounterSerializer


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return Encounter.objects.none()
        if getattr(user, 'is_superuser', False):
            return super().get_queryset()
        return super().get_queryset().filter(
            Q(patient__primary_doctor=user) | Q(created_by=user)
        )

    def perform_create(self, serializer) -> None:
        """
        ایجاد و ذخیره‌ی یک نمونه Encounter و تعیین نویسندهٔ آن.
        
        این متد هنگام ایجاد (create) یک Encounter، serializer.save() را فراخوانی می‌کند و فیلد created_by را با کاربر احراز هویت شده مقداردهی می‌کند.
        چون این ViewSet از تنظیمات پیش‌فرض DRF استفاده می‌کند که نیازمند احراز هویت است، کاربر همیشه احراز هویت شده خواهد بود.
        """
        patient = serializer.validated_data.get('patient')
        user = self.request.user
        if (not getattr(user, 'is_superuser', False)) and (not patient or patient.primary_doctor_id != user.id):
            raise PermissionDenied("You do not have permission to create encounters for this patient.")
        serializer.save(created_by=user)