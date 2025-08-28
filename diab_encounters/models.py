from django.db import models
from patients_core.models import Patient
import uuid


class Encounter(models.Model):
    """Encounter model for patient visits"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    subjective = models.TextField(help_text="Subjective findings")
    objective = models.TextField(help_text="Objective findings")
    assessment = models.TextField(help_text="Assessment")
    plan = models.TextField(help_text="Treatment plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'encounters'
        
    def __str__(self):
        return f"Encounter for {self.patient.full_name} - {self.created_at.date()}"