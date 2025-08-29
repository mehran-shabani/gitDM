from celery import shared_task
from .services import create_ai_summary, link_references
from .models import AISummary
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_summary_with_references(
    patient_id,
    content,
    content_type_model=None,
    object_id=None,
    context=None,
    summary_type="medical_record",
    topic_hint="diabetes"
):
    """Create an AI summary using GapGPT/OpenAI and link relevant clinical references.

    Args:
        patient_id: ID of the patient
        content: Raw content to be summarized by AI
        content_type_model: Model name for generic foreign key (e.g., 'encounter', 'lab_result')
        object_id: ID of the specific object for generic foreign key
        context: Optional patient context for better summarization
        summary_type: Type of summary for specialized prompts ('encounter', 'lab_results', 'medications', 'medical_record')
        topic_hint: Optional topic hint for linking references (e.g., 'diabetes', 'hypertension')

    Returns:
        The ID of the created AISummary object
    """
    try:
        # Get ContentType if model name provided
        content_type_id = None
        if content_type_model:
            try:
                content_type = ContentType.objects.get(model=content_type_model.lower())
                content_type_id = content_type.id
            except ContentType.DoesNotExist:
                logger.warning(f"ContentType not found for model: {content_type_model}")

        # Create AI summary using the service
        summary = create_ai_summary(
            content=content,
            patient_id=patient_id,
            content_type_id=content_type_id,
            object_id=object_id,
            context=context,
            summary_type=summary_type,
            topic_hint=topic_hint
        )

        logger.info(f"Successfully created AI summary {summary.id} for patient {patient_id}")
        return summary.id

    except Exception as e:
        logger.error(f"Error creating AI summary for patient {patient_id}: {str(e)}")
        raise

@shared_task
def generate_summary_for_existing_record(summary_id, new_content, context=None, summary_type="medical_record"):
    """Regenerate AI summary for an existing AISummary record.

    Args:
        summary_id: ID of existing AISummary
        new_content: New content to summarize
        context: Optional patient context
        summary_type: Type of summary for specialized prompts

    Returns:
        Updated AISummary ID
    """
    try:
        from .services import OpenAIService

        summary = AISummary.objects.get(id=summary_id)
        ai_service = OpenAIService()

        # Generate new summary
        new_summary_text = ai_service.generate_summary(new_content, context, summary_type)

        # Update the summary
        summary.summary = new_summary_text
        summary.save()

        logger.info(f"Successfully regenerated AI summary {summary_id}")
        return summary.id

    except AISummary.DoesNotExist:
        logger.error(f"AISummary {summary_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error regenerating AI summary {summary_id}: {str(e)}")
        raise