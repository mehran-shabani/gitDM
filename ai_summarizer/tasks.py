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