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
    """
    آزمایشی که ایجاد و پیوند یک Encounter به یک Patient را بررسی می‌کند.
    
    این تست یک رکورد Patient می‌سازد و سپس یک Encounter مرتبط با آن را با مقدار occurred_at معین و created_by (UUID) ایجاد می‌کند. آزمون تضمین می‌کند که Encounter به همان شیء Patient اشاره می‌کند و فیلد occurred_at مقداردهی شده است. این تست نیاز به دسترسی به پایگاه‌داده دارد و تغییرات موقتی در دیتابیس ایجاد می‌کند.
    """
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
