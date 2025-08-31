from django.http import JsonResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from gitdm.models import PatientProfile


@require_GET
@login_required
def export_patient(request, pk):
    try:
        patient = PatientProfile.objects.get(pk=pk)
    except PatientProfile.DoesNotExist:
        return HttpResponseNotFound()

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