from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
import uuid


class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def resource_type(self) -> str:
        """Backward-compatible property for admin display."""
        return self.content_type.model
    
    resource_type.fget.short_description = "Resource Type"  # type: ignore

    def clean(self) -> None:
        """Validate that content_object's patient matches self.patient if applicable."""
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self) -> str:
from __future__ import annotations

    def resource_type(self: "AISummary") -> str:
        """Backward-compatible property for admin display."""
        return self.content_type.model

    def clean(self: "AISummary") -> None:
        """Validate that content_object's patient matches self.patient if applicable."""
        if self.content_object and hasattr(self.content_object, 'patient'):
            if self.content_object.patient != self.patient:
                raise ValidationError({
                    'patient': 'Patient mismatch: The selected patient must match the patient of the related object.'
                })

    def __str__(self: "AISummary") -> str:
        """Admin label: 'AI Summary for <patient> - <model>'."""
        return f"AI Summary for {self.patient.full_name} - {self.content_type.model}"


