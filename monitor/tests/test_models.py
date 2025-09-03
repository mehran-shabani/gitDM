"""Tests for monitor models."""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from model_bakery import baker

from monitor.models import Service, HealthCheckResult, AIDigest


@pytest.mark.django_db
class TestServiceModel:
    """Test Service model."""
    
    def test_service_creation(self):
        """Test basic service creation."""
        service = baker.make(
            Service,
            name="TestAPI",
            base_url="https://api.test.com",
            health_path="/health",
            method="GET",
            timeout_s=5,
            enabled=True
        )
        
        assert service.name == "TestAPI"
        assert service.base_url == "https://api.test.com"
        assert service.full_health_url == "https://api.test.com/health"
        assert service.enabled is True
        assert str(service) == "TestAPI (enabled)"
    
    def test_full_health_url_property(self):
        """Test full_health_url property with different configurations."""
        service = baker.make(
            Service,
            base_url="https://api.test.com/",  # with trailing slash
            health_path="/status"
        )
        assert service.full_health_url == "https://api.test.com/status"
        
        service.base_url = "https://api.test.com"  # without trailing slash
        assert service.full_health_url == "https://api.test.com/status"
    
    def test_get_headers_dict(self):
        """Test headers processing."""
        # Dict headers
        service = baker.make(Service, headers={"X-API-Key": "test"})
        assert service.get_headers_dict() == {"X-API-Key": "test"}
        
        # Empty headers
        service = baker.make(Service, headers={})
        assert service.get_headers_dict() == {}
        
        # None/empty headers handled by default
        service = Service(name="test", base_url="https://test.com")
        service.headers = None  # This might happen in edge cases
        assert service.get_headers_dict() == {}
    
    def test_service_str_representation(self):
        """Test string representation."""
        enabled_service = baker.make(Service, name="API1", enabled=True)
        disabled_service = baker.make(Service, name="API2", enabled=False)
        
        assert str(enabled_service) == "API1 (enabled)"
        assert str(disabled_service) == "API2 (disabled)"


@pytest.mark.django_db
class TestHealthCheckResultModel:
    """Test HealthCheckResult model."""
    
    def test_health_check_result_creation(self):
        """Test basic health check result creation."""
        service = baker.make(Service)
        result = baker.make(
            HealthCheckResult,
            service=service,
            status_code=200,
            ok=True,
            latency_ms=150,
            error_text="",
        )
        
        assert result.service == service
        assert result.status_code == 200
        assert result.ok is True
        assert result.latency_ms == 150
        assert result.error_text == ""
    
    def test_status_display_property(self):
        """Test status_display property."""
        service = baker.make(Service)
        
        # Successful result
        success_result = baker.make(
            HealthCheckResult,
            service=service,
            status_code=200,
            ok=True
        )
        assert success_result.status_display == "OK (200)"
        
        # Failed result with status code
        failed_result = baker.make(
            HealthCheckResult,
            service=service,
            status_code=500,
            ok=False
        )
        assert failed_result.status_display == "FAILED (500)"
        
        # Failed result without status code
        timeout_result = baker.make(
            HealthCheckResult,
            service=service,
            status_code=None,
            ok=False
        )
        assert timeout_result.status_display == "FAILED (N/A)"
    
    def test_string_representation(self):
        """Test string representation."""
        service = baker.make(Service, name="TestAPI")
        
        # Successful check
        success_result = baker.make(
            HealthCheckResult,
            service=service,
            ok=True,
            checked_at=timezone.now()
        )
        assert "✓ TestAPI" in str(success_result)
        
        # Failed check
        failed_result = baker.make(
            HealthCheckResult,
            service=service,
            ok=False,
            checked_at=timezone.now()
        )
        assert "✗ TestAPI" in str(failed_result)


@pytest.mark.django_db
class TestAIDigestModel:
    """Test AIDigest model."""
    
    def test_ai_digest_creation(self):
        """Test basic AI digest creation."""
        service = baker.make(Service)
        start_time = timezone.now() - timezone.timedelta(hours=24)
        end_time = timezone.now()
        
        digest = baker.make(
            AIDigest,
            service=service,
            period_start=start_time,
            period_end=end_time,
            anomalies=[{"timestamp": "2024-01-01T12:00:00", "score": -0.5}],
            summary_text="Test summary"
        )
        
        assert digest.service == service
        assert digest.period_start == start_time
        assert digest.period_end == end_time
        assert digest.anomaly_count == 1
        assert digest.summary_text == "Test summary"
    
    def test_global_digest(self):
        """Test global digest (no specific service)."""
        start_time = timezone.now() - timezone.timedelta(hours=24)
        end_time = timezone.now()
        
        digest = baker.make(
            AIDigest,
            service=None,  # Global digest
            period_start=start_time,
            period_end=end_time,
            summary_text="Global summary"
        )
        
        assert digest.service is None
        assert "Global" in str(digest)
    
    def test_anomaly_count_property(self):
        """Test anomaly_count property."""
        # With list of anomalies
        digest = baker.make(
            AIDigest,
            anomalies=[{"a": 1}, {"b": 2}, {"c": 3}]
        )
        assert digest.anomaly_count == 3
        
        # Empty list
        digest = baker.make(AIDigest, anomalies=[])
        assert digest.anomaly_count == 0
        
        # Non-list (shouldn't happen but handle gracefully)
        digest = baker.make(AIDigest, anomalies={})
        assert digest.anomaly_count == 0
    
    def test_period_duration_hours_property(self):
        """Test period_duration_hours property."""
        start_time = timezone.now() - timezone.timedelta(hours=24)
        end_time = timezone.now()
        
        digest = baker.make(
            AIDigest,
            period_start=start_time,
            period_end=end_time
        )
        
        # Should be approximately 24 hours
        assert abs(digest.period_duration_hours - 24) < 0.1