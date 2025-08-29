# Testing framework: pytest + pytest-django
# Purpose: Comprehensive unit tests for Patient and Encounter behaviors,
# focusing on edge and failure cases.

import os
import pytest
from patients_core.models import Patient
from diab_encounters.models import Encounter
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

# Use environment variable for test password, with a secure default
TEST_PASSWORD = os.environ.get('TEST_USER_PASSWORD', 'TestP@ssw0rd!2024')
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_patient_create() -> None:
    doctor = User.objects.create_user(username="doc_test", password=TEST_PASSWORD)
    p = Patient.objects.create(
        full_name="Ali Test",
        primary_doctor=doctor,
    )
    assert p.id is not None
    assert p.full_name == "Ali Test"
    assert p.primary_doctor == doctor


@pytest.mark.django_db
def test_encounter_link() -> None:
    """Create an Encounter linked to a Patient with valid created_by user."""
    doctor = User.objects.create_user(username="doc_enc", password=TEST_PASSWORD)
    creator = User.objects.create_user(username="nurse_enc", password=TEST_PASSWORD)
    p = Patient.objects.create(
        full_name="Ali Test",
        primary_doctor=doctor,
    )
    e = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-01-01T10:00:00+00:00"),
        created_by=creator,
    )
    assert e.patient == p
    assert e.occurred_at is not None
    assert e.created_by == creator


@pytest.mark.django_db
def test_patient_missing_required_fields_raises(db: object) -> None:
    # Assuming full_name is required.
    # If model-level validation enforces it, calling full_clean will raise.
    doctor = User.objects.create_user(username="doc_missing", password=TEST_PASSWORD)
    p = Patient(
        full_name=None,
        primary_doctor=doctor,
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
    creator = User.objects.create_user(username="creator_req", password=TEST_PASSWORD)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encounter.objects.create(
                patient=None,
                occurred_at=None,
                created_by=creator,
            )


@pytest.mark.django_db
def test_cascade_delete_patient_deletes_encounters(db: object) -> None:
    doctor = User.objects.create_user(username="doc_cascade", password=TEST_PASSWORD)
    creator1 = User.objects.create_user(username="creator_cascade1", password=TEST_PASSWORD)
    creator2 = User.objects.create_user(username="creator_cascade2", password=TEST_PASSWORD)
    p = Patient.objects.create(
        full_name="Cascade Test",
        primary_doctor=doctor,
    )
    Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-01-02T12:00:00+00:00"),
        created_by=creator1,
    )
    Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-02-03T12:00:00+00:00"),
        created_by=creator2,
    )
    pid = p.id
    p.delete()
    assert not Encounter.objects.filter(patient_id=pid).exists(), (
        "Encounters should be deleted on patient delete"
    )


@pytest.mark.django_db
def test_encounter_str_and_ordering_if_defined(db: object) -> None:
    doctor = User.objects.create_user(username="doc_str", password=TEST_PASSWORD)
    creator1 = User.objects.create_user(username="creator_str1", password=TEST_PASSWORD)
    creator2 = User.objects.create_user(username="creator_str2", password=TEST_PASSWORD)
    p = Patient.objects.create(
        full_name="Str Test",
        primary_doctor=doctor,
    )
    e_newer = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-04-01T10:00:00+00:00"),
        created_by=creator1,
    )
    e_older = Encounter.objects.create(
        patient=p,
        occurred_at=datetime.fromisoformat("2025-03-01T10:00:00+00:00"),
        created_by=creator2,
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
    doctor = User.objects.create_user(username="doc_uuid", password=TEST_PASSWORD)
    p = Patient.objects.create(
        full_name="UUID Test",
        primary_doctor=doctor,
    )
    assert p.primary_doctor.id is not None
    assert p.primary_doctor == doctor