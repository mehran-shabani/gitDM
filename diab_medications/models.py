from django.db import models
import uuid


class MedicationOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey('diab_encounters.Encounter', null=True, blank=True, on_delete=models.SET_NULL)
    atc = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        """
        یک نمایش متنی برای سفارش دارو برمی‌گرداند.
        
        نمایش به‌صورت "<نام دارو> for <نام‌و‌نام‌خانوادگی بیمار>" است و برای نمایش در پنل ادمین، لاگ‌ها و خروجی‌های متنی مدل استفاده می‌شود.
        Returns:
        	(str): رشته قالب‌بندی‌شده شامل نام دارو و مقدار `patient.full_name`.
        """
        return f"{self.name} for {self.patient.full_name}"