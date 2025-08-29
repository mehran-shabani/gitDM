from django.db import models
from django.conf import settings


class Encounter(models.Model):
  id = models.AutoField(primary_key=True)
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
        نمایش متن‌توصیفی کوتاه برای شیٔ Encounter.
        
        برمی‌گرداند یک رشتهٔ خوانا که بیمار (با مقدار patient.full_name) و زمان رخداد ملاقات (occurred_at) را نشان می‌دهد؛ برای نمایش در پنل ادمین، لاگ‌ها یا هنگام تبدیل شی به رشته استفاده می‌شود.
        
        Returns:
            str: رشته‌ای به فرمت "Encounter for {patient.full_name} at {occurred_at}" که نام کامل بیمار و تاریخ/زمان وقوع را شامل می‌شود.
        """
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"
