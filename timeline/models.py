from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class MedicalTimeline(models.Model):
    """
    مدل تایم‌لاین پزشکی برای ثبت و نمایش کرونولوژیک تمام رویدادهای مرتبط با بیمار
    """
    class EventType(models.TextChoices):
        ENCOUNTER = 'ENCOUNTER', 'مواجهه بالینی'
        LAB_RESULT = 'LAB_RESULT', 'نتیجه آزمایش'
        MEDICATION = 'MEDICATION', 'دارو'
        PHYSICAL_EXAM = 'PHYSICAL_EXAM', 'معاینه فیزیکی'
        DIAGNOSTIC_TEST = 'DIAGNOSTIC_TEST', 'تست تشخیصی'
        PROCEDURE = 'PROCEDURE', 'اقدام درمانی'
        DIET_PLAN = 'DIET_PLAN', 'برنامه غذایی'
        EXERCISE = 'EXERCISE', 'ورزش'
        ALERT = 'ALERT', 'هشدار بالینی'
        REMINDER = 'REMINDER', 'یادآوری'
    
    class Severity(models.TextChoices):
        LOW = 'LOW', 'پایین'
        NORMAL = 'NORMAL', 'عادی'
        HIGH = 'HIGH', 'بالا'
        CRITICAL = 'CRITICAL', 'بحرانی'
    
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    
    # Generic relation to link to any model (Encounter, LabResult, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # زمان وقوع رویداد (ممکن است با زمان ثبت متفاوت باشد)
    occurred_at = models.DateTimeField()
    
    # اطلاعات اضافی به صورت JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    # شدت و اولویت رویداد
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.NORMAL
    )
    
    # کاربر ایجادکننده
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_timeline_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # فلگ برای نمایش در تایم‌لاین
    is_visible = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['patient', 'occurred_at']),
            models.Index(fields=['event_type', 'occurred_at']),
            models.Index(fields=['severity', 'occurred_at']),
            models.Index(fields=['patient', 'event_type', 'occurred_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = 'Medical Timeline Event'
        verbose_name_plural = 'Medical Timeline Events'
    
    def __str__(self):
        return f"{self.title} - {self.patient.full_name} ({self.occurred_at.date()})"
    
    @classmethod
    def create_from_encounter(cls, encounter):
        """ایجاد رویداد تایم‌لاین از مواجهه بالینی"""
        return cls.objects.create(
            patient=encounter.patient,
            content_object=encounter,
            event_type=cls.EventType.ENCOUNTER,
            title=f"ویزیت پزشکی",
            description=encounter.subjective[:200] + "..." if len(encounter.subjective) > 200 else encounter.subjective,
            occurred_at=encounter.occurred_at,
            created_by=encounter.created_by,
            metadata={
                'assessment': encounter.assessment,
                'plan': encounter.plan
            }
        )
    
    @classmethod
    def create_from_lab_result(cls, lab_result):
        """ایجاد رویداد تایم‌لاین از نتیجه آزمایش"""
        # تعیین شدت بر اساس مقدار
        severity = cls.Severity.NORMAL
        if lab_result.loinc in ['4548-4', '17856-6']:  # HbA1c
            if lab_result.value > 9:
                severity = cls.Severity.CRITICAL
            elif lab_result.value > 7:
                severity = cls.Severity.HIGH
        elif lab_result.loinc in ['2345-7', '2339-0']:  # Glucose
            if lab_result.value < 70 or lab_result.value > 200:
                severity = cls.Severity.HIGH
        
        return cls.objects.create(
            patient=lab_result.patient,
            content_object=lab_result,
            event_type=cls.EventType.LAB_RESULT,
            title=f"نتیجه آزمایش {lab_result.loinc}",
            description=f"{lab_result.value} {lab_result.unit}",
            occurred_at=lab_result.taken_at,
            created_by=lab_result.encounter.created_by if lab_result.encounter else None,
            severity=severity,
            metadata={
                'loinc': lab_result.loinc,
                'value': str(lab_result.value),
                'unit': lab_result.unit
            }
        )


class TestReminder(models.Model):
    """
    مدل یادآوری آزمایشات و معاینات دوره‌ای
    """
    class TestType(models.TextChoices):
        # آزمایشات خونی
        HBA1C = 'HBA1C', 'HbA1c (هموگلوبین گلیکوزیله)'
        FBS = 'FBS', 'قند ناشتا (Fasting Blood Sugar)'
        TWO_HPP = '2HPP', 'قند ۲ ساعت بعد از غذا (2-Hour Post-Prandial)'
        BUN = 'BUN', 'اوره خون (Blood Urea Nitrogen)'
        CREATININE = 'CR', 'کراتینین (Creatinine)'
        ALT = 'ALT', 'آلانین آمینوترانسفراز'
        AST = 'AST', 'آسپارتات آمینوترانسفراز'
        ALP = 'ALP', 'آلکالین فسفاتاز'
        TSH = 'TSH', 'هورمون محرک تیروئید'
        
        # آزمایش ادرار
        URINE_24H_PROTEIN = 'PR_URINE_24', 'پروتئین ادرار ۲۴ ساعته'
        
        # معاینات
        EYE_EXAM = 'EYE_EXAM', 'معاینه چشم'
        EMG = 'EMG', 'الکترومایوگرافی'
        NCV = 'NCV', 'سرعت رسانش عصبی'
        
        # اندازه‌گیری‌ها
        BMI = 'BMI', 'شاخص توده بدنی'
        BLOOD_PRESSURE = 'BP', 'فشار خون'
        
        # برنامه‌ها
        DIET_CONSULTATION = 'DIET', 'مشاوره تغذیه'
        EXERCISE_PLAN = 'EXERCISE', 'برنامه ورزشی'
    
    class Frequency(models.TextChoices):
        WEEKLY = 'WEEKLY', 'هفتگی'
        MONTHLY = 'MONTHLY', 'ماهانه'
        QUARTERLY = 'QUARTERLY', 'سه‌ماهه'
        BIANNUALLY = 'BIANNUALLY', 'شش‌ماهه'
        ANNUALLY = 'ANNUALLY', 'سالانه'
        CUSTOM = 'CUSTOM', 'سفارشی'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'پایین'
        MEDIUM = 'MEDIUM', 'متوسط'
        HIGH = 'HIGH', 'بالا'
        URGENT = 'URGENT', 'فوری'
    
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='test_reminders'
    )
    
    test_type = models.CharField(max_length=20, choices=TestType.choices)
    frequency = models.CharField(max_length=15, choices=Frequency.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # تاریخ‌ها
    last_performed = models.DateTimeField(null=True, blank=True)
    next_due = models.DateTimeField()
    
    # تنظیمات یادآوری
    reminder_days_before = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)
    
    # اطلاعات اضافی
    notes = models.TextField(blank=True)
    custom_interval_days = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="فاصله سفارشی به روز (فقط برای نوع CUSTOM)"
    )
    
    # کاربر ایجادکننده
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_reminders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_due']
        indexes = [
            models.Index(fields=['patient', 'test_type']),
            models.Index(fields=['next_due', 'is_active']),
            models.Index(fields=['test_type', 'frequency']),
            models.Index(fields=['priority', 'next_due']),
        ]
        verbose_name = 'Test Reminder'
        verbose_name_plural = 'Test Reminders'
        unique_together = ['patient', 'test_type']  # یک نوع آزمایش برای هر بیمار
    
    def __str__(self):
        return f"{self.get_test_type_display()} - {self.patient.full_name} (سررسید: {self.next_due.date()})"
    
    def calculate_next_due_date(self):
        """محاسبه تاریخ سررسید بعدی"""
        if self.frequency == self.Frequency.WEEKLY:
            return self.next_due + timezone.timedelta(weeks=1)
        elif self.frequency == self.Frequency.MONTHLY:
            return self.next_due + timezone.timedelta(days=30)
        elif self.frequency == self.Frequency.QUARTERLY:
            return self.next_due + timezone.timedelta(days=90)
        elif self.frequency == self.Frequency.BIANNUALLY:
            return self.next_due + timezone.timedelta(days=180)
        elif self.frequency == self.Frequency.ANNUALLY:
            return self.next_due + timezone.timedelta(days=365)
        elif self.frequency == self.Frequency.CUSTOM and self.custom_interval_days:
            return self.next_due + timezone.timedelta(days=self.custom_interval_days)
        return self.next_due
    
    def mark_as_completed(self, performed_date=None):
        """علامت‌گذاری آزمایش به عنوان انجام شده"""
        if performed_date is None:
            performed_date = timezone.now()
        
        self.last_performed = performed_date
        self.next_due = self.calculate_next_due_date()
        self.save(update_fields=['last_performed', 'next_due'])
        
        # ایجاد notification برای تأیید انجام
        from notifications.services import NotificationService
        NotificationService.create_test_completion_notification(self, performed_date)
    
    def is_overdue(self):
        """بررسی اینکه آزمایش از موعد گذشته است یا نه"""
        return timezone.now() > self.next_due
    
    def days_until_due(self):
        """تعداد روزهای باقی‌مانده تا سررسید"""
        delta = self.next_due - timezone.now()
        return delta.days
    
    def should_send_reminder(self):
        """بررسی اینکه آیا باید یادآوری ارسال شود یا نه"""
        days_left = self.days_until_due()
        return 0 <= days_left <= self.reminder_days_before


