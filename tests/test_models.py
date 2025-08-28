# Testing framework: pytest + pytest-django
# Purpose: Comprehensive unit tests for Patient and Encounter behaviors,
# focusing on edge and failure cases.

import pytest
from patients_core.models import Patient
from diab_encounters.models import Encounter
from datetime import datetime
import uuid
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

@pytest.mark.django_db
def test_patient_create() -> None:
    p = Patient.objects.create(
        full_name="Ali Test",
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    assert p.id is not None
    assert p.full_name == "Ali Test"


@pytest.mark.django_db
def test_encounter_link() -> None:
    """
    آزمایشی که ایجاد و پیوند یک Encounter به یک Patient را بررسی می‌کند.

    این تست یک رکورد Patient می‌سازد و سپس یک Encounter مرتبط با آن را با مقدار
    occurred_at معین و created_by (UUID) ایجاد می‌کند.
    آزمون تضمین می‌کند که Encounter به همان شیء Patient اشاره می‌کند
    و فیلد occurred_at مقداردهی شده است.
    این تست نیاز به دسترسی به پایگاه‌داده دارد و تغییرات موقتی در دیتابیس ایجاد می‌کند.
    """
    p = Patient.objects.create(
        full_name="Ali Test",
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    e = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-01-01T10:00:00+00:00"),
        created_by=uuid.UUID("22222222-2222-2222-2222-222222222222"),
    )
    assert e.patient == p
    assert e.occurred_at is not None


@pytest.mark.django_db
def test_patient_missing_required_fields_raises(db: object) -> None:
    # Assuming full_name is required.
    # If model-level validation enforces it, calling full_clean will raise.
    p = Patient(
        full_name=None,
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    with pytest.raises((ValidationError, IntegrityError)):
        # Try full_clean first if available; fall back to save in a transaction
        try:
            p.full_clean()
            p.save()
        except Exception as e:
            raise e


@pytest.mark.django_db
def test_encounter_requires_patient_and_occurred_at(db: object) -> None:
    # Attempt to create encounter without patient or occurred_at should fail.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encounter.objects.create(
                patient=None,
                occurred_at=None,
                created_by=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            )


@pytest.mark.django_db
def test_cascade_delete_patient_deletes_encounters(db: object) -> None:
    p = Patient.objects.create(
        full_name="Cascade Test",
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-01-02T12:00:00+00:00"),
        created_by=uuid.UUID("22222222-2222-2222-2222-222222222222"),
    )
    Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-02-03T12:00:00+00:00"),
        created_by=uuid.UUID("33333333-3333-3333-3333-333333333333"),
    )
    pid = p.id
    p.delete()
    assert not Encounter.objects.filter(patient_id=pid).exists(), (
        "Encounters should be deleted on patient delete"
    )


@pytest.mark.django_db
def test_encounter_str_and_ordering_if_defined(db: object) -> None:
    p = Patient.objects.create(
        full_name="Str Test",
        primary_doctor_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    e_newer = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-04-01T10:00:00+00:00"),
        created_by=uuid.UUID("44444444-4444-4444-4444-444444444444"),
    )
    e_older = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-03-01T10:00:00+00:00"),
        created_by=uuid.UUID("55555555-5555-5555-5555-555555555555"),
    )
    # __str__ should be a non-empty string if defined
    assert isinstance(str(e_newer), str)
    assert str(e_newer).strip() != ""

    # If Meta.ordering is set (commonly by -occurred_at), ensure queryset respects it.
    # We don't know exact default ordering.
    # Assert that explicit order_by yields chronological results.
    default = list(Encounter.objects.filter(patient=p).values_list("id", flat=True))
    sorted_by_occurred = list(
        Encounter.objects.filter(patient=p)
        .order_by("occurred_at")
        .values_list("id", flat=True)
    )
    # If default ordering differs, explicit ordering ensures chronological order
    assert set(default) == set(sorted_by_occurred)
    assert sorted_by_occurred == [e_older.id, e_newer.id]


@pytest.mark.django_db
def test_patient_uuid_fields_accept_valid_uuid(db: object) -> None:
    p = Patient.objects.create(
        full_name="UUID Test",
        primary_doctor_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    )
    assert isinstance(p.primary_doctor_id, uuid.UUID)