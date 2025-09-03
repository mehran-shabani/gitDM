from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Dict, List, Tuple

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from sklearn.ensemble import IsolationForest

from .health import call_health
from .models import AIDigest, HealthCheckResult, Service

logger = logging.getLogger("health")


@shared_task(name="<APP_NAME>.tasks.run_health_checks")
def run_health_checks() -> int:
    services = list(Service.objects.filter(enabled=True))
    count = 0
    for svc in services:
        data = call_health(svc)
        with transaction.atomic():
            HealthCheckResult.objects.create(
                service=svc,
                status_code=data.get("status_code"),
                ok=bool(data.get("ok")),
                latency_ms=data.get("latency_ms"),
                error_text=data.get("error_text"),
                meta=data.get("meta") or {},
            )
        count += 1
    return count


def _summarize_text(service_to_metrics: Dict[str, Dict[str, Any]], period: Tuple[dt.datetime, dt.datetime]) -> str:
    import os

    start, end = period
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI

            client = OpenAI()
            content = [
                {
                    "type": "text",
                    "text": (
                        "Summarize API health over the period. Provide key incidents, services with highest errors/latency, critical windows, and actionable recommendations (timeouts, retries, circuit breaker, alerting). Data: "
                        + json.dumps(service_to_metrics)
                    ),
                }
            ]
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": content}],
                temperature=0.2,
                max_tokens=300,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("OpenAI summarization failed: %s", exc)

    lines: List[str] = [f"Summary for {start.isoformat()} to {end.isoformat()}"]
    by_error = sorted(
        service_to_metrics.items(),
        key=lambda kv: (kv[1].get("error_rate", 0.0), kv[1].get("p95_latency", 0.0)),
        reverse=True,
    )
    for name, m in by_error[:5]:
        lines.append(
            f"- {name}: error_rate={m.get('error_rate', 0):.2%}, p95_latency={m.get('p95_latency', 0):.0f}ms anomalies={len(m.get('anomalies', []))}"
        )
    if not by_error:
        lines.append("- No data available.")
    lines.append("Recommendations: tune timeouts, add retries with backoff, implement circuit breakers, set alerts on error_rate>2% or p95_latency>1000ms.")
    return "\n".join(lines)


def _compute_basic_metrics(results: List[HealthCheckResult]) -> Dict[str, Any]:
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    errors = [not r.ok for r in results]
    error_rate = (sum(errors) / len(errors)) if errors else 0.0
    p95 = 0.0
    if latencies:
        lat_sorted = sorted(latencies)
        idx = int(0.95 * (len(lat_sorted) - 1))
        p95 = lat_sorted[idx]
    return {"error_rate": error_rate, "p95_latency": p95}


@shared_task(name="<APP_NAME>.tasks.analyze_logs")
def analyze_logs(period_hours: int = 24) -> int:
    end = timezone.now()
    start = end - dt.timedelta(hours=period_hours)

    services = list(Service.objects.filter(enabled=True))
    digests_created = 0

    for svc in services:
        qs = (
            HealthCheckResult.objects.filter(service=svc, checked_at__gte=start, checked_at__lte=end)
            .select_related("service")
            .order_by("checked_at")
        )
        results = list(qs)
        anomalies: List[Dict[str, Any]] = []

        if results:
            X = []
            timestamps = []
            for r in results:
                lat = r.latency_ms or 0.0
                err_flag = 0 if r.ok else 1
                X.append([lat, err_flag])
                timestamps.append(r.checked_at.isoformat())
            try:
                model = IsolationForest(contamination="auto", random_state=42)
                preds = model.fit_predict(X)
                scores = model.decision_function(X)
                for i, p in enumerate(preds):
                    if p == -1:
                        anomalies.append({"ts": timestamps[i], "score": float(scores[i])})
            except Exception as exc:
                logger.warning("IsolationForest failed for %s: %s", svc.name, exc)

        metrics = _compute_basic_metrics(results)
        metrics["anomalies"] = anomalies
        summary = _summarize_text({svc.name: metrics}, (start, end))
        AIDigest.objects.create(
            service=svc,
            period_start=start,
            period_end=end,
            anomalies=anomalies,
            summary_text=summary,
        )
        digests_created += 1

    overall_results = list(
        HealthCheckResult.objects.filter(checked_at__gte=start, checked_at__lte=end)
        .select_related("service")
        .order_by("checked_at")
    )
    svc_to_metrics: Dict[str, Dict[str, Any]] = {}
    if overall_results:
        by_service: Dict[int, List[HealthCheckResult]] = {}
        for r in overall_results:
            by_service.setdefault(r.service_id, []).append(r)
        for svc_id, rs in by_service.items():
            name = rs[0].service.name
            metrics = _compute_basic_metrics(rs)
            lat = [x.latency_ms or 0.0 for x in rs]
            err = [0 if x.ok else 1 for x in rs]
            try:
                model = IsolationForest(contamination="auto", random_state=42)
                preds = model.fit_predict([[l, e] for l, e in zip(lat, err)])
                svc_anoms = []
                for i, p in enumerate(preds):
                    if p == -1:
                        svc_anoms.append({"ts": rs[i].checked_at.isoformat()})
                metrics["anomalies"] = svc_anoms
            except Exception:
                metrics["anomalies"] = []
            svc_to_metrics[name] = metrics

    summary_overall = _summarize_text(svc_to_metrics, (start, end))
    AIDigest.objects.create(
        service=None,
        period_start=start,
        period_end=end,
        anomalies=[{"service": k, "count": len(v.get("anomalies", []))} for k, v in svc_to_metrics.items()],
        summary_text=summary_overall,
    )
    digests_created += 1
    return digests_created

