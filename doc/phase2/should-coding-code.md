# کدهای الزامی – مدل‌ها

## patients_core/models.py
from django.db import models
import uuid

class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True)
    primary_doctor_id = models.UUIDField()  # doctor مالک
    created_at = models.DateTimeField(auto_now_add=True)

## diab_encounters/models.py
from django.db import models
import uuid

class Encounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField()
    subjective = models.TextField(blank=True)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

## diab_labs/models.py
from django.db import models
import uuid

class LabResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey('diab_encounters.Encounter', null=True, blank=True, on_delete=models.SET_NULL)
    loinc = models.CharField(max_length=40)
    value = models.FloatField()
    unit = models.CharField(max_length=16)
    taken_at = models.DateTimeField()

## diab_medications/models.py
from django.db import models
import uuid

class MedicationOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    encounter = models.ForeignKey('diab_encounters.Encounter', null=True, blank=True, on_delete=models.SET_NULL)
    atc = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

## clinical_refs/models.py
from django.db import models
import uuid

class ClinicalReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=120)
    year = models.PositiveIntegerField()
    url = models.URLField(blank=True)
    topic = models.CharField(max_length=80)

## ai_summarizer/models.py
from django.db import models
import uuid

class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

## records_versioning/models.py
from django.db import models
import uuid

class RecordVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    resource_type = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    version = models.PositiveIntegerField()
    prev_version = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField()
    changed_by = models.UUIDField()
    changed_at = models.DateTimeField(auto_now_add=True)