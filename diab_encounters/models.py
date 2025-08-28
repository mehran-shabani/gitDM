from django.db import models
import uuid


class Encounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField()
    subjective = models.TextField(blank=True)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"