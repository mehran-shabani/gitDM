import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from gitdm.models import PatientProfile


@pytest.mark.django_db
def test_export_requires_auth_and_ownership() -> None:
    client = APIClient()
    # Unauthenticated should be 401/403
    resp = client.get("/api/export/patient/1/")
    assert resp.status_code in (401, 403)

    user_model = get_user_model()
    owner = user_model.objects.create_user(email="exp_owner@example.com", password="p", is_doctor=True)
    other = user_model.objects.create_user(email="exp_other@example.com", password="p", is_doctor=True)
    p = PatientProfile.objects.create(full_name="PA", primary_doctor=owner)

    # Auth as other doctor -> 403/404
    client.force_authenticate(user=other)
    resp = client.get(f"/api/export/patient/{p.id}/")
    assert resp.status_code in (403, 404)

    # Auth as owner -> 200
    client.force_authenticate(user=owner)
    resp = client.get(f"/api/export/patient/{p.id}/")
    assert resp.status_code == 200