from django.db import models
import uuid


class ClinicalReference(models.Model):
    """Clinical reference model for medical guidelines and standards"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=255, help_text="Topic of the clinical reference")
    content = models.TextField(help_text="Content of the clinical reference")
    source = models.CharField(max_length=255, help_text="Source organization (e.g., ADA, WHO)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clinical_references'
        
    def __str__(self):
        return f"{self.topic} - {self.source}"