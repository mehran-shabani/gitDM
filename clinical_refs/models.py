from django.db import models
import uuid

class ClinicalReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=120)  # ADA, WHO, IDF, ESC, ...
    year = models.PositiveIntegerField()
    url = models.URLField(blank=True)
    topic = models.CharField(max_length=80)    # diabetes, hba1c, therapy, renal
    section = models.CharField(max_length=160, blank=True)  # e.g., "Glycemic Targets"
    lang = models.CharField(max_length=8, default='en')
    tags = models.JSONField(default=list, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["topic","year","source"]),
        ]