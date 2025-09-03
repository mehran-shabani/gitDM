from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from encounters.models import Patient
from security.models import DoctorProfile

User = get_user_model()


class PatientAnalytics(models.Model):
    """مدل برای ذخیره آمارهای تحلیلی بیماران"""
    
    TREND_CHOICES = [
        ('improving', 'در حال بهبود'),
        ('stable', 'ثابت'),
        ('worsening', 'در حال بدتر شدن'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='بیمار'
    )
    
    date = models.DateField(
        default=timezone.now,
        verbose_name='تاریخ'
    )
    
    # آمارهای قند خون
    avg_glucose = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(800)],
        verbose_name='میانگین قند خون'
    )
    
    min_glucose = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(800)],
        verbose_name='حداقل قند خون'
    )
    
    max_glucose = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(800)],
        verbose_name='حداکثر قند خون'
    )
    
    glucose_std_dev = models.FloatField(
        null=True,
        blank=True,
        verbose_name='انحراف معیار قند خون'
    )
    
    glucose_trend = models.CharField(
        max_length=20,
        choices=TREND_CHOICES,
        default='stable',
        verbose_name='روند قند خون'
    )
    
    # آمارهای HbA1c
    avg_hba1c = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(4), MaxValueValidator(18)],
        verbose_name='میانگین HbA1c'
    )
    
    hba1c_trend = models.CharField(
        max_length=20,
        choices=TREND_CHOICES,
        default='stable',
        verbose_name='روند HbA1c'
    )
    
    # آمارهای فشار خون
    avg_systolic = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='میانگین فشار سیستولیک'
    )
    
    avg_diastolic = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='میانگین فشار دیاستولیک'
    )
    
    # سایر آمارها
    encounters_count = models.IntegerField(
        default=0,
        verbose_name='تعداد ویزیت‌ها'
    )
    
    medications_count = models.IntegerField(
        default=0,
        verbose_name='تعداد داروها'
    )
    
    lab_tests_count = models.IntegerField(
        default=0,
        verbose_name='تعداد آزمایش‌ها'
    )
    
    alerts_count = models.IntegerField(
        default=0,
        verbose_name='تعداد هشدارها'
    )
    
    compliance_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='امتیاز پایبندی به درمان'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'آمار بیمار'
        verbose_name_plural = 'آمارهای بیماران'
        unique_together = ['patient', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"آمار {self.patient} - {self.date}"


class DoctorAnalytics(models.Model):
    """مدل برای ذخیره آمارهای تحلیلی پزشکان"""
    
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='پزشک'
    )
    
    date = models.DateField(
        default=timezone.now,
        verbose_name='تاریخ'
    )
    
    # آمارهای بیماران
    total_patients = models.IntegerField(
        default=0,
        verbose_name='کل بیماران'
    )
    
    active_patients = models.IntegerField(
        default=0,
        verbose_name='بیماران فعال'
    )
    
    new_patients = models.IntegerField(
        default=0,
        verbose_name='بیماران جدید'
    )
    
    # آمارهای ویزیت
    total_encounters = models.IntegerField(
        default=0,
        verbose_name='کل ویزیت‌ها'
    )
    
    avg_encounters_per_patient = models.FloatField(
        null=True,
        blank=True,
        verbose_name='میانگین ویزیت به ازای هر بیمار'
    )
    
    # آمارهای عملکرد بیماران
    avg_patient_hba1c = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(4), MaxValueValidator(18)],
        verbose_name='میانگین HbA1c بیماران'
    )
    
    patients_at_goal = models.IntegerField(
        default=0,
        verbose_name='بیماران در محدوده هدف'
    )
    
    patients_above_goal = models.IntegerField(
        default=0,
        verbose_name='بیماران بالای محدوده هدف'
    )
    
    # آمارهای هشدارها
    total_alerts = models.IntegerField(
        default=0,
        verbose_name='کل هشدارها'
    )
    
    critical_alerts = models.IntegerField(
        default=0,
        verbose_name='هشدارهای بحرانی'
    )
    
    # امتیازات
    performance_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='امتیاز عملکرد'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'آمار پزشک'
        verbose_name_plural = 'آمارهای پزشکان'
        unique_together = ['doctor', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['doctor', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"آمار {self.doctor} - {self.date}"


class SystemAnalytics(models.Model):
    """مدل برای ذخیره آمارهای کلی سیستم"""
    
    date = models.DateField(
        unique=True,
        default=timezone.now,
        verbose_name='تاریخ'
    )
    
    # آمارهای کاربران
    total_users = models.IntegerField(
        default=0,
        verbose_name='کل کاربران'
    )
    
    active_users = models.IntegerField(
        default=0,
        verbose_name='کاربران فعال'
    )
    
    total_doctors = models.IntegerField(
        default=0,
        verbose_name='کل پزشکان'
    )
    
    total_patients = models.IntegerField(
        default=0,
        verbose_name='کل بیماران'
    )
    
    # آمارهای داده‌ها
    total_encounters = models.IntegerField(
        default=0,
        verbose_name='کل ویزیت‌ها'
    )
    
    total_lab_tests = models.IntegerField(
        default=0,
        verbose_name='کل آزمایش‌ها'
    )
    
    total_medications = models.IntegerField(
        default=0,
        verbose_name='کل نسخه‌ها'
    )
    
    total_alerts = models.IntegerField(
        default=0,
        verbose_name='کل هشدارها'
    )
    
    # آمارهای عملکرد سیستم
    avg_system_hba1c = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(4), MaxValueValidator(18)],
        verbose_name='میانگین HbA1c سیستم'
    )
    
    system_goal_achievement = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='درصد دستیابی به اهداف'
    )
    
    # آمارهای استفاده
    daily_active_users = models.IntegerField(
        default=0,
        verbose_name='کاربران فعال روزانه'
    )
    
    api_calls = models.IntegerField(
        default=0,
        verbose_name='تعداد فراخوانی API'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'آمار سیستم'
        verbose_name_plural = 'آمارهای سیستم'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"آمار سیستم - {self.date}"


class Report(models.Model):
    """مدل برای ذخیره گزارش‌های تولید شده"""
    
    REPORT_TYPES = [
        ('patient_summary', 'خلاصه بیمار'),
        ('doctor_performance', 'عملکرد پزشک'),
        ('system_overview', 'نمای کلی سیستم'),
        ('custom', 'سفارشی'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        verbose_name='نوع گزارش'
    )
    
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name='فرمت'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_reports',
        verbose_name='درخواست‌دهنده'
    )
    
    # فیلترها
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ شروع'
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ پایان'
    )
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='بیمار'
    )
    
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='پزشک'
    )
    
    # نتیجه
    file_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='مسیر فایل'
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='پیام خطا'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'گزارش'
        verbose_name_plural = 'گزارش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['requested_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"