import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_token_and_create_patient():
    User.objects.create_user(username='u1', password='p1')
    c = APIClient()
    r = c.post('/api/token/', {'username': 'u1', 'password': 'p1'}, format='json')
    assert r.status_code == 200
    token = r.data['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    payload = {
        'full_name': 'Ali Test',
        'primary_doctor': 1  # Using integer ID for the system user
    }
    r2 = c.post('/api/patients/', payload, format='json')
    assert r2.status_code == 201
    pid = r2.data['id']
    r3 = c.get(f'/api/patients/{pid}/timeline/')
    assert r3.status_code == 200
