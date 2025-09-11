from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Encounter
from .serializers import EncounterSerializer
from security.mixins import OwnedByCurrentDoctorQuerysetMixin
from security.permissions import IsOwnerDoctorOrReadOnly


class EncounterViewSet(OwnedByCurrentDoctorQuerysetMixin, viewsets.ModelViewSet):
    queryset = Encounter.objects.select_related('patient', 'created_by').order_by('-occurred_at')
    serializer_class = EncounterSerializer
    permission_classes = (IsOwnerDoctorOrReadOnly,)

    def perform_create(self, serializer) -> None:
        """
        ایجاد و ذخیره‌ی یک نمونه Encounter و تعیین نویسندهٔ آن.
        
        این متد هنگام ایجاد (create) یک Encounter، serializer.save() را فراخوانی می‌کند و فیلد created_by را با کاربر احراز هویت شده مقداردهی می‌کند.
        چون این ViewSet از تنظیمات پیش‌فرض DRF استفاده می‌کند که نیازمند احراز هویت است، کاربر همیشه احراز هویت شده خواهد بود.
        """
        # Ensure patient belongs to current doctor (superusers bypass)
        if not getattr(self.request.user, "is_superuser", False):
            self.enforce_patient_ownership(
                serializer,
                "You do not have permission to add records for this patient.",
            )
        serializer.save(created_by=self.request.user)
    def perform_update(self, serializer) -> None:
        if not getattr(self.request.user, "is_superuser", False):
            self.enforce_patient_ownership(
                serializer,
                "You do not have permission to modify records for this patient.",
            )
        serializer.save()