from django.db import models
from django.core.exceptions import ValidationError
from gitdm.validators import validate_hba1c_value, validate_blood_glucose


class LabResult(models.Model):
    patient = models.ForeignKey('gitdm.PatientProfile', on_delete=models.CASCADE)
    encounter = models.ForeignKey(
        'encounters.Encounter',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    loinc = models.CharField(max_length=40)
    value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=16)
    taken_at = models.DateTimeField()

    def clean(self):
        """
        اعتبارسنجی مقادیر آزمایش بر اساس نوع LOINC
        """
        # HbA1c validation
        if self.loinc in ['4548-4', '17856-6']:  # HbA1c LOINC codes
            validate_hba1c_value(self.value)
        
        # Blood glucose validation
        elif self.loinc in ['2345-7', '2339-0', '1558-6']:  # Glucose LOINC codes
            validate_blood_glucose(self.value)
        
        # سایر validationها بر اساس نیاز...

    def __str__(self) -> str:
        """نمایش خلاصه: <loinc>: <value> <unit> for <patient>."""
        return f"{self.loinc}: {self.value} {self.unit} for {self.patient.full_name}"