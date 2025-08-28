from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MedicationOrder
from ai_summarizer.tasks import summarize_record

@receiver(post_save, sender=MedicationOrder)
def trigger_med_summary(sender, instance, created, **kwargs):
    if created:
        payload = {"drug": instance.name, "dose": instance.dose, "freq": instance.frequency}
        summarize_record.delay(str(instance.patient_id), 'MedicationOrder', str(instance.id), payload)