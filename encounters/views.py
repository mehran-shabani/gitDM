from rest_framework import viewsets
from .models import Encounter
from .serializers import EncounterSerializer


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer

    def perform_create(self, serializer) -> None:
        """
        ایجاد و ذخیره‌ی یک نمونه Encounter و تعیین نویسندهٔ آن.
        
        این متد هنگام ایجاد (create) یک Encounter، serializer.save() را فراخوانی می‌کند و فیلد created_by را با کاربر احراز هویت شده مقداردهی می‌کند.
        چون این ViewSet از تنظیمات پیش‌فرض DRF استفاده می‌کند که نیازمند احراز هویت است، کاربر همیشه احراز هویت شده خواهد بود.
        """
        serializer.save(created_by=self.request.user)