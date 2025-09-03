from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    مدل اطلاع‌رسانی برای کاربران
    """
    class NotificationType(models.TextChoices):
        INFO = 'INFO', 'اطلاعات'
        WARNING = 'WARNING', 'هشدار'
        CRITICAL = 'CRITICAL', 'بحرانی'
        REMINDER = 'REMINDER', 'یادآوری'
        AI_SUMMARY = 'AI_SUMMARY', 'خلاصه هوشمند'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'پایین'
        MEDIUM = 'MEDIUM', 'متوسط'
        HIGH = 'HIGH', 'بالا'
        URGENT = 'URGENT', 'فوری'
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # ارتباط با منابع
    patient_id = models.CharField(max_length=64, null=True, blank=True)
    resource_type = models.CharField(max_length=50, null=True, blank=True)
    resource_id = models.CharField(max_length=64, null=True, blank=True)
    
    # وضعیت
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # کانال‌های ارسال
    sent_email = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'priority']),
            models.Index(fields=['patient_id', 'created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.email}"
    
    def mark_as_read(self):
        """
        علامت‌گذاری به عنوان خوانده شده
        """
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class ClinicalAlert(models.Model):
    """
    مدل برای هشدارهای بالینی خودکار
    """
    class AlertType(models.TextChoices):
        HIGH_HBA1C = 'HIGH_HBA1C', 'HbA1c بالا'
        LOW_GLUCOSE = 'LOW_GLUCOSE', 'قند خون پایین'
        HIGH_GLUCOSE = 'HIGH_GLUCOSE', 'قند خون بالا'
        MISSED_APPOINTMENT = 'MISSED_APPOINTMENT', 'عدم حضور در ویزیت'
        DRUG_INTERACTION = 'DRUG_INTERACTION', 'تداخل دارویی'
        ABNORMAL_TREND = 'ABNORMAL_TREND', 'روند غیرطبیعی'
    
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='clinical_alerts'
    )
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'پایین'),
            ('MEDIUM', 'متوسط'),
            ('HIGH', 'بالا'),
            ('CRITICAL', 'بحرانی')
        ],
        default='MEDIUM'
    )
    
    # جزئیات هشدار
    trigger_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    message = models.TextField()
    
    # وضعیت
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.patient.full_name}"
    
    def acknowledge(self, user):
        """
        تایید هشدار توسط پزشک
        """
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['acknowledged_by', 'acknowledged_at', 'is_active'])


class SmartReminder(models.Model):
    """
    مدل یادآوری هوشمند برای داروها، آزمایشات و ویزیت‌ها
    """
    class ReminderType(models.TextChoices):
        MEDICATION = 'MEDICATION', 'مصرف دارو'
        LAB_TEST = 'LAB_TEST', 'آزمایش'
        APPOINTMENT = 'APPOINTMENT', 'ویزیت'
        EXERCISE = 'EXERCISE', 'ورزش'
        DIET = 'DIET', 'رژیم غذایی'
        GLUCOSE_CHECK = 'GLUCOSE_CHECK', 'چک قند خون'
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'فعال'
        PAUSED = 'PAUSED', 'متوقف شده'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'
    
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='smart_reminders'
    )
    reminder_type = models.CharField(max_length=20, choices=ReminderType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # ارتباط با منابع
    medication_id = models.CharField(max_length=64, null=True, blank=True)
    lab_test_id = models.CharField(max_length=64, null=True, blank=True)
    
    # زمان‌بندی
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # تنظیمات تکرار
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('ONCE', 'یکبار'),
            ('DAILY', 'روزانه'),
            ('WEEKLY', 'هفتگی'),
            ('MONTHLY', 'ماهانه'),
            ('CUSTOM', 'سفارشی')
        ],
        default='DAILY'
    )
    times_per_day = models.PositiveIntegerField(default=1)
    days_of_week = models.JSONField(
        default=list,
        blank=True,
        help_text="روزهای هفته برای یادآوری (0=یکشنبه، 6=شنبه)"
    )
    
    # زمان‌های پیشنهادی (یادگیری شده)
    preferred_times = models.JSONField(
        default=list,
        help_text="زمان‌های ترجیحی برای یادآوری"
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    is_adaptive = models.BooleanField(
        default=True,
        help_text="آیا زمان‌بندی بر اساس رفتار بیمار تنظیم شود"
    )
    
    # اطلاعات اولویت
    priority = models.IntegerField(
        default=5,
        help_text="اولویت یادآوری (1-10)"
    )
    is_critical = models.BooleanField(
        default=False,
        help_text="آیا یادآوری بحرانی است"
    )
    
    # متادیتا
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reminders'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['patient', 'status', 'reminder_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.reminder_type} - {self.title} - {self.patient.full_name}"
    
    def is_active_on_date(self, date):
        """
        چک کردن اینکه آیا یادآوری در تاریخ مشخص فعال است
        """
        if self.status != self.Status.ACTIVE:
            return False
        if date < self.start_date:
            return False
        if self.end_date and date > self.end_date:
            return False
        return True


class ReminderPattern(models.Model):
    """
    الگوهای رفتاری بیمار برای بهینه‌سازی زمان یادآوری
    """
    patient = models.ForeignKey(
        'gitdm.PatientProfile',
        on_delete=models.CASCADE,
        related_name='reminder_patterns'
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=SmartReminder.ReminderType.choices
    )
    
    # الگوهای زمانی
    best_response_times = models.JSONField(
        default=list,
        help_text="زمان‌هایی که بیمار بهترین پاسخ را داده"
    )
    worst_response_times = models.JSONField(
        default=list,
        help_text="زمان‌هایی که بیمار پاسخ نداده"
    )
    
    # آمار پاسخ‌دهی
    total_reminders_sent = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    average_response_time = models.DurationField(
        null=True,
        blank=True,
        help_text="میانگین زمان پاسخ به یادآوری"
    )
    
    # ترجیحات یادگیری شده
    preferred_notification_channel = models.CharField(
        max_length=20,
        choices=[
            ('IN_APP', 'درون برنامه'),
            ('SMS', 'پیامک'),
            ('EMAIL', 'ایمیل'),
            ('PUSH', 'نوتیفیکیشن')
        ],
        default='IN_APP'
    )
    
    # تحلیل رفتاری
    compliance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="نرخ تبعیت از یادآوری (درصد)"
    )
    last_pattern_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'reminder_type']
        indexes = [
            models.Index(fields=['patient', 'reminder_type']),
            models.Index(fields=['compliance_rate']),
        ]
    
    def __str__(self):
        return f"Pattern {self.reminder_type} - {self.patient.full_name}"
    
    def update_pattern(self, response_time, responded):
        """
        بروزرسانی الگوی رفتاری بر اساس پاسخ جدید
        """
        self.total_reminders_sent += 1
        if responded:
            self.total_responses += 1
            if response_time.hour not in self.best_response_times:
                self.best_response_times.append(response_time.hour)
        else:
            if response_time.hour not in self.worst_response_times:
                self.worst_response_times.append(response_time.hour)
        
        # محاسبه نرخ تبعیت
        self.compliance_rate = (self.total_responses / self.total_reminders_sent) * 100
        self.save()


class ReminderSchedule(models.Model):
    """
    برنامه‌ریزی و زمان‌بندی یادآورها
    """
    reminder = models.ForeignKey(
        SmartReminder,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    scheduled_time = models.DateTimeField()
    
    # وضعیت
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # پاسخ بیمار
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    response_time = models.DurationField(null=True, blank=True)
    
    # تلاش‌های ارسال
    attempt_count = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    
    # نتیجه
    action_taken = models.CharField(
        max_length=50,
        choices=[
            ('COMPLETED', 'انجام شد'),
            ('POSTPONED', 'به تعویق افتاد'),
            ('SKIPPED', 'رد شد'),
            ('NOT_APPLICABLE', 'قابل اجرا نیست')
        ],
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    
    # متادیتا
    created_at = models.DateTimeField(default=timezone.now)
    notification_id = models.CharField(max_length=64, null=True, blank=True)
    
    class Meta:
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['reminder', 'scheduled_time']),
            models.Index(fields=['is_sent', 'scheduled_time']),
            models.Index(fields=['is_acknowledged']),
        ]
    
    def __str__(self):
        return f"{self.reminder.title} - {self.scheduled_time}"
    
    def mark_as_sent(self):
        """
        علامت‌گذاری به عنوان ارسال شده
        """
        self.is_sent = True
        self.sent_at = timezone.now()
        self.attempt_count += 1
        self.last_attempt_at = timezone.now()
        self.save()
    
    def acknowledge(self, action_taken=None, notes=''):
        """
        ثبت پاسخ بیمار به یادآوری
        """
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        if self.sent_at:
            self.response_time = self.acknowledged_at - self.sent_at
        if action_taken:
            self.action_taken = action_taken
        if notes:
            self.notes = notes
        self.save()
        
        # بروزرسانی الگوی رفتاری
        pattern, created = ReminderPattern.objects.get_or_create(
            patient=self.reminder.patient,
            reminder_type=self.reminder.reminder_type
        )
        pattern.update_pattern(self.scheduled_time, True)


class ReminderResponse(models.Model):
    """
    تاریخچه پاسخ‌های بیمار به یادآورها برای تحلیل رفتاری
    """
    schedule = models.ForeignKey(
        ReminderSchedule,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    
    # نوع پاسخ
    response_type = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'فوری'),
            ('DELAYED', 'با تاخیر'),
            ('NO_RESPONSE', 'بدون پاسخ'),
            ('DISMISSED', 'رد شده')
        ]
    )
    
    # زمان پاسخ
    response_time = models.DateTimeField()
    response_delay = models.DurationField(
        help_text="تاخیر در پاسخ از زمان ارسال"
    )
    
    # جزئیات پاسخ
    action_result = models.CharField(
        max_length=50,
        choices=[
            ('TAKEN', 'مصرف شد'),
            ('POSTPONED', 'به تعویق افتاد'),
            ('SKIPPED', 'رد شد'),
            ('PARTIAL', 'بخشی انجام شد')
        ],
        null=True,
        blank=True
    )
    
    # بازخورد بیمار
    patient_feedback = models.TextField(blank=True)
    satisfaction_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="امتیاز رضایت (1-5)"
    )
    
    # متادیتا
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['schedule', 'response_type']),
            models.Index(fields=['response_time']),
            models.Index(fields=['satisfaction_score']),
        ]
    
    def __str__(self):
        return f"Response to {self.schedule} - {self.response_type}"