from celery import shared_task
from ai_summarizer.services import link_references
from ai_summarizer.models import AISummary

@shared_task
def create_summary_with_references(patient_id, resource_type, resource_id, text, topic_hint=None):
    """Create an AI summary record and link relevant clinical references.
    
    Args:
        patient_id: ID of the patient
        resource_type: Type of the medical resource (e.g., 'encounter', 'lab_result')
        resource_id: ID of the specific resource
        text: The summarized text content
        topic_hint: Optional topic hint for linking references (e.g., 'diabetes', 'hypertension')
    
    Returns:
        The ID of the created AISummary object
    """
    # Create the summary
    summary = AISummary.objects.create(
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=resource_id,
        summary=text
    )
    
    # Link relevant references
    refs = link_references(text, topic_hint=topic_hint)
    if refs:
        # Use unpacking to add all references in a single database query
        summary.references.add(*refs)
    
    return summary.id
