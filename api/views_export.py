from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.http import require_GET
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
import logging
from gitdm.models import PatientProfile

logger = logging.getLogger(__name__)


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_patient(request, pk):
    """
    Export patient data with proper error handling and logging
    """
    try:
        patient = PatientProfile.objects.get(pk=pk)
        logger.info(f"Patient export requested for patient {pk} by user {request.user.id}")
    except PatientProfile.DoesNotExist:
        logger.warning(f"Patient export failed: Patient {pk} not found")
        return HttpResponseNotFound()

    # Enforce ownership: only the primary_doctor can export
    user = getattr(request, "user", None)
    if not getattr(user, "is_superuser", False):
        if getattr(patient, "primary_doctor", None) != user:
            logger.warning(f"Unauthorized export attempt: User {user.id} tried to export patient {pk}")
            raise NotFound()
    
    try:
        data = {
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
            },
            "encounters": [],
            "labs": [],
            "medications": [],
            "ai_summaries": [],
        }
        logger.info(f"Patient export successful for patient {pk}")
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error during patient export for {pk}: {str(e)}")
        raise