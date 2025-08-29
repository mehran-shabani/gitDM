from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import uuid


class MedicationOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'patients_core.Patient',
        on_delete=models.CASCADE,
        related_name='medication_orders',
    )
    encounter = models.ForeignKey(
        'diab_encounters.Encounter',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='medication_orders',
    )
    atc = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date", "-id"]
        indexes = [
            models.Index(fields=["patient", "start_date"]),
            models.Index(fields=["patient", "end_date"]),
            models.Index(fields=["atc"]),
        ]

    def clean(self) -> None:
        """Validate that end_date is not before start_date."""
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'End date cannot be before start date.'
            })

    def __str__(self) -> str:
        """نمایش کوتاه: "<نام دارو> for <نام کامل بیمار>"."""
        patient_name = getattr(self.patient, "full_name", str(self.patient))
        return f"{self.name} for {patient_name}"