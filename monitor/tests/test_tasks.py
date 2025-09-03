"""Tests for Celery tasks."""

import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from model_bakery import baker

from monitor.models import Service, HealthCheckResult, AIDigest
from monitor.tasks import run_health_checks, analyze_logs, _detect_anomalies, _generate_summary


@pytest.mark.django_db
class TestHealthCheckTasks:
    """Test health check Celery tasks."""
    
    def test_run_health_checks_no_services(self):
        """Test health check task with no enabled services."""
        result = run_health_checks()
        
        assert result['status'] == 'success'
        assert result['checked_services'] == 0
    
    @patch('monitor.tasks.call_health')
    @patch('monitor.tasks._write_health_logs')
    def test_run_health_checks_success(self, mock_write_logs, mock_call_health):
        """Test successful health check execution."""
        # Create test services
        services = baker.make(Service, enabled=True, _quantity=2)
        
        # Mock health check responses
        mock_call_health.return_value = {
            'status_code': 200,
            'ok': True,
            'latency_ms': 150,
            'error_text': '',
            'meta': {'test': True}
        }
        
        result = run_health_checks()
        
        assert result['status'] == 'success'
        assert result['checked_services'] == 2
        assert len(result['results']) == 2
        
        # Check database records were created
        assert HealthCheckResult.objects.count() == 2
        
        # Check log writing was called
        mock_write_logs.assert_called_once()
        assert mock_call_health.call_count == 2
    
    @patch('monitor.tasks.call_health')
    def test_run_health_checks_with_failures(self, mock_call_health):
        """Test health check with some failures."""
        service = baker.make(Service, enabled=True, name="FailingAPI")
        
        mock_call_health.return_value = {
            'status_code': 500,
            'ok': False,
            'latency_ms': 2000,
            'error_text': 'Internal Server Error',
            'meta': {}
        }
        
        result = run_health_checks()
        
        assert result['status'] == 'success'
        assert result['checked_services'] == 1
        
        # Check failed result was recorded
        health_result = HealthCheckResult.objects.first()
        assert health_result.ok is False
        assert health_result.status_code == 500
        assert health_result.error_text == 'Internal Server Error'
    
    @patch('monitor.tasks.call_health')
    def test_run_health_checks_exception_handling(self, mock_call_health):
        """Test health check task exception handling."""
        baker.make(Service, enabled=True)
        
        mock_call_health.side_effect = Exception("Network error")
        
        result = run_health_checks()
        
        assert result['status'] == 'success'  # Task completes despite service errors
        
        # Check error was recorded
        health_result = HealthCheckResult.objects.first()
        assert health_result.ok is False
        assert "Task error" in health_result.error_text


@pytest.mark.django_db
class TestAIAnalysisTasks:
    """Test AI analysis tasks."""
    
    def test_analyze_logs_no_data(self):
        """Test log analysis with no data."""
        result = analyze_logs(period_hours=24)
        
        assert result['status'] == 'no_data'
        assert result['period_hours'] == 24
    
    @patch('monitor.tasks._generate_summary')
    @patch('monitor.tasks._detect_anomalies')
    @patch('monitor.tasks._generate_global_summary')
    @patch('monitor.tasks._detect_global_anomalies')
    def test_analyze_logs_with_data(self, mock_global_anomalies, mock_global_summary, 
                                   mock_detect_anomalies, mock_generate_summary):
        """Test log analysis with health check data."""
        # Create test data
        service = baker.make(Service, enabled=True, name="TestAPI")
        baker.make(
            HealthCheckResult,
            service=service,
            checked_at=timezone.now(),
            _quantity=10
        )
        
        # Mock analysis functions
        mock_detect_anomalies.return_value = [{"timestamp": "2024-01-01", "score": -0.5}]
        mock_generate_summary.return_value = "Service summary"
        mock_global_anomalies.return_value = []
        mock_global_summary.return_value = "Global summary"
        
        result = analyze_logs(period_hours=24)
        
        assert result['status'] == 'success'
        assert result['period_hours'] == 24
        assert 'TestAPI' in result['services_analyzed']
        
        # Check AI digests were created
        assert AIDigest.objects.count() == 2  # Service + Global
        
        service_digest = AIDigest.objects.filter(service=service).first()
        assert service_digest.summary_text == "Service summary"
        
        global_digest = AIDigest.objects.filter(service=None).first()
        assert global_digest.summary_text == "Global summary"


class TestAnomalyDetection:
    """Test anomaly detection functions."""
    
    def test_detect_anomalies_insufficient_data(self):
        """Test anomaly detection with insufficient data."""
        # Create mock results (less than 10)
        results = [MagicMock(latency_ms=100, ok=True, checked_at=timezone.now()) for _ in range(5)]
        
        anomalies = _detect_anomalies(results)
        assert anomalies == []
    
    def test_detect_anomalies_with_outliers(self):
        """Test anomaly detection with clear outliers."""
        # Create mock results with one clear outlier
        results = []
        base_time = timezone.now()
        
        # Normal results
        for i in range(15):
            result = MagicMock()
            result.latency_ms = 100 + (i * 5)  # Normal latency range
            result.ok = True
            result.checked_at = base_time + timezone.timedelta(minutes=i)
            results.append(result)
        
        # Add outlier
        outlier = MagicMock()
        outlier.latency_ms = 5000  # Very high latency
        outlier.ok = False
        outlier.checked_at = base_time + timezone.timedelta(minutes=16)
        results.append(outlier)
        
        anomalies = _detect_anomalies(results)
        
        # Should detect at least one anomaly
        assert len(anomalies) >= 1
        assert all('timestamp' in a for a in anomalies)
        assert all('anomaly_score' in a for a in anomalies)


class TestSummaryGeneration:
    """Test summary generation functions."""
    
    def test_generate_summary_basic(self):
        """Test basic summary generation."""
        service = baker.make(Service, name="TestAPI")
        
        # Create mock results
        results = []
        for i in range(10):
            result = MagicMock()
            result.ok = i < 8  # 80% success rate
            result.latency_ms = 100 + (i * 10)
            results.append(result)
        
        anomalies = [{"timestamp": "2024-01-01", "latency_ms": 500}]
        
        summary = _generate_summary(service, results, anomalies)
        
        assert "TestAPI" in summary
        assert "80.0%" in summary  # Success rate
        assert "1" in summary  # Anomaly count
        assert "Recommendations" in summary
    
    def test_generate_summary_perfect_service(self):
        """Test summary for perfectly healthy service."""
        service = baker.make(Service, name="PerfectAPI")
        
        # All successful results
        results = []
        for i in range(10):
            result = MagicMock()
            result.ok = True
            result.latency_ms = 100
            results.append(result)
        
        anomalies = []
        
        summary = _generate_summary(service, results, anomalies)
        
        assert "PerfectAPI" in summary
        assert "100.0%" in summary  # Perfect success rate
        assert "0" in summary  # No anomalies