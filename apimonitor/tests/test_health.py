"""
Tests for health check functionality.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from model_bakery import baker

from monitor.models import Service
from monitor.health import call_health


@pytest.mark.django_db
class TestCallHealth:
    """Test cases for call_health function."""
    
    def test_successful_health_check(self):
        """Test successful health check with 200 status."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            timeout_s=5
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client = Mock()
            mock_client.request.return_value = mock_response
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            call_health(service)
        
        assert result['status_code'] == 200
        assert result['ok'] is True
        assert result['error'] is None
        assert 'latency_ms' in result
        assert result['latency_ms'] > 0
    
    def test_failed_health_check_with_error_status(self):
        """Test health check with error status code."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            timeout_s=5
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 503
            
            mock_client = Mock()
            mock_client.request.return_value = mock_response
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            result = call_health(service)
        
        assert result['status_code'] == 503
        assert result['ok'] is False
        assert result['error'] is None
        assert 'latency_ms' in result
    
    def test_health_check_timeout(self):
        """Test health check timeout handling."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            timeout_s=2
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.request.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            result = call_health(service)
        
        assert result['status_code'] is None
        assert result['ok'] is False
        assert 'Timeout' in result['error']
        assert result['attempt'] == 3  # All retries exhausted
    
    def test_health_check_network_error(self):
        """Test health check network error handling."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            timeout_s=5
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.request.side_effect = httpx.NetworkError("DNS failure")
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            result = call_health(service)
        
        assert result['status_code'] is None
        assert result['ok'] is False
        assert 'Network error' in result['error']
        assert 'DNS failure' in result['error']
    
    def test_health_check_retry_success(self):
        """Test health check succeeds after retry."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            timeout_s=5
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client = Mock()
            # First attempt fails, second succeeds
            mock_client.request.side_effect = [
                httpx.TimeoutException("Timeout"),
                mock_response
            ]
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = call_health(service)
        
        assert result['status_code'] == 200
        assert result['ok'] is True
        assert result['attempt'] == 2
    
    def test_health_check_with_custom_headers(self):
        """Test health check includes custom headers."""
        service = baker.make(
            Service,
            base_url='https://api.example.com',
            health_path='/health',
            method='GET',
            headers={'X-API-Key': 'test-key'},
            timeout_s=5
        )
        
        with patch('httpx.Client') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client = Mock()
            mock_client.request.return_value = mock_response
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            result = call_health(service)
            
            # Verify headers were passed
            mock_client.request.assert_called_with(
                method='GET',
                url='https://api.example.com/health',
                headers={'X-API-Key': 'test-key'},
                follow_redirects=True
            )
            # Also ensure httpx.Client was created with TLS verify enabled
            _, client_kwargs = mock_client_class.call_args
            assert client_kwargs.get('verify') is True
            assert client_kwargs.get('timeout') is not None
            assert result['ok'] is True