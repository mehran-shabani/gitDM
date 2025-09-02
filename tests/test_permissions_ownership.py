import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from gitdm.models import PatientProfile


@pytest.mark.django_db
def test_user_cannot_access_other_users_patient_and_related() -> None:
    User = get_user_model()
    doctor_a = User.objects.create_user(email="doc_a@example.com", password="p")
    doctor_b = User.objects.create_user(email="doc_b@example.com", password="p")

    pa = PatientProfile.objects.create(full_name="PA", primary_doctor=doctor_a)
    pb = PatientProfile.objects.create(full_name="PB", primary_doctor=doctor_b)

    c = APIClient()
    # Authenticate as doctor A
    c.force_authenticate(user=doctor_a)

    # A can list only their patients
    r = c.get("/api/patients/")
    assert r.status_code == 200
    ids = [item["id"] for item in r.data]
    assert pa.id in ids
    assert pb.id not in ids

    # A cannot see patient B
    r = c.get(f"/api/patients/{pb.id}/")
    assert r.status_code in (403, 404)

    # Encounters list filtered by ownership (empty initially)
    r = c.get("/api/encounters/")
    assert r.status_code == 200

    # A cannot create encounter for patient B
    enc_data = {
        "patient": pb.id,
        "occurred_at": "2025-01-01T10:00:00Z",
        "subjective": "",
        "objective": {},
        "assessment": {},
        "plan": {},
    }
    r = c.post("/api/encounters/", enc_data, format="json")
    assert r.status_code in (403, 400)

    # Create encounter for A's patient should work
    enc_data["patient"] = pa.id
    r = c.post("/api/encounters/", enc_data, format="json")
    assert r.status_code == 201
    enc_id = r.data["id"]

    # A cannot update encounter if changing patient to B's
    r = c.patch(f"/api/encounters/{enc_id}/", {"patient": pb.id}, format="json")
    assert r.status_code in (403, 400)

    # Labs: cannot create for B
    lab_data = {"patient": pb.id, "loinc": "4548-4", "value": 7.1, "unit": "%", "taken_at": "2025-01-01T09:00:00Z"}
    r = c.post("/api/labs/", lab_data, format="json")
    assert r.status_code in (403, 400)

    # Meds: cannot create for B
    med_data = {"patient": pb.id, "atc": "A10BA02", "name": "Metformin", "dose": "500mg", "frequency": "BID", "start_date": "2025-01-01"}
    r = c.post("/api/meds/", med_data, format="json")
    assert r.status_code in (403, 400)


@pytest.mark.django_db
def test_versions_endpoints_owner_only() -> None:
<!-- Removed unused import -->
    user_model = get_user_model()
    a = user_model.objects.create_user(email="own_a@example.com", password="p", is_doctor=True)
    b = user_model.objects.create_user(email="own_b@example.com", password="p", is_doctor=True)
    pa = PatientProfile.objects.create(full_name="PA", primary_doctor=a)
    c = APIClient()
    c.force_authenticate(user=b)

    # B cannot list A's patient's versions
    r = c.get(f"/api/versions/Patient/{pa.id}/")
    assert r.status_code in (403, 404)

    # B cannot revert
    r = c.post(f"/api/versions/Patient/{pa.id}/revert/", {"target_version": 1}, format="json")
    assert r.status_code in (403, 404)

    # A can list
    c.force_authenticate(user=a)
    r = c.get(f"/api/versions/Patient/{pa.id}/")
    assert r.status_code == 200


@pytest.mark.django_db
def test_export_owner_only_responses() -> None:
    user_model = get_user_model()
    a = user_model.objects.create_user(email="exp_a@example.com", password="p", is_doctor=True)
    b = user_model.objects.create_user(email="exp_b@example.com", password="p", is_doctor=True)
    pa = PatientProfile.objects.create(full_name="PA", primary_doctor=a)
    c = APIClient()

    # Unauthenticated -> 401
    r = c.get(f"/api/export/patient/{pa.id}/")
    assert r.status_code in (401, 403)

    # Authenticated as other doctor -> 403
    c.force_authenticate(user=b)
    r = c.get(f"/api/export/patient/{pa.id}/")
    assert r.status_code in (403, 404)

    # Authenticated as owner -> 200
    c.force_authenticate(user=a)
    r = c.get(f"/api/export/patient/{pa.id}/")
    assert r.status_code == 200
