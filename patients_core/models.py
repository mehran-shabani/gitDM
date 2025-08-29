from django.db import models
from django.conf import settings


class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
    

    id = models.AutoField(primary_key=True)
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
        بازمی‌گرداند نام کامل بیمار به‌عنوان نمایشی از نمونهٔ Patient.
        
        این متد مقدار فیلد `full_name` را به‌صورت رشته بازمی‌گرداند و برای نمایش خوانا در رابط‌های مدیریتی، قالب‌بندی خروجی و زمانی که نمونه به رشته تبدیل می‌شود استفاده می‌شود.
        
        Returns:
            str: نام کامل بیمار
        """
        return self.full_name
