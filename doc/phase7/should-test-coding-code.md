# تست‌های الزامی – Security

## tests/test_security.py
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_audit_log_created(client):
    u = User.objects.create_user(username='u1', password='p1')
    client = APIClient()
    client.login(username='u1', password='p1')
    r = client.get('/health/')
    from security.models import AuditLog
    assert AuditLog.objects.filter(path='/health/').exists()

@pytest.mark.django_db
def test_export_patient_requires_auth():
    client = APIClient()
    r = client.get('/api/export/patient/00000000-0000-0000-0000-000000000111/')
    assert r.status_code == 401