from django.db import models
import uuid


class LabResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey('diab_encounters.Encounter', null=True, blank=True, on_delete=models.SET_NULL)
    loinc = models.CharField(max_length=40)
    value = models.FloatField()
    unit = models.CharField(max_length=16)
    taken_at = models.DateTimeField()

    def __str__(self):
        return f"{self.loinc}: {self.value} {self.unit} for {self.patient.full_name}"