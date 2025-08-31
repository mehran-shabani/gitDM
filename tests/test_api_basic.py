import json
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
def test_token_and_create_patient():
    User.objects.create_user(email='u1@test.com', password='p1')
    c = APIClient()
    r = c.post('/api/token/', {'email': 'u1@test.com', 'password': 'p1'}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data and 'refresh' in r.data
    token = r.data['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    payload = {
        'full_name': 'Ali Test',
        # user will be set from request by serializer
    }
    r2 = c.post('/api/patients/', payload, format='json')
    assert r2.status_code == 201
    pid = r2.data['id']
    r3 = c.get(f'/api/patients/{pid}/timeline/')
    assert r3.status_code == 200
