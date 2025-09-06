"""
Tests for Celery tasks.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import timedelta
from django.utils import timezone
from model_bakery import baker

from monitor.models import Service, HealthCheckResult, AIDigest
from monitor.tasks import run_health_checks, analyze_logs, generate_summary


@pytest.mark.django_db
class TestRunHealthChecks:
    """Test cases for run_health_checks task."""
    
    @patch('monitor.tasks.call_health')
    def test_run_health_checks_success(self, mock_call_health):
        """Test successful health checks for multiple services."""
        # Create test services
        service1 = baker.make(Service, name='Service1', enabled=True)
        service2 = baker.make(Service, name='Service2', enabled=True)
        baker.make(Service, name='Service3', enabled=False)  # Disabled
        
        # Mock health check results
        mock_call_health.side_effect = [
            {
                'status_code': 200,
                'ok': True,
                'latency_ms': 150.5,
                'error': None,
                'attempt': 1
            },
            {
                'status_code': 503,
                'ok': False,
                'latency_ms': 2000.0,
                'error': 'Service unavailable',
                'attempt': 3
            }
        ]
        
        result = run_health_checks()
        
        # Verify correct number of checks
        assert result['checked'] == 2
        assert result['successful'] == 1
        assert result['failed'] == 1
        assert result['errors'] == 0
        
        # Verify health results were created
        assert HealthCheckResult.objects.count() == 2
        
        # Check first result
        result1 = HealthCheckResult.objects.filter(service=service1).first()
        assert result1.status_code == 200
        assert result1.ok is True
        assert result1.latency_ms == 150.5
        assert result1.error_text == ""
        
        # Check second result
        result2 = HealthCheckResult.objects.filter(service=service2).first()
        assert result2.status_code == 503
        assert result2.ok is False
        assert result2.error_text == 'Service unavailable'
    @patch('monitor.tasks.call_health')
    def test_run_health_checks_with_exception(self, mock_call_health):
        """Test health checks handling exceptions."""
        baker.make(Service, name='Service1', enabled=True)
        
        # Mock exception during health check
        mock_call_health.side_effect = Exception("Unexpected error")
        
        result = run_health_checks()
        
        assert result['checked'] == 0
        assert result['errors'] == 1
        
        # No health result should be created
        assert HealthCheckResult.objects.count() == 0

@pytest.mark.django_db
class TestAnalyzeLogs:
    """Test cases for analyze_logs task."""
    
    def test_analyze_logs_no_data(self):
        """Test analyze_logs with no data."""
        result = analyze_logs(period_hours=24)
        
        assert result['status'] == 'no_data'
        assert AIDigest.objects.count() == 0
    
    @patch('monitor.tasks.IsolationForest')
    def test_analyze_logs_with_anomalies(self, mock_isolation_forest):
        """Test analyze_logs detects anomalies."""
        # Create test data
        service_obj = baker.make(Service, name='TestService')
        now = timezone.now()

        # Create health results with varying latencies
        for i in range(20):
            latency = 100 if i < 18 else 5000  # 2 anomalies
            baker.make(
                HealthCheckResult,
                service=service_obj,
                status_code=200,
                ok=True,
                latency_ms=latency,
                checked_at=now - timedelta(hours=i)
            )
        
        # Mock IsolationForest
        mock_clf = Mock()
        mock_clf.fit_predict.return_value = [-1 if i >= 18 else 1 for i in range(20)]
        mock_clf.score_samples.return_value = [-0.5 if i >= 18 else 0.1 for i in range(20)]
        mock_isolation_forest.return_value = mock_clf
        
        result = analyze_logs(period_hours=24)
        
        assert result['status'] == 'success'
        assert result['anomalies_found'] == 2
        assert result['services_analyzed'] == 1
        
        # Check AI digest was created
        digest = AIDigest.objects.first()
        assert digest is not None
        assert len(digest.anomalies) == 2
        assert 'Health Check Analysis Report' in digest.summary_text
    
    def test_generate_summary_rule_based(self):
        """Test rule-based summary generation."""
        service_summaries = [
            {
                'service': 'API1',
                'error_rate': 0.15,
                'avg_latency_ms': 4500,
                'total_checks': 100,
                'errors': 15
            },
            {
                'service': 'API2',
                'error_rate': 0.0,
                'avg_latency_ms': 200,
                'total_checks': 100,
                'errors': 0
            }
        ]
        
        anomalies = [
            {
                'timestamp': '2024-01-01T10:00:00Z',
                'score': -0.5,
                'latency_ms': 5000,
                'ok': False,
                'status_code': 503
            }
        ] * 15  # 15 anomalies
        
        summary = generate_summary(
            service_summaries=service_summaries,
            anomalies=anomalies,
            period_hours=24
        )
        
        # Check summary contains expected sections
        assert 'Health Check Analysis Report' in summary
        assert 'Services with Errors:' in summary
        assert 'API1: 15.0% error rate' in summary
        assert 'Services with High Latency:' in summary
        assert 'API1: 4500ms average' in summary
        assert 'Recommendations:' in summary
        assert 'Consider increasing timeout' in summary
        assert 'Implement circuit breaker' in summary
        assert 'Set up alerting' in summary
    
    @patch('openai.OpenAI')
    def test_generate_summary_with_openai(self, mock_openai_class):
        """Test summary generation with OpenAI."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="AI-generated summary"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service_summaries = [{'service': 'API1', 'error_rate': 0.1}]
        anomalies = []
        
        with patch('monitor.tasks.settings.OPENAI_API_KEY', 'test-key'):
            summary = generate_summary(
                service_summaries=service_summaries,
                anomalies=anomalies,
                period_hours=24
            )
        
        assert summary == "AI-generated summary"
        mock_client.chat.completions.create.assert_called_once()