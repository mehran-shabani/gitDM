import pytest
from patients_core.models import Patient
from diab_encounters.models import Encounter
from datetime import datetime
import uuid


@pytest.mark.django_db
def test_patient_create():
    p = Patient.objects.create(
        full_name="Ali Test", 
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111")
    )
    assert p.id is not None
    assert p.full_name == "Ali Test"


@pytest.mark.django_db
def test_encounter_link():
    p = Patient.objects.create(
        full_name="Ali Test", 
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111")
    )
    e = Encounter.objects.create(
        patient=p, 
        occurred_at=datetime.fromisoformat("2025-01-01T10:00:00+00:00"),
        created_by=uuid.UUID("22222222-2222-2222-2222-222222222222")
    )
    assert e.patient == p
    assert e.occurred_at is not None
