from django.db import models
from django.conf import settings


class Encounter(models.Model):
    # Using Django's default BigAutoField (id field is automatically created)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
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

    def __str__(self) -> str:
        """
        رشتهٔ نمایشی کوتاه که نام کامل بیمار و زمان مواجهه را برمی‌گرداند.
        
        این متد یک نمای انسانی‌خوانا برای نمونه‌ی Encounter تولید می‌کند به صورت:
        "Encounter for {patient.full_name} at {occurred_at}"
        
        Returns:
            str: رشتهٔ نمایش شامل نام کامل بیمار و زمان وقوع مواجهه.
        """
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"
