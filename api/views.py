from uuid import UUID
from django.conf import settings
from rest_framework import viewsets
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
    MedicationOrderSerializer, ClinicalReferenceSerializer, AISummarySerializer
)

SYSTEM_USER_ID = UUID(getattr(settings, 'SYSTEM_USER_ID'))


from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        بازگرداندن queryset مناسب برای Patient با اعمال محدودیت‌های دسترسی براساس کاربر درخواست‌کننده.
        
        این متد:
        - در صورتی که کاربر احراز هویت نشده باشد، یک queryset خالی برمی‌گرداند تا دسترسی به بیماران مسدود شود.
        - اگر کاربر سوپر‌یوزر باشد، تمام رکوردهای پیش‌فرض (از super().get_queryset()) را بازمی‌گرداند.
        - در غیر این‌صورت فقط آن بیمارانی که فیلد `primary_doctor` آن‌ها برابر با کاربر جاری است بازگردانده می‌شوند.
        
        هدف: تضمین اینکه کاربران عادی تنها به بیماران مربوط به خود دسترسی دارند و کاربران بدون احراز هویت هیچ داده‌ای نمی‌بینند.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Patient.objects.none()
        if getattr(user, "is_superuser", False):
            return super().get_queryset()
        return super().get_queryset().filter(primary_doctor=user)
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        تایم‌لاین تجمیع‌شده یک بیمار را برمی‌گرداند، شامل مواجهات بالینی، نتایج آزمایش، دستورهای دارویی و خلاصه‌های تولیدشده توسط زیرسیستم هوش‌مصنوعی.
        
        جزئیات:
        - این اکشن برای یک بیمار مشخص (بر پایه pk/URL) اجرا می‌شود و مجموعه‌های مرتبط را جداگانه واکشی و سریالایز می‌کند.
        - محدودیت‌ها:
          - پارامتر کوئری `limit` تعیین‌کننده حداکثر تعداد آیتم‌ها برای هر یک از نوع‌های Encounter، LabResult و MedicationOrder است. مقدار پیش‌فرض 100 و بیشینه مجاز 500 است (اگر مقدار بزرگ‌تر ارسال شود به 500 تقلیل می‌یابد).
          - AISummaryها مستقل از `limit` همواره تا 5 مورد اخیر (بر اساس `created_at` نزولی) محدود می‌شوند.
        - داده‌های بازگردانده شده:
          - patient: داده سریالایزشدهٔ بیمار
          - encounters: لیست سریالایزشدهٔ Encounterها مرتب‌شده بر اساس `occurred_at` نزولی (تا `limit`)
          - labs: لیست سریالایزشدهٔ LabResultها مرتب‌شده بر اساس `taken_at` نزولی (تا `limit`)
          - medications: لیست سریالایزشدهٔ MedicationOrderها مرتب‌شده بر اساس `start_date` نزولی (تا `limit`)
          - ai_summaries: لیست سریالایزشدهٔ AISummaryها (حداکثر 5 مورد، مرتب بر اساس `created_at` نزولی)
        
        نکات مرتبط با هوش‌مصنوعی و پردازش:
        - AISummaryها خروجی‌های تحلیلی/خلاصه‌سازی هستند که ممکن است بر پایه پردازش‌های خودکار، مدل‌های زبانی یا آنالیزهای بالینی تولید شده باشند؛ این موارد مکمل داده‌های خام بالینی هستند و برای نمایش خلاصهٔ وضعیت یا نکات مهم بیمار ارائه می‌شوند.
        - این اکشن صرفاً خواندن و سریالایز کردن رکوردهای AISummary را انجام می‌دهد و هیچ پردازش یا اجرای تسک ضمنی (مثل فراخوانی مدل یا ایجاد وظیفه پس‌زمینه) را راه‌اندازی نمی‌کند؛ اگر نیاز به تولید یا به‌روزرسانی خلاصه‌های هوش‌مصنوعی باشد، آن عملیات باید از مسیرهای جداگانه مدیریت شود.
        
        عوارض جانبی و خطاها:
        - خود تابع داده‌ها را تغییر نمی‌دهد؛ در صورت نبودن دسترسی یا وجود خطا در بازیابی آبجکت بیمار، خطاهای مربوط به permissions یا 404 توسط متدهای پایهٔ ViewSet/DRF تولید می‌شوند.
        """
        p = self.get_object()
        # Limit results to prevent performance issues
        limit = int(request.query_params.get('limit', 100))
        limit = min(limit, 500)  # Max 500 items per type
        
        enc = Encounter.objects.filter(patient=p).order_by('-occurred_at')[:limit]
        labs = LabResult.objects.filter(patient=p).order_by('-taken_at')[:limit]
        meds = MedicationOrder.objects.filter(patient=p).order_by('-start_date')[:limit]
        summaries = AISummary.objects.filter(patient=p).order_by('-created_at')[:5]
        
        return Response({
            'patient': PatientSerializer(p).data,
            'encounters': EncounterSerializer(enc, many=True).data,
            'labs': LabResultSerializer(labs, many=True).data,
            'medications': MedicationOrderSerializer(meds, many=True).data,
            'ai_summaries': AISummarySerializer(summaries, many=True).data
        })


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer

    def perform_create(self, serializer):
        # Use the authenticated user if available, otherwise use system user
        """
        ایجاد و ذخیره‌ی یک نمونه Encounter و تعیین نویسندهٔ آن.
        
        این متد هنگام ایجاد (create) یک Encounter، serializer.save() را فراخوانی می‌کند و فیلد مالک/سازنده را تضمینی مقداردهی می‌کند: اگر درخواست‌دهنده احراز هویت شده باشد، شیٔ User مربوطه در created_by قرار می‌گیرد، و در غیر این‌صورت به‌عنوان مقدار جایگزین شناسه‌ی UUID تعریف‌شده در SYSTEM_USER_ID در created_by_id نوشته می‌شود. نتیجهٔ متد ایجاد و ذخیرهٔ شیٔ پایگاه‌داده‌ای Encounter است؛ این روش تضمین می‌کند همیشه یک مقدار مرجع برای سازنده وجود دارد (یا ارجاع به یک User واقعی یا شناسهٔ سیستم).
        """
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            serializer.save(created_by=user)
        else:
            # Fallback to system user ID - this should ideally be a proper User instance
            serializer.save(created_by_id=SYSTEM_USER_ID)


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer


class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer
