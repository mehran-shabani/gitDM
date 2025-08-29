from uuid import UUID
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from django.contrib.auth import get_user_model
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
        user = self.request.user
        if not user.is_authenticated:
            return Patient.objects.none()
        if getattr(user, "is_superuser", False):
            return super().get_queryset()
        return super().get_queryset().filter(primary_doctor=user)
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        بازگرداندن یک "تایم‌لاین" تجمیع‌شده سطح بیمار شامل مواجهات، نتایج آزمایش، دستورهای دارویی و خلاصه‌های هوش‌مصنوعی.
        
        این اکشن (GET) برای یک بیمار مشخص:
        - بیمار را بازیابی می‌کند.
        - رکوردهای مرتبط را به‌صورت جداگانه پرس‌وجو و بر اساس زمان مرتب می‌کند:
          - Encounterها بر حسب `occurred_at` نزولی (تا `limit` مورد).
          - LabResultها بر حسب `taken_at` نزولی (تا `limit` مورد).
          - MedicationOrderها بر حسب `start_date` نزولی (تا `limit` مورد).
          - AISummaryها بر حسب `created_at` نزولی (حداکثر ۵ مورد).
        - هر مجموعه را با Serializer متناظر سریالایز کرده و در یک ساختار JSON ترکیبی برمی‌گرداند.
        
        پارامترهای کوئری:
        - limit (اختیاری): تعداد حداکثر آیتم‌ها در هر نوع (Encounter، LabResult، MedicationOrder). مقدار پیش‌فرض ۱۰۰ و حداکثر مجاز ۵۰۰ است. خلاصه‌های هوش‌مصنوعی همواره تا ۵ مورد محدود می‌شوند.
        
        مقدار بازگشتی:
        - یک Response حاوی دیکشنری با کلیدهای:
          - patient: داده‌ی سریالایزشده بیمار
          - encounters: لیست سریالایزشده مواجهات
          - labs: لیست سریالایزشده نتایج آزمایش
          - medications: لیست سریالایزشده دستورهای دارویی
          - ai_summaries: لیست سریالایزشده خلاصه‌های تولیدشده توسط سیستم هوش‌مصنوعی
        
        نکات افزوده:
        - محدود کردن نتایج برای جلوگیری از مشکلات عملکرد و ارسال حجم زیاد داده انجام شده است.
        - AISummary نشان‌دهنده‌ی خلاصه‌های تحلیلی/هوشمند مرتبط با بیمار است و جدا از داده‌های خام بالینی برگردانده می‌شود (همیشه تا ۵ مورد).
        """
        p = self.get_object()
        # Limit results to prevent performance issues
        limit = int(request.query_params.get('limit', 100))
        limit = min(limit, 500)  # Max 500 items per type
        
        enc = (
            Encounter.objects.filter(patient=p)
            .select_related('patient', 'created_by')
            .order_by('-occurred_at')[:limit]
        )
        labs = (
            LabResult.objects.filter(patient=p)
            .select_related('patient', 'encounter')
            .order_by('-taken_at')[:limit]
        )
        meds = (
            MedicationOrder.objects.filter(patient=p)
            .select_related('patient', 'encounter')
            .order_by('-start_date')[:limit]
        )
        summaries = (
            AISummary.objects.filter(patient=p)
            .select_related('patient', 'content_type')
            .order_by('-created_at')[:5]
        )
        
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

    def perform_create(self, serializer) -> None:
        # Use the authenticated user if available, otherwise use system user
        """
        ایجاد یک نمونه Encounter با انتساب کاربر سازنده.
        
        عملیات ذخیره (serializer.save) را فراخوانی می‌کند و فیلد created_by را براساس کاربر احراز هویت‌شدهٔ درخواست تنظیم می‌کند. اگر کاربر احراز هویت‌نشده باشد، به‌عنوان مقدار جایگزین شناسه سراسری سیستم (SYSTEM_USER_ID) را در created_by_id قرار می‌دهد. این متد باعث ایجاد و پایگاه‌داده‌ای شدن نمونه Encounter می‌شود و تضمین می‌کند که همیشه یک مقدار برای مالک/سازنده ثبت شده وجود دارد — در صورت نبود کاربر واقعی، از شناسه سیستم استفاده می‌شود (یک UUID)، نه یک شیء User کامل.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            serializer.save(created_by=user)
            return

        # Fallback به کاربر سیستمی واقعی
        User = get_user_model()
        try:
            system_user = User.objects.get(pk=SYSTEM_USER_ID)
        except User.DoesNotExist as exc:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                "SYSTEM_USER_ID not found in the user table. "
                "Create the system user or set a valid existing UUID."
            ) from exc
        serializer.save(created_by=system_user)


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer


class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer


class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer
