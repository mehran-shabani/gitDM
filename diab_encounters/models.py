from django.db import models
from django.conf import settings
import uuid


class Encounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField()
    subjective = models.TextField(blank=True)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        یک نمایش متنی خوانا از شیء Encounter برمی‌گرداند.
        
        این متد یک رشته انسانی‌خوانا تولید می‌کند که برای نمایش در مدیریت Django، لاگ‌ها یا لیست‌ها مناسب است؛ رشته شامل نام کامل بیمار (patient.full_name) و زمان وقوع ملاقات (occurred_at) است. مقدار بازگشتی نشان‌دهندهٔ همان فیلدهای مدل است و فرمت دقیق تاریخ/زمان مطابق با نمایش `occurred_at` (قابل شامل زمان و منطقه زمانی در صورت وجود) خواهد بود.
        
        Returns:
            str: نمایش متنی شامل نام بیمار و زمان وقوع ملاقات.
        """
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"