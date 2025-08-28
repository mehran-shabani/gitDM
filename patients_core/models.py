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
    primary_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='patients')  # doctor مالک
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        رشته‌ای قابل‌خواندن برای نمونه Patient برمی‌گرداند.
        
        این متد نمایشی انسانی (human-readable) از شیء Patient را بازمی‌گرداند؛ مقدار فیلد `full_name` را به‌عنوان نمایش متنی نمونه برمی‌گرداند که در Django admin، لاگ‌ها و تبدیل به رشته استفاده می‌شود.
        
        Returns:
        	str: مقدار `full_name` بیمار.
        """
        return self.full_name