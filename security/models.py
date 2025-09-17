from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    """
    Minimal audit log model expected by tests:
    - id: BigAutoField
    - user_id: UUIDField (nullable)
    - path, method, status_code
    - created_at: auto_now_add
    - meta: JSON (default {})
    """
    class ActionType(models.TextChoices):
        CREATE = 'CREATE', 'ایجاد'
        UPDATE = 'UPDATE', 'به‌روزرسانی'
        DELETE = 'DELETE', 'حذف'
        VIEW = 'VIEW', 'مشاهده'
        EXPORT = 'EXPORT', 'خروجی‌گیری'
    
    id = models.BigAutoField(primary_key=True)
    user_id = models.UUIDField(null=True, blank=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)
    
    # Extended fields for comprehensive audit logging
    action = models.CharField(max_length=20, choices=ActionType.choices, null=True, blank=True)
    resource_type = models.CharField(max_length=50, null=True, blank=True)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    patient_id = models.CharField(max_length=100, null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    @classmethod
    def log_action(cls, user=None, action=None, resource_type=None, resource_id=None, 
                   patient_id=None, old_values=None, new_values=None, request=None, notes=None):
        """Helper method to create audit log entries"""
        try:
            return cls.objects.create(
                user_id=user.id if user and user.is_authenticated else None,
                path=request.path if request else '',
                method=request.method if request else '',
                status_code=200,  # Default success
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                old_values=old_values,
                new_values=new_values,
                notes=notes,
                meta={'remote_addr': request.META.get('REMOTE_ADDR') if request else None}
            )
        except Exception:
            # Fallback to minimal logging
            return cls.objects.create(
                path=request.path if request else '',
                method=request.method if request else '',
                status_code=200,
                meta={'error': 'Extended logging failed'}
            )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.method} {self.path} -> {self.status_code}"


class Role(models.Model):
    """
    Simple user role binding expected by tests.
    Primary key: BigAutoField
    Enforces one-to-one per user.
    """
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    VIEWER = 'viewer'

    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=16,
        choices=[
            (ADMIN, 'Admin'),
            (DOCTOR, 'Doctor'),
            (VIEWER, 'Viewer'),
        ],
    )

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.user} -> {self.role}"


class SecurityEvent(models.Model):
    """
    Basic security event model (kept minimal for compatibility).
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

    def __str__(self):  # pragma: no cover - trivial
        user_info = getattr(self.user, 'email', None) if self.user else "Anonymous"
        return f"{self.event_type} - {user_info} at {self.timestamp}"