from __future__ import annotations

from typing import Any, Dict, Optional

from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=200, unique=True)
    base_url = models.URLField(max_length=500)
    health_path = models.CharField(max_length=255)
    method = models.CharField(max_length=10, default="GET")
    headers = models.JSONField(default=dict, blank=True)
    timeout_s = models.PositiveIntegerField(default=5)
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class HealthCheckResult(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="results")
    status_code = models.IntegerField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    latency_ms = models.FloatField(null=True, blank=True)
    error_text = models.TextField(null=True, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["service", "checked_at"], name="service_checked_at_idx"),
        ]
        ordering = ["-checked_at"]

    def __str__(self) -> str:
        return f"{self.service.name} @ {self.checked_at:%Y-%m-%d %H:%M:%S}"


class AIDigest(models.Model):
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="digests")
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    anomalies = models.JSONField(default=list, blank=True)
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        svc = self.service.name if self.service else "ALL"
        return f"Digest {svc} {self.period_start:%Y-%m-%d}->{self.period_end:%Y-%m-%d}"

