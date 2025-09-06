from django.db import models
from django.core.validators import MinValueValidator


class Service(models.Model):
    """API service configuration for health monitoring."""
    
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField()
    health_path = models.CharField(max_length=200, default='/health')
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('HEAD', 'HEAD'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
        ],
        default='GET'
    )
    headers = models.JSONField(default=dict, blank=True)
    timeout_s = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)]
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        indexes = (
            models.Index(fields=['enabled']),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.base_url})"

    @property
    def full_url(self) -> str:
        """Get the complete health check URL."""
        return f"{self.base_url.rstrip('/')}/{self.health_path.lstrip('/')}"

class HealthCheckResult(models.Model):
    """Health check result for a service."""
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='health_results'
    )
    status_code = models.IntegerField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    latency_ms = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    error_text = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-checked_at',)
        indexes = (
            models.Index(fields=['service', '-checked_at']),
            models.Index(fields=['checked_at']),
            models.Index(fields=['ok']),
        )

    def __str__(self) -> str:
        status = self.status_code or 'Error'
        return f"{self.service.name} - {status} at {self.checked_at}"


class AIDigest(models.Model):
    """AI-generated analysis digest of health check logs."""
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='ai_digests',
        null=True,
        blank=True
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    anomalies = models.JSONField(default=list)
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = (
            models.Index(fields=['service', '-created_at']),
            models.Index(fields=['period_start', 'period_end']),
        )

    def __str__(self) -> str:
        service_name = self.service.name if self.service else 'All Services'
        return f"AI Digest for {service_name} ({self.period_start} - {self.period_end})"
