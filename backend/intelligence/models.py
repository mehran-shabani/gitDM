from __future__ import annotations
import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError


class AISummary(models.Model):
    id = models.BigAutoField(primary_key=True)
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(max_length=64, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    summary = models.TextField()
    references = models.ManyToManyField(
        'references.ClinicalReference',
        blank=True,
        help_text="Clinical references automatically linked based on summary content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def resource_type(self: "AISummary") -> str:
        """
        نام مدل مرتبط با شیء پیوست‌شده را برمی‌گرداند (برای نمایش سازگار با نسخه‌های قبلی در پنل ادمین).

        این متد مقدار `content_type.model` را برمی‌گرداند که نام مدل مربوط به شیء مرتبط را نشان می‌دهد. برای نمایش کوتاه در پنل ادمین و نگه‌داشتن سازگاری با نسخه‌های قبلی کلاس به‌عنوان یک ویژگی بازگشتی استفاده می‌شود.

        Returns:
            str: نام مدل مرتبط (معمولاً به صورت حروف کوچک).
        """
        return self.content_type.model

    def clean(self: "AISummary") -> None:
        """
        یک‌خطی:
        اعتبارسنجی می‌کند که اگر شیء مرتبط (content_object) دارای فیلد patient باشد، همان بیمارِ AISummary باشد.

        توضیح تفصیلی:
        این متد هنگام اعتبارسنجی مدل اجرا می‌شود و در صورت وجود content_object و داشتن صفت `patient`، مقدار آن را با `self.patient` مقایسه می‌کند. در صورت ناهماهنگی بین بیماران، یک ValidationError برای فیلد `patient` بالا می‌برد تا از ذخیره‌سازی یا پردازش داده‌های نامتجانس جلوگیری کند.

        استثناها:
        - ValidationError: زمانی که patient مربوط به content_object با patient این AISummary مطابقت نداشته باشد.
        """
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self: "AISummary") -> str:
        """
        رشته‌نمایشی مدل برای نمایش در ادمین: یک برچسب قابل خواندن که خلاصهٔ هوش‌مصنوعی را به صورت "AI Summary for <نام کامل بیمار> - <نام مدل مرتبط>" برمی‌گرداند.

        این مقدار برای نمایش در لیست‌ها و صفحات ادمین استفاده می‌شود و از فیلدهای `patient.full_name` و `content_type.model` برای ساخت رشته استفاده می‌کند.
        """

        return f"AI Summary for {self.patient.full_name} - {self.content_type.model}"


class BaselineMetrics(models.Model):
    """
    معیارهای پایه برای هر بیمار جهت مقایسه با داده‌های جدید
    """
    patient = models.OneToOneField('gitdm.PatientProfile', on_delete=models.CASCADE)
    
    # معیارهای آزمایشگاهی
    avg_hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_blood_glucose = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_systolic_bp = models.IntegerField(null=True, blank=True)
    avg_diastolic_bp = models.IntegerField(null=True, blank=True)
    
    # انحراف معیار برای هر معیار
    std_hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    std_blood_glucose = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    std_systolic_bp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    std_diastolic_bp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # الگوهای رفتاری
    avg_encounters_per_month = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_labs_per_month = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    medication_adherence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # آخرین به‌روزرسانی
    last_calculated = models.DateTimeField(auto_now=True)
    data_points_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Baseline Metrics"
        verbose_name_plural = "Baseline Metrics"
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["last_calculated"]),
        ]
    
    def __str__(self) -> str:
        return f"Baseline for {self.patient.full_name}"


