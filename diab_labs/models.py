from django.db import models
from patients_core.models import Patient
import uuid

class Lab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='labs')
    loinc = models.CharField(max_length=20)
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    taken_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lab {self.loinc} for {self.patient.full_name}"