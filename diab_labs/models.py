from django.db import models
from patients_core.models import Patient
import uuid


class LabResult(models.Model):
    """Lab result model for diabetes monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    loinc = models.CharField(max_length=20, help_text="LOINC code for the lab test")
    value = models.FloatField(help_text="Lab test value")
    unit = models.CharField(max_length=50, help_text="Unit of measurement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lab_results'
        
    def __str__(self):
        return f"{self.patient.full_name} - {self.loinc}: {self.value} {self.unit}"