class TimelineEventCategory(models.Model):
    """
    دسته‌بندی رویدادهای تایم‌لاین برای بهتر سازماندهی کردن
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # کد رنگ hex
    icon = models.CharField(max_length=50, blank=True)  # نام آیکون
    
    class Meta:
        verbose_name = 'Timeline Event Category'
        verbose_name_plural = 'Timeline Event Categories'
    
    def __str__(self):
        return self.name


class MedicalTimelineNote(models.Model):
    """
    یادداشت‌های اضافی برای رویدادهای تایم‌لاین
    """
    timeline_event = models.ForeignKey(
        MedicalTimeline,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note = models.TextField()
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-added_at']
    
    def __str__(self):
        return f"یادداشت برای {self.timeline_event.title} در {self.added_at.date()}"


class ReminderTemplate(models.Model):
    """
    قالب‌های از پیش تعریف شده برای یادآورهای مختلف
    """
    test_type = models.CharField(
        max_length=20,
        choices=TestReminder.TestType.choices,
        unique=True
    )
    default_frequency = models.CharField(
        max_length=15,
        choices=TestReminder.Frequency.choices
    )
    default_priority = models.CharField(
        max_length=10,
        choices=TestReminder.Priority.choices,
        default=TestReminder.Priority.MEDIUM
    )
    default_reminder_days = models.PositiveIntegerField(default=7)
    
    # راهنمایی‌ها
    instructions = models.TextField(blank=True)
    preparation_notes = models.TextField(blank=True)  # نکات آماده‌سازی
    
    # فعال/غیرفعال
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Reminder Template'
        verbose_name_plural = 'Reminder Templates'
    
    def __str__(self):
        return f"قالب یادآوری {self.get_test_type_display()}"


class PatientTimelinePreference(models.Model):
    """
    تنظیمات شخصی‌سازی تایم‌لاین برای هر بیمار
    """
    patient = models.OneToOneField(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='timeline_preferences'
    )
    
    # تنظیمات نمایش
    show_lab_results = models.BooleanField(default=True)
    show_medications = models.BooleanField(default=True)
    show_encounters = models.BooleanField(default=True)
    show_alerts = models.BooleanField(default=True)
    show_reminders = models.BooleanField(default=True)
    
    # تنظیمات یادآوری
    enable_email_reminders = models.BooleanField(default=True)
    enable_sms_reminders = models.BooleanField(default=False)
    
    # محدوده زمانی پیش‌فرض
    default_timeline_range_days = models.PositiveIntegerField(default=365)  # یک سال
    
    class Meta:
        verbose_name = 'Patient Timeline Preference'
        verbose_name_plural = 'Patient Timeline Preferences'
    
    def __str__(self):
        return f"تنظیمات تایم‌لاین {self.patient.full_name}"