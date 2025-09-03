from __future__ import annotations

import datetime as dt

from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from <APP_NAME>.models import AIDigest, HealthCheckResult, Service


def test_health_summary_endpoint(db):
    svc1 = baker.make(Service, enabled=True, name="A")
    svc2 = baker.make(Service, enabled=True, name="B")
    now = timezone.now()
    baker.make(HealthCheckResult, service=svc1, ok=True, status_code=200, latency_ms=123.4, checked_at=now)
    baker.make(HealthCheckResult, service=svc2, ok=False, status_code=500, latency_ms=456.7, checked_at=now)
    AIDigest.objects.create(service=None, period_start=now - dt.timedelta(hours=24), period_end=now, anomalies=[], summary_text="ok")

    client = APIClient()
    url = "/api/monitor/health/summary"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert len(data["services"]) == 2
    assert data["latest_digest"] is not None

