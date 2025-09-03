from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class AuditLog(models.Model):
    """
    مدل برای ثبت تمام فعالیت‌های کاربران در سیستم
    """
    class ActionType(models.TextChoices):
        CREATE = 'CREATE', 'ایجاد'
        UPDATE = 'UPDATE', 'به‌روزرسانی'
        DELETE = 'DELETE', 'حذف'
        VIEW = 'VIEW', 'مشاهده'
        LOGIN = 'LOGIN', 'ورود'
        LOGOUT = 'LOGOUT', 'خروج'
        EXPORT = 'EXPORT', 'خروجی‌گیری'
        AI_SUMMARY = 'AI_SUMMARY', 'خلاصه‌سازی AI'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ActionType.choices)
    resource_type = models.CharField(max_length=50, help_text="نوع منبع (Patient, Encounter, etc.)")
    resource_id = models.CharField(max_length=64, null=True, blank=True)
    patient_id = models.CharField(max_length=64, null=True, blank=True, help_text="ID بیمار مرتبط")
    
    # جزئیات تغییرات
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # اطلاعات درخواست
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # متادیتا
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['patient_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} {self.resource_type} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, resource_type, resource_id=None, patient_id=None, 
                   old_values=None, new_values=None, request=None, notes=""):
        """
        متد کمکی برای ثبت آسان audit logs
        """
        ip_address = None
        user_agent = ""
        
        if request:
            # استخراج IP از headers
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            patient_id=str(patient_id) if patient_id else None,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes
        )


class SecurityEvent(models.Model):
    """
    مدل برای ثبت رویدادهای امنیتی مهم
    """
    class EventType(models.TextChoices):
        FAILED_LOGIN = 'FAILED_LOGIN', 'ورود ناموفق'
        SUSPICIOUS_ACTIVITY = 'SUSPICIOUS', 'فعالیت مشکوک'
        UNAUTHORIZED_ACCESS = 'UNAUTHORIZED', 'دسترسی غیرمجاز'
        DATA_BREACH_ATTEMPT = 'BREACH_ATTEMPT', 'تلاش نقض داده'
        BULK_EXPORT = 'BULK_EXPORT', 'خروجی‌گیری انبوه'
    
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='security_events'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
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
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'resolved']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else "Anonymous"
        return f"{self.event_type} - {user_info} at {self.timestamp}"