from django.http import JsonResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.http import require_GET
from gitdm.models import PatientProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from pharmacy.models import MedicationOrder
from intelligence.models import AISummary


@require_GET
@login_required
@vary_on_headers('Authorization')
def export_patient(request, pk):
    try:
        patient = PatientProfile.objects.get(pk=pk)
    except PatientProfile.DoesNotExist:
        return HttpResponseNotFound()

    user = getattr(request, 'user', None)
    if not getattr(user, 'is_superuser', False):
        if patient.primary_doctor_id != getattr(user, 'id', None):
            return JsonResponse({"detail": "Forbidden"}, status=403)

    encounters = (
        Encounter.objects.filter(patient=patient)
        .order_by('-occurred_at')
        .values('id', 'occurred_at', 'subjective', 'objective', 'assessment', 'plan', 'created_by_id')
    )
    labs = (
        LabResult.objects.filter(patient=patient)
        .order_by('-taken_at')
        .values('id', 'encounter_id', 'loinc', 'value', 'unit', 'taken_at')
    )
    meds = (
        MedicationOrder.objects.filter(patient=patient)
        .order_by('-start_date')
        .values('id', 'encounter_id', 'atc', 'name', 'dose', 'frequency', 'start_date', 'end_date')
    )
    summaries = (
        AISummary.objects.filter(patient=patient)
        .order_by('-created_at')
        .values('id', 'summary', 'created_at')
    )

    data = {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "primary_doctor_id": patient.primary_doctor_id,
        },
        "encounters": list(encounters),
        "labs": list(labs),
        "medications": list(meds),
        "ai_summaries": list(summaries),
    }
    return JsonResponse(data)