from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LabResult
from ai_summarizer.tasks import summarize_record

@receiver(post_save, sender=LabResult)
def trigger_lab_summary(sender, instance, created, **kwargs):
    if created:
        payload = {"loinc": instance.loinc, "value": instance.value, "unit": instance.unit}
        summarize_record.delay(str(instance.patient_id), 'LabResult', str(instance.id), payload)