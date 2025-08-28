# تست‌های الزامی فاز ۰۲

## tests/test_models.py
import pytest
from patients_core.models import Patient
from diab_encounters.models import Encounter

def test_patient_create(db):
    p = Patient.objects.create(full_name="Ali Test", primary_doctor_id="11111111-1111-1111-1111-111111111111")
    assert p.id is not None

def test_encounter_link(db):
    p = Patient.objects.create(full_name="Ali Test", primary_doctor_id="11111111-1111-1111-1111-111111111111")
    e = Encounter.objects.create(patient=p, occurred_at="2025-01-01T10:00Z")
    assert e.patient == p