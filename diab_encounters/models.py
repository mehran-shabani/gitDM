from django.db import models
from patients_core.models import Patient
import uuid

class Encounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    occurred_at = models.DateTimeField()
    subjective = models.TextField(blank=True)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Encounter {self.id} for {self.patient.full_name}"