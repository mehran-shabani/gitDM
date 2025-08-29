import uuid
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from patients_core.models import Patient
from diab_encounters.models import Encounter
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version

User = get_user_model()

@pytest.mark.django_db
def test_version_increments_on_save():
    # Create a test user (doctor)
    doctor = User.objects.create_user(username='testdoctor', password='testpass')
    
    p = Patient.objects.create(full_name='Test P', primary_doctor=doctor)
    v1 = RecordVersion.objects.filter(resource_type='Patient', resource_id=p.id, version=1).exists()
    assert v1
    p.full_name = 'Test P2'
    p.save()
    v2 = RecordVersion.objects.get(resource_type='Patient', resource_id=p.id, version=2)
    assert v2.diff is not None and 'full_name' in v2.diff

@pytest.mark.django_db
def test_revert_creates_new_version():
    # Create test users
    doctor = User.objects.create_user(username='doctor', password='testpass')
    admin = User.objects.create_user(username='admin', password='testpass')
    
    p = Patient.objects.create(full_name='Patient A', primary_doctor=doctor)
    p.full_name = 'Patient B'
    p.save()
    # revert to v1
    revert_to_version('Patient', p.id, 1, admin)
    v3 = RecordVersion.objects.get(resource_type='Patient', resource_id=p.id, version=3)
    assert v3.prev_version == 2
    from patients_core.models import Patient as P
    p2 = P.objects.get(id=p.id)
    assert p2.full_name == 'Patient A'