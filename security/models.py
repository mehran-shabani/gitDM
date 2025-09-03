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
    id = models.BigAutoField(primary_key=True)
    user_id = models.UUIDField(null=True, blank=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

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