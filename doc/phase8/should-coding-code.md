# کدهای الزامی – Test Flow

## tests/test_flow_diabetes.py
import uuid
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from patients_core.models import Patient
from ai_summarizer.models import AISummary
from records_versioning.models import RecordVersion

@pytest.mark.django_db
def test_full_diabetes_flow(monkeypatch):
    # Mock OpenAI response
    monkeypatch.setattr(
        "openai.ChatCompletion.create",
        lambda **kwargs: {"choices":[{"message":{"content":"خلاصه آزمایشی"}}]}
    )

    # Create user
    u = User.objects.create_user(username='doc1', password='p1')

    c = APIClient()
    r = c.post('/api/token/', {'username':'doc1','password':'p1'}, format='json')
    token = r.data['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Create patient
    pdata = {"full_name":"Patient X","primary_doctor_id":"00000000-0000-0000-0000-000000000111"}
    r2 = c.post('/api/patients/', pdata, format='json')
    pid = r2.data['id']

    # Add encounter
    edata = {"patient":pid,"occurred_at":"2025-01-01T10:00:00Z","subjective":"خستگی","objective":{"bp":"140/90"},"assessment":{"icd10":["E11"]},"plan":{"drug":"metformin"}}
    r3 = c.post('/api/encounters/', edata, format='json')
    assert r3.status_code in (200,201)

    # Add lab
    ldata = {"patient":pid,"loinc":"4548-4","value":9.2,"unit":"%","taken_at":"2025-01-01T09:00:00Z"}
    r4 = c.post('/api/labs/', ldata, format='json')
    assert r4.status_code in (200,201)

    # Add medication
    mdata = {"patient":pid,"atc":"A10BA02","name":"Metformin","dose":"500mg","frequency":"BID","start_date":"2025-01-01"}
    r5 = c.post('/api/meds/', mdata, format='json')
    assert r5.status_code in (200,201)

    # Wait AI summary task (simulate immediate)
    summaries = AISummary.objects.filter(patient_id=pid)
    assert summaries.exists()

    # Versioning check
    versions = RecordVersion.objects.filter(resource_type='Patient',resource_id=pid)
    assert versions.count()>=1

    # Timeline
    r6 = c.get(f'/api/patients/{pid}/timeline/')
    assert r6.status_code==200
    assert 'ai_summaries' in r6.data

    # Export
    r7 = c.get(f'/api/export/patient/{pid}/')
    assert r7.status_code==200
    assert 'encounters' in r7.data