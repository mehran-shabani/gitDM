from django.db import models
import uuid


class LabResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey('diab_encounters.Encounter', null=True, blank=True, on_delete=models.SET_NULL)
    loinc = models.CharField(max_length=40)
    value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=16)
    taken_at = models.DateTimeField()

    def __str__(self):
        """
        یک نمایش متنی خوانا از نمونه LabResult را برمی‌گرداند.
        
        نمایش به شکل "<LOINC>: <مقدار> <واحد> for <نام کامل بیمار>" است؛ برای مثال "4548-4: 7.2 mmol/L for علی رضایی". این رشته برای نمایش در رابط ادمین، لاگ‌ها یا رپریزنتیشن‌های متنی استفاده می‌شود و تنها شامل فیلدهای loinc، value، unit و patient.full_name است.
        """
        return f"{self.loinc}: {self.value} {self.unit} for {self.patient.full_name}"