from celery import shared_task
from ai_summarizer.services import link_references
from ai_summarizer.models import AISummary

@shared_task
def summarize_record(patient_id, resource_type, resource_id, text):
    """Summarize a medical record and link relevant clinical references."""
    # Create the summary
    summary = AISummary.objects.create(
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=resource_id,
        summary=text
    )
    
    # Link relevant references
    refs = link_references(text, topic_hint='diabetes')
    for r in refs:
        summary.references.add(r)
    
    return summary.id
