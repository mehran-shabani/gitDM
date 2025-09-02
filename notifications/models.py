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