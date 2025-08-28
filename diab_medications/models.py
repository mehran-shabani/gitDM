from django.db import models
from patients_core.models import Patient
import uuid


class MedicationOrder(models.Model):
    """Medication order model for diabetes treatment"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medication_orders')
    name = models.CharField(max_length=255, help_text="Medication name")
    dose = models.CharField(max_length=100, help_text="Dosage")
    frequency = models.CharField(max_length=100, help_text="Frequency of administration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medication_orders'
        
    def __str__(self):
        return f"{self.patient.full_name} - {self.name} {self.dose}"