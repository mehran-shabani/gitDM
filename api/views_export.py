from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.http import require_GET
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from gitdm.models import PatientProfile


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_patient(request, pk):
    try:
        patient = PatientProfile.objects.get(pk=pk)
    except PatientProfile.DoesNotExist:
        return HttpResponseNotFound()

from rest_framework.exceptions import NotFound

    # Enforce ownership: only the primary_doctor can export
    user = getattr(request, "user", None)
    if not getattr(user, "is_superuser", False):
        if getattr(patient, "primary_doctor", None) != user:
            # Avoid leaking existence of the patient to non-owners
            raise NotFound()
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
    return JsonResponse(data)