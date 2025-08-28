# تست‌های الزامی فاز ۰۱

## pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py

## tests/test_health.py
import json
from django.test import Client

def test_health_ok():
    c = Client()
    r = c.get('/health/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert data['status'] == 'ok'

## tests/test_db.py
from django.db import connection

def test_db_connects():
    with connection.cursor() as cur:
        cur.execute('SELECT 1;')
        row = cur.fetchone()
        assert row[0] == 1

## tests/test_celery.py
from config.celery import celery_app

def test_celery_registered():
    assert celery_app is not None