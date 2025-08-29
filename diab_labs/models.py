from django.db import models


class LabResult(models.Model):
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey(
        'diab_encounters.Encounter',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    loinc = models.CharField(max_length=40)
    value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=16)
    taken_at = models.DateTimeField()

    def __str__(self) -> str:
        """نمایش خلاصه: <loinc>: <value> <unit> for <patient>."""
        return f"{self.loinc}: {self.value} {self.unit} for {self.patient.full_name}"
