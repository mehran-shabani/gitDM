from __future__ import annotations

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import AIDigest, HealthCheckResult, Service
from .serializers import AIDigestSerializer, HealthCheckResultSerializer, ServiceSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("id")
    serializer_class = ServiceSerializer


class HealthCheckResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = HealthCheckResult.objects.select_related("service").all().order_by("-checked_at")
    serializer_class = HealthCheckResultSerializer

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        service_id = self.request.query_params.get("service")
        since = self.request.query_params.get("since")
        until = self.request.query_params.get("until")
        if service_id:
            qs = qs.filter(service_id=service_id)
        if since:
            dt_since = parse_datetime(since)
            if dt_since is not None and dt_since.tzinfo is None:
                dt_since = make_aware(dt_since)
            if dt_since is not None:
                qs = qs.filter(checked_at__gte=dt_since)
        if until:
            dt_until = parse_datetime(until)
            if dt_until is not None and dt_until.tzinfo is None:
                dt_until = make_aware(dt_until)
            if dt_until is not None:
                qs = qs.filter(checked_at__lte=dt_until)
        return qs


class AIDigestViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AIDigest.objects.select_related("service").all().order_by("-created_at")
    serializer_class = AIDigestSerializer

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request: Request) -> Response:
        service_id = request.query_params.get("service")
        qs = self.get_queryset()
        if service_id:
            qs = qs.filter(service_id=service_id)
        obj = qs.first()
        if not obj:
            return Response({"detail": "No digests"}, status=200)
        return Response(self.get_serializer(obj).data)


@api_view(["GET"])  # /api/monitor/health/summary
def health_summary(request: Request) -> Response:
    services = list(Service.objects.filter(enabled=True))
    latest_results = (
        HealthCheckResult.objects.filter(service__in=services)
        .select_related("service")
        .order_by("service_id", "-checked_at")
    )
    latest_map = {}
    for res in latest_results:
        if res.service_id not in latest_map:
            latest_map[res.service_id] = res

    last_digest = AIDigest.objects.order_by("-created_at").first()

    out = {
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "ok": latest_map.get(s.id).ok if latest_map.get(s.id) else None,
                "status_code": latest_map.get(s.id).status_code if latest_map.get(s.id) else None,
                "latency_ms": latest_map.get(s.id).latency_ms if latest_map.get(s.id) else None,
                "checked_at": latest_map.get(s.id).checked_at.isoformat() if latest_map.get(s.id) else None,
            }
            for s in services
        ],
        "latest_digest": AIDigestSerializer(last_digest).data if last_digest else None,
    }
    return Response(out)

