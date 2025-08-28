from django.db import models
import uuid


class Patient(models.Model):
    """Patient model for diabetes management system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    primary_doctor_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        
    def __str__(self):
        return self.full_name