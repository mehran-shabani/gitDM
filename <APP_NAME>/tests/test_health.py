from __future__ import annotations

import httpx
from model_bakery import baker

from <APP_NAME>.health import call_health
from <APP_NAME>.models import Service


class DummyResponse:
    def __init__(self, status_code: int = 200, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}


def test_call_health_success(monkeypatch):
    svc: Service = baker.prepare(
        Service,
        name="X",
        base_url="https://example.com",
        health_path="/health",
        method="GET",
        headers={},
        timeout_s=1,
    )

    async def fake_request(*args, **kwargs):
        return DummyResponse(200)

    monkeypatch.setattr("<APP_NAME>.health._async_request", fake_request)
    result = call_health(svc)
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["latency_ms"] >= 0


def test_call_health_retry_then_fail(monkeypatch):
    svc: Service = baker.prepare(
        Service,
        name="X",
        base_url="https://example.com",
        health_path="/health",
        method="GET",
        headers={},
        timeout_s=1,
    )

    async def fake_request(*args, **kwargs):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr("<APP_NAME>.health._async_request", fake_request)
    res = call_health(svc)
    assert res["ok"] is False
    assert res["status_code"] is None
    assert isinstance(res["error_text"], str)

