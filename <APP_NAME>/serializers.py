from __future__ import annotations

from rest_framework import serializers

from .models import AIDigest, HealthCheckResult, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "base_url",
            "health_path",
            "method",
            "headers",
            "timeout_s",
            "enabled",
        ]


class HealthCheckResultSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = HealthCheckResult
        fields = [
            "id",
            "service",
            "service_name",
            "status_code",
            "ok",
            "latency_ms",
            "error_text",
            "checked_at",
            "meta",
        ]


class AIDigestSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = AIDigest
        fields = [
            "id",
            "service",
            "service_name",
            "period_start",
            "period_end",
            "anomalies",
            "summary_text",
            "created_at",
        ]

