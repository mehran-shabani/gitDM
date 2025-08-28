# کدهای الزامی – AI Integration

## ai_summarizer/tasks.py
import os, json
from celery import shared_task
import openai
from django.utils import timezone
from ai_summarizer.models import AISummary
from patients_core.models import Patient
from clinical_refs.models import ClinicalReference

openai.api_key = os.getenv('OPENAI_API_KEY')

@shared_task(bind=True, max_retries=3)
def summarize_record(self, patient_id, resource_type, resource_id, payload):
    try:
        prompt = f"خلاصه‌سازی پرونده پزشکی {resource_type}:\n{json.dumps(payload, ensure_ascii=False)}"
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"تو یک پزشک هستی"},{"role":"user","content":prompt}],
            temperature=0.2,
            max_tokens=300
        )
        text = response['choices'][0]['message']['content']
        summary = AISummary.objects.create(
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            summary=text,
            created_at=timezone.now()
        )
        # پیوند به رفرنس ADA
        ref = ClinicalReference.objects.filter(topic__icontains='diabetes').first()
        if ref:
            summary.references.add(ref)
        return summary.id
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

## diab_encounters/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Encounter
from ai_summarizer.tasks import summarize_record

@receiver(post_save, sender=Encounter)
def trigger_enc_summary(sender, instance, created, **kwargs):
    if created:
        payload = {
            "subjective": instance.subjective,
            "objective": instance.objective,
            "assessment": instance.assessment,
            "plan": instance.plan,
        }
        summarize_record.delay(str(instance.patient_id), 'Encounter', str(instance.id), payload)

## diab_labs/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LabResult
from ai_summarizer.tasks import summarize_record

@receiver(post_save, sender=LabResult)
def trigger_lab_summary(sender, instance, created, **kwargs):
    if created:
        payload = {"loinc": instance.loinc, "value": instance.value, "unit": instance.unit}
        summarize_record.delay(str(instance.patient_id), 'LabResult', str(instance.id), payload)

## diab_medications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MedicationOrder
from ai_summarizer.tasks import summarize_record

@receiver(post_save, sender=MedicationOrder)
def trigger_med_summary(sender, instance, created, **kwargs):
    if created:
        payload = {"drug": instance.name, "dose": instance.dose, "freq": instance.frequency}
        summarize_record.delay(str(instance.patient_id), 'MedicationOrder', str(instance.id), payload)