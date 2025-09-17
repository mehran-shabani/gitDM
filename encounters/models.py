from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from gitdm.validators import validate_encounter_date


class Encounter(models.Model):
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField()
    subjective = models.TextField(blank=True)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["patient", "occurred_at"]),
            models.Index(fields=["created_by", "created_at"]),
        ]

    def clean(self):
        """
        اعتبارسنجی داده‌های مواجهه
        """
        # اعتبارسنجی تاریخ مواجهه
        if self.occurred_at:
            validate_encounter_date(self.occurred_at)
        
        # بررسی اینکه created_by یک پزشک است
        if self.created_by and not getattr(self.created_by, 'is_doctor', False):
            raise ValidationError({
                'created_by': 'Only doctors can create encounters.'
            })
        
        # بررسی اینکه بیمار متعلق به همان پزشک است (اختیاری)
        if (self.created_by and self.patient and 
            hasattr(self.patient, 'primary_doctor') and 
            self.patient.primary_doctor and 
            self.patient.primary_doctor != self.created_by):
            # این فقط یک هشدار است، نه خطا
            pass

    def __str__(self) -> str:
        """
        رشتهٔ نمایشی کوتاه که نام کامل بیمار و زمان مواجهه را برمی‌گرداند.
        
        این متد یک نمای انسانی‌خوانا برای نمونه‌ی Encounter تولید می‌کند به صورت:
        "Encounter for {patient.full_name} at {occurred_at}"
        
        Returns:
            str: رشتهٔ نمایش شامل نام کامل بیمار و زمان وقوع مواجهه.
        """
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"