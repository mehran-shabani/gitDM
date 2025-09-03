from django.db import models
from django.utils import timezone
from typing import Dict, Any
import json


class Service(models.Model):
    """Service configuration for health monitoring."""
    
    name = models.CharField(max_length=100, unique=True, help_text="Service name")
    base_url = models.URLField(help_text="Base URL of the service")
    health_path = models.CharField(
        max_length=200, 
        default="/health", 
        help_text="Health check endpoint path"
    )
    method = models.CharField(
        max_length=10, 
        choices=[("GET", "GET"), ("POST", "POST"), ("HEAD", "HEAD")],
        default="GET",
        help_text="HTTP method for health check"
    )
    headers = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Custom headers as JSON object"
    )
    timeout_s = models.PositiveIntegerField(
        default=5,
        help_text="Request timeout in seconds"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether this service is actively monitored"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self) -> str:
        return f"{self.name} ({'enabled' if self.enabled else 'disabled'})"

    @property
    def full_health_url(self) -> str:
        """Get the complete health check URL."""
        return f"{self.base_url.rstrip('/')}{self.health_path}"

    def get_headers_dict(self) -> Dict[str, str]:
        """Get headers as a dictionary."""
        if isinstance(self.headers, dict):
            return self.headers
        try:
            return json.loads(self.headers) if self.headers else {}
        except (json.JSONDecodeError, TypeError):
            return {}


class HealthCheckResult(models.Model):
    """Result of a health check for a service."""
    
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE, 
        related_name='health_results'
    )
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ok = models.BooleanField(help_text="Whether the health check was successful")
    latency_ms = models.PositiveIntegerField(
        help_text="Response time in milliseconds"
    )
    error_text = models.TextField(
        blank=True, 
        help_text="Error message if health check failed"
    )
    checked_at = models.DateTimeField(default=timezone.now)
    meta = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional metadata about the check"
    )

    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['service', 'checked_at']),
            models.Index(fields=['checked_at']),
            models.Index(fields=['ok']),
        ]
        verbose_name = "Health Check Result"
        verbose_name_plural = "Health Check Results"

    def __str__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"{status} {self.service.name} - {self.checked_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def status_display(self) -> str:
        """Human-readable status."""
        if self.ok:
            return f"OK ({self.status_code})"
        return f"FAILED ({self.status_code or 'N/A'})"


class AIDigest(models.Model):
    """AI-generated analysis digest of health check data."""
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_digests',
        help_text="Specific service (null for global analysis)"
    )
    period_start = models.DateTimeField(help_text="Start of analysis period")
    period_end = models.DateTimeField(help_text="End of analysis period")
    anomalies = models.JSONField(
        default=list,
        help_text="Detected anomalies with timestamps and scores"
    )
    summary_text = models.TextField(
        help_text="AI-generated summary and recommendations"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['period_start', 'period_end']),
        ]
        verbose_name = "AI Digest"
        verbose_name_plural = "AI Digests"

    def __str__(self) -> str:
        service_name = self.service.name if self.service else "Global"
        return f"AI Digest: {service_name} ({self.period_start.date()} - {self.period_end.date()})"

    @property
    def anomaly_count(self) -> int:
        """Number of detected anomalies."""
        return len(self.anomalies) if isinstance(self.anomalies, list) else 0

    @property
    def period_duration_hours(self) -> float:
        """Duration of analysis period in hours."""
        delta = self.period_end - self.period_start
        return delta.total_seconds() / 3600