from django.db import models
from patients_core.models import Patient
from clinical_refs.models import ClinicalReference
import uuid


class AISummary(models.Model):
    """AI-generated summary for patient records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ai_summaries')
    resource_type = models.CharField(max_length=50, help_text="Type of resource (Encounter, LabResult, MedicationOrder)")
    resource_id = models.UUIDField(help_text="ID of the resource being summarized")
    summary = models.TextField(help_text="AI-generated summary")
    references = models.ManyToManyField(ClinicalReference, blank=True, help_text="Related clinical references")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_summaries'
        
    def __str__(self):
        return f"AI Summary for {self.patient.full_name} - {self.resource_type}"