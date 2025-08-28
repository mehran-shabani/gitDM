import json
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from ai_summarizer.models import AISummary

def export_patient(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"error":"unauthorized"}, status=401)
    try:
        p = Patient.objects.get(pk=pk)
        data = {
            "patient": {"id": str(p.id), "name": p.full_name},
            "encounters": list(Encounter.objects.filter(patient=p).values()),
            "labs": list(LabResult.objects.filter(patient=p).values()),
            "medications": list(MedicationOrder.objects.filter(patient=p).values()),
            "summaries": list(AISummary.objects.filter(patient=p).values()),
        }
        return JsonResponse(data, safe=False, json_dumps_params={'cls':DjangoJSONEncoder})
    except Patient.DoesNotExist:
        return JsonResponse({"error":"not found"}, status=404)