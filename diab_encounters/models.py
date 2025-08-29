
from django.db import models
from django.conf import settings
import uuid


class Encounter(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        """Encounter برای <patient> در <occurred_at>."""
        return f"Encounter for {self.patient.full_name} at {self.occurred_at}"