class PatternAnalysis(models.Model):
    """
    نتایج تحلیل الگوهای رفتاری بیمار
    """
    class PatternType(models.TextChoices):
        GLUCOSE_TREND = 'GLUCOSE_TREND', 'روند قند خون'
        HBA1C_TREND = 'HBA1C_TREND', 'روند HbA1c'
        BP_TREND = 'BP_TREND', 'روند فشار خون'
        MEDICATION_ADHERENCE = 'MED_ADHERENCE', 'پایبندی دارویی'
        VISIT_FREQUENCY = 'VISIT_FREQ', 'فراوانی ویزیت'
        LAB_FREQUENCY = 'LAB_FREQ', 'فراوانی آزمایش'
    
    class TrendDirection(models.TextChoices):
        IMPROVING = 'IMPROVING', 'بهبود'
        STABLE = 'STABLE', 'پایدار'
        WORSENING = 'WORSENING', 'بدتر شدن'
        FLUCTUATING = 'FLUCTUATING', 'نوسان'
    
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    pattern_type = models.CharField(max_length=20, choices=PatternType.choices)
    trend_direction = models.CharField(max_length=15, choices=TrendDirection.choices)
    
    # نتایج تحلیل
    analysis_result = models.JSONField(default=dict)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)  # 0-1
    statistical_significance = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    
    # بازه زمانی تحلیل
    analysis_start_date = models.DateTimeField()
    analysis_end_date = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pattern Analysis"
        verbose_name_plural = "Pattern Analyses"
        indexes = [
            models.Index(fields=["patient", "pattern_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["trend_direction"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_pattern_type_display()} for {self.patient.full_name} - {self.get_trend_direction_display()}"


class AnomalyDetection(models.Model):
    """
    ناهنجاری‌های تشخیص داده شده در داده‌های بیمار
    """
    class AnomalyType(models.TextChoices):
        STATISTICAL_OUTLIER = 'OUTLIER', 'نقطه پرت آماری'
        SUDDEN_CHANGE = 'SUDDEN_CHANGE', 'تغییر ناگهانی'
        TREND_REVERSAL = 'TREND_REVERSAL', 'معکوس شدن روند'
        MISSING_DATA = 'MISSING_DATA', 'داده گمشده'
        MEDICATION_SKIP = 'MED_SKIP', 'عدم مصرف دارو'
        UNUSUAL_PATTERN = 'UNUSUAL_PATTERN', 'الگوی غیرعادی'
    
    class SeverityLevel(models.TextChoices):
        LOW = 'LOW', 'کم'
        MEDIUM = 'MEDIUM', 'متوسط'
        HIGH = 'HIGH', 'بالا'
        CRITICAL = 'CRITICAL', 'بحرانی'
    
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    anomaly_type = models.CharField(max_length=20, choices=AnomalyType.choices)
    severity_level = models.CharField(max_length=10, choices=SeverityLevel.choices)
    
    # جزئیات ناهنجاری
    description = models.TextField()
    detected_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    expected_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    deviation_score = models.DecimalField(max_digits=5, decimal_places=3)  # میزان انحراف از نرمال
    
    # ارجاع به داده مرتبط
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=64, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # وضعیت پردازش
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        'gitdm.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='acknowledged_anomalies'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # زمان‌بندی
    detected_at = models.DateTimeField(auto_now_add=True)
    data_timestamp = models.DateTimeField()  # زمان واقعی داده
    
    class Meta:
        verbose_name = "Anomaly Detection"
        verbose_name_plural = "Anomaly Detections"
        indexes = [
            models.Index(fields=["patient", "severity_level"]),
            models.Index(fields=["anomaly_type", "detected_at"]),
            models.Index(fields=["is_acknowledged"]),
            models.Index(fields=["data_timestamp"]),
        ]
        ordering = ['-detected_at']
    
    def __str__(self) -> str:
        return f"{self.get_anomaly_type_display()} - {self.patient.full_name} ({self.get_severity_level_display()})"


class PatternAlert(models.Model):
    """
    هشدارهای مبتنی بر الگوهای تشخیص داده شده
    """
    class AlertType(models.TextChoices):
        DETERIORATING_CONTROL = 'DETERIORATING', 'بدتر شدن کنترل'
        MEDICATION_NON_ADHERENCE = 'NON_ADHERENCE', 'عدم پایبندی دارویی'
        MISSED_APPOINTMENTS = 'MISSED_APPT', 'عدم حضور در ویزیت'
        UNUSUAL_LAB_PATTERN = 'UNUSUAL_LAB', 'الگوی غیرعادی آزمایش'
        EMERGENCY_PATTERN = 'EMERGENCY', 'الگوی اورژانسی'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'کم'
        MEDIUM = 'MEDIUM', 'متوسط'
        HIGH = 'HIGH', 'بالا'
        URGENT = 'URGENT', 'فوری'
    
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # ارجاع به تحلیل‌های مرتبط
    related_patterns = models.ManyToManyField(PatternAnalysis, blank=True)
    related_anomalies = models.ManyToManyField(AnomalyDetection, blank=True)
    
    # وضعیت هشدار
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        'gitdm.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # زمان‌بندی
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Pattern Alert"
        verbose_name_plural = "Pattern Alerts"
        indexes = [
            models.Index(fields=["patient", "priority"]),
            models.Index(fields=["alert_type", "is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_resolved"]),
        ]
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.title} - {self.patient.full_name} ({self.get_priority_display()})"