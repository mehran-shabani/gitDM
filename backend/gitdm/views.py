from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import PatientProfile
from .serializers import PatientSerializer, CustomTokenObtainPairSerializer
from .permissions import IsDoctor, IsPatientOwnerOrDoctor


class PatientViewSet(viewsets.ModelViewSet):
    queryset = PatientProfile.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_permissions(self):
        """
        تنظیم permissions بر اساس action
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'timeline']:
            permission_classes = [IsAuthenticated, IsPatientOwnerOrDoctor]
        else:
            permission_classes = [IsAuthenticated, IsDoctor]
        
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

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
            return PatientProfile.objects.none()
        if getattr(user, "is_superuser", False):
            return super().get_queryset()
        return super().get_queryset().filter(primary_doctor=user)
    
    def perform_create(self, serializer) -> None:
        # Assign current user as primary_doctor to satisfy permission model
        serializer.save(primary_doctor=self.request.user)

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
        - encounters: لیست سریالایزشدهٔ Encounterها مرتب‌شده بر اساس `occured_at` نزولی (تا `limit`)
        - labs: لیست سریالایزشدهٔ LabResultها مرتب‌شده بر اساس `taken_at` نزولی (تا `limit`)
        - medications: لیست سریالایزشدهٔ MedicationOrderها مرتب‌شده بر اساس `start_date` نزولی (تا `limit`)
        - ai_summaries: لیست سریالایزشدهٔ AISummaryها (حداکثر 5 مورد، مرتب بر اساس `created_at` نزولی)
        
        نکات مرتبط با هوش‌مصنوعی و پردازش:
        - AISummaryها خروجی‌های تحلیلی/خلاصه‌سازی هستند که ممکن است بر پایه پردازش‌های خودکار، مدل‌های زبانی یا آنالیزهای بالینی تولید شده باشند؛ این موارد مکمل داده‌های خام بالینی هستند و برای نمایش خلاصهٔ وضعیت یا نکات مهم بیمار ارائه می‌شوند.
        - این اکشن صرفاً خواندن و سریالایز کردن رکوردهای AISummary را انجام می‌دهد و هیچ پردازش یا اجرای تسک ضمنی (مثل فراخوانی مدل یا ایجاد وظیفه پس‌زمینه) را راه‌اندازی نمی‌کند؛ اگر نیاز به تولید یا به‌روزرسانی خلاصه‌های هوش‌مصنوعی باشد، آن عملیات باید از مسیرهای جداگانه مدیریت شود.
        
        عوارض جانبی و خطاها:
        - خود تابع داده‌ها را تغییر نمی‌دهد؛ در صورت نبودن دسترسی یا وجود خطا در بازیابی آبجکت بیمار، خطاهای مربوط به permissions یا 404 توسط متدهای پایهٔ ViewSet/DRF تولید می‌شوند.
        """
        from encounters.models import Encounter
        from encounters.serializers import EncounterSerializer
        from laboratory.models import LabResult
        from laboratory.serializers import LabResultSerializer
        from pharmacy.models import MedicationOrder
        from pharmacy.serializers import MedicationOrderSerializer
        from intelligence.models import AISummary
        from intelligence.serializers import AISummarySimpleSerializer
        
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
            'patient': PatientSerializer(p, context={'request': request}).data,
            'encounters': EncounterSerializer(enc, many=True).data,
            'labs': LabResultSerializer(labs, many=True).data,
            'medications': MedicationOrderSerializer(meds, many=True).data,
            'ai_summaries': AISummarySimpleSerializer(summaries, many=True).data
        })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer