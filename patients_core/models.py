from django.db import models
from django.conf import settings
import uuid


class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
    

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, null=True, blank=True)
    primary_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='patients',
    )  # doctor مالک
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        """
        نمایش یک نمایهٔ متنی خوانا برای نمونهٔ Patient.
        
        برمی‌گرداند نام کامل بیمار (مقدار فیلد `full_name`) به‌صورت یک رشتهٔ متنی که برای نمایش در رابط مدیریت، لاگ‌ها و انتخابگرها و هر جایی که لازم است نمایشی انسانی از شیء بیمار نشان داده شود استفاده می‌شود.
        """
        return self.full_name
