# کدهای الزامی – Security

## security/models.py (جدید)
from django.db import models
import uuid

class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.UUIDField(null=True, blank=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=[('admin','Admin'),('doctor','Doctor'),('viewer','Viewer')])

## security/middleware.py (جدید)
from .models import AuditLog

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            AuditLog.objects.create(
                user_id=getattr(request.user,'id',None),
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                meta={"remote_addr": request.META.get('REMOTE_ADDR')}
            )
        except Exception:
            pass
        return response

## security/permissions.py (جدید)
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user,'role') and request.user.role.role=='admin'

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user,'role') and request.user.role.role=='doctor'

## api/views_export.py (جدید)
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

## config/settings.py (به‌روزرسانی)
MIDDLEWARE += [
    'security.middleware.AuditMiddleware',
]