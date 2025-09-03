from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from .models import Service


logger = logging.getLogger("health")


async def _async_request(client: httpx.AsyncClient, method: str, url: str, headers: Dict[str, Any], timeout_s: int) -> httpx.Response:
    return await client.request(method=method.upper(), url=url, headers=headers or {}, timeout=timeout_s)


def call_health(service: Service) -> Dict[str, Any]:
    url = f"{service.base_url.rstrip('/')}{service.health_path}"
    retries = 2
    backoffs = [0.5, 1.5]
    start_ns = time.perf_counter_ns()
    status_code: Optional[int] = None
    error_text: Optional[str] = None
    response_headers: Dict[str, Any] = {}

    try:
        async def _run() -> httpx.Response:
            async with httpx.AsyncClient(follow_redirects=True, verify=True) as client:
                last_exc: Optional[Exception] = None
                for attempt in range(retries + 1):
                    try:
                        resp = await _async_request(client, service.method, url, service.headers or {}, service.timeout_s)
                        return resp
                    except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.ReadError) as exc:
                        last_exc = exc
                        if attempt < retries:
                            await asyncio.sleep(backoffs[attempt])
                        else:
                            raise
                assert False, "unreachable"

        resp: httpx.Response = asyncio.run(_run())
        status_code = resp.status_code
        response_headers = dict(resp.headers)
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"

    end_ns = time.perf_counter_ns()
    latency_ms = (end_ns - start_ns) / 1_000_000.0
    ok = status_code is not None and 200 <= status_code < 400 and error_text is None

    record = {
        "service": service.name,
        "status": status_code,
        "ok": ok,
        "latency_ms": round(latency_ms, 3),
        "error": error_text,
        "ts": time.time(),
    }
    try:
        logger.info(json.dumps(record, ensure_ascii=False))
    except Exception:
        logger.exception("Failed to log health record")

    return {
        "status_code": status_code,
        "ok": ok,
        "latency_ms": latency_ms,
        "error_text": error_text,
        "meta": {"headers": response_headers},
    }

