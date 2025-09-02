from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from gitdm.models import PatientProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from pharmacy.models import MedicationOrder
from intelligence.models import AISummary

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_patient(request, pk):
    patient = get_object_or_404(PatientProfile, pk=pk)

    user = request.user
    if not getattr(user, "is_superuser", False) and patient.primary_doctor_id != user.id:
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    encounters = (
        Encounter.objects.filter(patient=patient)
        .select_related("patient", "created_by")
        .order_by("-occurred_at")
    )
    labs = (
        LabResult.objects.filter(patient=patient)
        .select_related("patient", "encounter")
        .order_by("-taken_at")
    )
    meds = (
        MedicationOrder.objects.filter(patient=patient)
        .select_related("patient", "encounter")
        .order_by("-start_date")
    )
    summaries = (
        AISummary.objects.filter(patient=patient)
        .select_related("patient", "content_type")
        .order_by("-created_at")
    )

    data = {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
        },
        "encounters": [
            {
                "id": e.id,
                "occurred_at": e.occurred_at.isoformat(),
                "subjective": e.subjective,
                "objective": e.objective,
                "assessment": e.assessment,
                "plan": e.plan,
            }
            for e in encounters
        ],
        "labs": [
            {
                "id": l.id,
                "loinc": l.loinc,
                "value": str(l.value),
                "unit": l.unit,
                "taken_at": l.taken_at.isoformat(),
            }
            for l in labs
        ],
        "medications": [
            {
                "id": m.id,
                "atc": m.atc,
                "name": m.name,
                "dose": m.dose,
                "frequency": m.frequency,
                "start_date": m.start_date.isoformat(),
                "end_date": m.end_date.isoformat() if m.end_date else None,
            }
            for m in meds
        ],
        "ai_summaries": [
            {
                "id": s.id,
                "resource_type": getattr(s.content_type, "model", None),
                "resource_id": str(s.object_id),
                "summary": s.summary,
                "created_at": s.created_at.isoformat(),
            }
            for s in summaries
        ],
    }
    return Response(data)