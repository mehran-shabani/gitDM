# تست‌های الزامی – Versioning

## tests/test_versioning_basic.py
import uuid
import pytest
from django.utils import timezone
from patients_core.models import Patient
from diab_encounters.models import Encounter
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version

@pytest.mark.django_db
def test_version_increments_on_save():
    p = Patient.objects.create(full_name='Test P', primary_doctor_id=uuid.UUID('00000000-0000-0000-0000-000000000002'))
    v1 = RecordVersion.objects.filter(resource_type='Patient', resource_id=p.id, version=1).exists()
    assert v1
    p.full_name = 'Test P2'
    p.save()
    v2 = RecordVersion.objects.get(resource_type='Patient', resource_id=p.id, version=2)
    assert v2.diff is not None and 'full_name' in v2.diff

@pytest.mark.django_db
def test_revert_creates_new_version():
    p = Patient.objects.create(full_name='Patient A', primary_doctor_id=uuid.UUID('00000000-0000-0000-0000-000000000002'))
    p.full_name = 'Patient B'
    p.save()
    # revert to v1
    revert_to_version('Patient', p.id, 1, uuid.UUID('00000000-0000-0000-0000-000000000003'))
    v3 = RecordVersion.objects.get(resource_type='Patient', resource_id=p.id, version=3)
    assert v3.prev_version == 2
    from patients_core.models import Patient as P
    p2 = P.objects.get(id=p.id)
    assert p2.full_name == 'Patient A'