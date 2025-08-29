import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from .models import AISummary
from references.models import ClinicalReference
import openai

logger = logging.getLogger(__name__)

TOPIC_KEYWORDS = {
    'diabetes': ['diabetes','hba1c','metformin','insulin','sglt2','glp-1'],
}

class OpenAIService:
    """Service class for AI GPT integration (supports both GapGPT and OpenAI APIs)"""

    def __init__(self):
        self.client = None
        self.api_provider = None

        # Prefer GapGPT if configured and enabled
        if settings.AI_SUMMARIZER_SETTINGS['USE_GAPGPT'] and settings.GAPGPT_API_KEY:
            try:
                self.client = openai.OpenAI(
                    base_url=settings.GAPGPT_BASE_URL,
                    api_key=settings.GAPGPT_API_KEY
                )
                self.api_provider = 'GapGPT'
                logger.info("Initialized GapGPT client")
            except Exception as e:
                logger.error(f"Failed to initialize GapGPT client: {e}")

        # Fallback to OpenAI if GapGPT not available
        if not self.client and settings.OPENAI_API_KEY:
            try:
                openai.api_key = settings.OPENAI_API_KEY
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self.api_provider = 'OpenAI'
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        if not self.client:
            logger.warning("No AI client configured. Summaries will use fallback truncation.")

    def generate_summary(
        self,
        content: str,
        context: Optional[str] = None,
        summary_type: str = "medical_record"
    ) -> str:
        """
        Generate AI summary using GapGPT or OpenAI GPT

        Args:
            content: The text content to summarize
            context: Optional context about the patient or medical scenario
            summary_type: Type of summary to generate (medical_record, encounter, lab_results, etc.)

        Returns:
            Generated summary text
        """
        if not self.client:
            logger.warning("AI client not configured. Falling back to truncated content.")
            return content[:500] + "..." if len(content) > 500 else content

        try:
            # Build system prompt based on summary type
            system_prompt = self._get_system_prompt(summary_type)

            # Build user message
            user_message = f"Please summarize the following medical information:\n\n{content}"
            if context:
                user_message = f"Patient Context: {context}\n\n{user_message}"

            logger.info(f"Generating summary using {self.api_provider} with model {settings.AI_SUMMARIZER_SETTINGS['MODEL']}")

            response = self.client.chat.completions.create(
                model=settings.AI_SUMMARIZER_SETTINGS['MODEL'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=settings.AI_SUMMARIZER_SETTINGS['MAX_TOKENS'],
                temperature=settings.AI_SUMMARIZER_SETTINGS['TEMPERATURE']
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary of {len(summary)} characters for content of {len(content)} characters using {self.api_provider}")
            return summary

        except Exception as e:
            logger.error(f"Error generating {self.api_provider} summary: {str(e)}")
            # Fallback to truncated content
            return content[:500] + "..." if len(content) > 500 else content

    def _get_system_prompt(self, summary_type: str) -> str:
        """Get specialized system prompt based on summary type"""
        base_prompt = settings.AI_SUMMARIZER_SETTINGS['SYSTEM_PROMPT']

        prompts = {
            "encounter": base_prompt + " Focus on the patient encounter details, symptoms, diagnoses, and treatment plans.",
            "lab_results": base_prompt + " Focus on laboratory values, reference ranges, and clinical significance of abnormal results.",
            "medications": base_prompt + " Focus on medication changes, dosages, indications, and any noted side effects or adherence issues.",
            "medical_record": base_prompt + " Provide a comprehensive summary of all medical information provided."
        }

        return prompts.get(summary_type, base_prompt)

def link_references(summary_text: str, topic_hint: str = 'diabetes') -> List[ClinicalReference]:
    """Link clinical references based on summary content and topic"""
    qs = ClinicalReference.objects.filter(topic__icontains=topic_hint)
    selected = []
    text_lower = summary_text.lower()
    for ref in qs[:20]:
        score = 0
        for kw in TOPIC_KEYWORDS.get(topic_hint, []):
            if kw in text_lower:
                score += 1
        if score:
            selected.append(ref)
    return selected[:3]

def create_ai_summary(
    content: str,
    patient_id: int,
    content_type_id: Optional[int] = None,
    object_id: Optional[str] = None,
    context: Optional[str] = None,
    summary_type: str = "medical_record",
    topic_hint: str = "diabetes"
) -> 'AISummary':
    """
    Create an AI summary using GapGPT or OpenAI GPT

    Args:
        content: Raw content to summarize
        patient_id: Patient ID
        content_type_id: Optional ContentType ID for generic foreign key
        object_id: Optional object ID for generic foreign key
        context: Optional patient context
        summary_type: Type of summary (encounter, lab_results, etc.)
        topic_hint: Topic hint for reference linking

    Returns:
        Created AISummary instance
    """
    # Generate summary using AI service
    ai_service = OpenAIService()
    summary_text = ai_service.generate_summary(content, context, summary_type)

    # Create AISummary instance
    summary = AISummary.objects.create(
        patient_id=patient_id,
        content_type_id=content_type_id,
        object_id=object_id,
        summary=summary_text
    )

    # Link relevant clinical references
    references = link_references(summary_text, topic_hint)
    if references:
        summary.references.add(*references)
        logger.info(f"Linked {len(references)} clinical references to summary {summary.id}")
    else:
        logger.info(f"No clinical references found for summary {summary.id}")

    return summary