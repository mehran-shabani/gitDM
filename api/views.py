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
        بازگردانی queryset مناسب برای کاربر جاری.
        
        این متد بر اساس وضعیت احراز هویت و مجوزهای کاربر، مجموعهٔ بیماران قابل‌دسترسی را بازمی‌گرداند:
        - اگر کاربر احراز هویت نشده باشد، یک queryset خالی بازمی‌گرداند.
        - اگر کاربر سوپر‌یوزر باشد، تمام بیماران (پیش‌فرض querysetِ والد) بازگردانده می‌شود.
        - در غیر اینصورت تنها بیمارانی که در فیلد `primary_doctor` به کاربر جاری مرتبط هستند فیلتر می‌شوند.
        
        Returns:
            django.db.models.QuerySet: queryset‌ای از اشیاء Patient مطابق سطح دسترسی کاربر.
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
        یک اکشن GET که تایم‌لاین تجمیع‌شدهٔ مرتبط با یک بیمار مشخص را بازمی‌گرداند.
        
        شرح:
        این متد برای یک بیمار (مشخص‌شده توسط pk از طریق get_object()) مجموعه‌ای از منابع بالینی مرتبط را پرس‌وجو، بر اساس زمان مرتب و سریالایز می‌کند و در یک پاسخ ترکیبی برمی‌گرداند. مجموعه‌ها به صورت جداگانه محدود و مرتب می‌شوند تا از بار زیاد روی سرور و شبکه جلوگیری شود.
        
        داده‌های بازگشتی:
        - patient: دادهٔ سریالایزشدهٔ بیمار.
        - encounters: لیستی از Encounterهای مرتب‌شده براساس `occurred_at` نزولی (تا `limit` مورد).
        - labs: لیستی از LabResultها مرتب‌شده براساس `taken_at` نزولی (تا `limit` مورد).
        - medications: لیستی از MedicationOrderها مرتب‌شده براساس `start_date` نزولی (تا `limit` مورد).
        - ai_summaries: لیستی از AISummaryهای تحلیلی/هوش‌مصنوعی مرتب‌شده براساس `created_at` نزولی (حداکثر ۵ مورد). این آیتم‌ها شامل خروجی‌های تحلیلی یا خلاصه‌های تولیدشده توسط سامانهٔ هوش‌مصنوعی برای کمک به بررسی بالینی هستند و مستقل از داده‌های خام بالینی ارائه می‌شوند.
        
        پارامترهای کوئری:
        - limit (اختیاری): حداکثر تعداد آیتم برای هر یک از مجموعه‌های Encounter، LabResult و MedicationOrder. مقدار پیش‌فرض ۱۰۰ و بیشینهٔ مجاز ۵۰۰ خواهد بود. AISummary همیشه تا ۵ مورد محدود می‌شود.
        
        نکات مهم:
        - هدف از محدودسازی و مرتب‌سازی، جلوگیری از مشکلات عملکردی و کاهش حجم دادهٔ منتقل‌شده است.
        - AISummaryها شامل تحلیل/خلاصهٔ تولیدشده توسط سیستم هوش‌مصنوعی هستند؛ رفتار، دقت یا منبع تولید این خلاصه‌ها خارج از این اکشن مدیریت می‌شود و صرفاً به صورت سریالایز شده بازگردانده می‌شوند.
        
        مقدار بازگشتی:
        - یک Response حاوی دیکشنری با کلیدهای ذکرشده و داده‌های سریالایز شده.
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
        یک Encounter جدید ایجاد و فیلد مالک (created_by) را تعیین می‌کند.
        
        این متد serializer.save(...) را فراخوانی می‌کند تا یک نمونه Encounter در پایگاه‌داده ساخته شود و مالک را بر اساس کاربر احراز هویت‌شدهٔ درخواست تنظیم می‌کند. اگر کاربر لاگین‌کرده باشد، شیء User او به created_by اختصاص می‌یابد؛ در غیر این صورت به‌عنوان مقدار جایگزین شناسه‌ی ثابت سیستم (SYSTEM_USER_ID، از نوع UUID) در created_by_id قرار داده می‌شود تا همیشه یک شناسه مالک ثبت شود. این متد صرفاً ذخیره‌سازی را انجام می‌دهد و خطاهای ذخیره‌سازی استاندارد مربوط به serializer را بازتولید می‌کند.
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
