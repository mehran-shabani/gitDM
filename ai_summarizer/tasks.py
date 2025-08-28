from django.utils import timezone
from .models import AISummary
from patients_core.models import Patient

def generate_ai_summary(patient_id):
    """Generate AI summary for a patient (mock implementation for testing)"""
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Mock AI summary content
        summary_content = "خلاصه آزمایشی"
        
        # Create AI summary
        summary = AISummary.objects.create(
            patient=patient,
            content=summary_content
        )
        
        return summary
    except Exception as e:
        # In a real implementation, we'd log this error
        pass

# For testing without Celery, we'll make this synchronous
generate_ai_summary.delay = generate_ai_summary