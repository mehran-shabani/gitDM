from django.db import models
import uuid

class MedicationOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
