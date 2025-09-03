from __future__ import annotations

import datetime as dt

from django.utils import timezone
from model_bakery import baker

from <APP_NAME>.models import HealthCheckResult, Service
from <APP_NAME>.tasks import analyze_logs, run_health_checks


def test_run_health_checks_creates_results(monkeypatch, db):
    svc = baker.make(Service, enabled=True)

    def fake_call_health(service):
        return {"status_code": 200, "ok": True, "latency_ms": 10.0, "error_text": None, "meta": {}}

    monkeypatch.setattr("<APP_NAME>.tasks.call_health", fake_call_health)
    count = run_health_checks()
    assert count == 1
    assert HealthCheckResult.objects.filter(service=svc).count() == 1


def test_analyze_logs_creates_digests(db):
    svc = baker.make(Service, enabled=True, name="S")
    now = timezone.now()
    for i in range(10):
        baker.make(
            HealthCheckResult,
            service=svc,
            ok=(i % 3 != 0),
            status_code=200 if i % 3 != 0 else 500,
            latency_ms=50 + i * 5,
            checked_at=now - dt.timedelta(minutes=60 - i),
        )
    created = analyze_logs(period_hours=24)
    assert created == 2

