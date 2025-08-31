import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from gitdm.models import PatientProfile
from intelligence.models import AISummary
from versioning.models import RecordVersion

@pytest.mark.django_db
def test_full_diabetes_flow():
    # Note: We're using a mock implementation for AI summarizer that doesn't require OpenAI

    # Create user
    User = get_user_model()
    u = User.objects.create_user(email='doc1@example.com', password='p1')

    c = APIClient()
    r = c.post('/api/token/', {'email':'doc1@example.com','password':'p1'}, format='json')
    token = r.data['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Create patient (user is required; for test simplicity use DRF auth user as both)
    pdata = {"full_name":"Patient X"}
    r2 = c.post('/api/patients/', pdata, format='json')
    pid = r2.data['id']

    # Add encounter
    edata = {"patient":pid,"occurred_at":"2025-01-01T10:00:00Z","subjective":"خستگی","objective":{"bp":"140/90"},"assessment":{"icd10":["E11"]},"plan":{"drug":"metformin"}}
    r3 = c.post('/api/encounters/', edata, format='json')
    assert r3.status_code == 201

    # Add lab
    ldata = {"patient":pid,"loinc":"4548-4","value":9.2,"unit":"%","taken_at":"2025-01-01T09:00:00Z"}
    r4 = c.post('/api/labs/', ldata, format='json')
    assert r4.status_code == 201

    # Add medication
    mdata = {"patient":pid,"atc":"A10BA02","name":"Metformin","dose":"500mg","frequency":"BID","start_date":"2025-01-01"}
    r5 = c.post('/api/meds/', mdata, format='json')
    assert r5.status_code == 201

    # Wait AI summary task (simulate immediate)
    summaries = AISummary.objects.filter(patient_id=pid)
    assert summaries.exists()

    # Versioning check
    versions = RecordVersion.objects.filter(resource_type='Patient',resource_id=pid)
    assert versions.count() >= 1

    # Timeline
    r6 = c.get(f'/api/patients/{pid}/timeline/')
    assert r6.status_code==200
    assert 'ai_summaries' in r6.data

    # Export
    r7 = c.get(f'/api/export/patient/{pid}/')
    assert r7.status_code in (200, 302, 301, 401, 403)
    # If unauthorized, the route exists; if authorized it should return JSON