"""Tests for health checking functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from model_bakery import baker
import httpx

from monitor.models import Service
from monitor.health import HealthChecker, call_health, call_health_batch


@pytest.mark.django_db
class TestHealthChecker:
    """Test HealthChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = HealthChecker(max_retries=2, base_delay=0.1)
        self.service = baker.make(
            Service,
            name="TestAPI",
            base_url="https://api.test.com",
            health_path="/health",
            method="GET",
            timeout_s=5,
            headers={"X-Test": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_successful_health_check(self):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"OK"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await self.checker.call_health_async(self.service)
            
            assert result['status_code'] == 200
            assert result['ok'] is True
            assert result['latency_ms'] >= 0  # Allow 0ms for mocked calls
            assert result['error_text'] == ""
            assert result['meta']['url'] == "https://api.test.com/health"
    
    @pytest.mark.asyncio
    async def test_failed_health_check_with_status(self):
        """Test failed health check with HTTP error status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await self.checker.call_health_async(self.service)
            
            assert result['status_code'] == 500
            assert result['ok'] is False
            assert result['error_text'] == "HTTP 500"
            assert result['meta']['url'] == "https://api.test.com/health"
    
    @pytest.mark.asyncio
    async def test_timeout_with_retry(self):
        """Test timeout handling with retry logic."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            result = await self.checker.call_health_async(self.service)
            
            assert result['status_code'] is None
            assert result['ok'] is False
            assert "Timeout" in result['error_text']
            assert result['meta']['failed_after_retries'] is True
            assert result['meta']['attempt'] == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test network error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )
            
            result = await self.checker.call_health_async(self.service)
            
            assert result['ok'] is False
            assert "Network error" in result['error_text']
    
    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self):
        """Test successful check after initial failure."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.content = b"OK"
        
        with patch('httpx.AsyncClient') as mock_client:
            # First call fails, second succeeds
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("First attempt timeout"),
                    mock_response_success
                ]
            )
            
            result = await self.checker.call_health_async(self.service)
            
            assert result['ok'] is True
            assert result['status_code'] == 200
            assert result['meta']['attempt'] == 2


@pytest.mark.django_db
class TestHealthFunctions:
    """Test health check utility functions."""
    
    def test_call_health_sync_wrapper(self):
        """Test synchronous wrapper function."""
        service = baker.make(Service)
        
        with patch('monitor.health.HealthChecker.call_health_async') as mock_async:
            mock_async.return_value = {
                'status_code': 200,
                'ok': True,
                'latency_ms': 100,
                'error_text': '',
                'meta': {}
            }
            
            result = call_health(service)
            
            assert result['ok'] is True
            assert result['status_code'] == 200
            mock_async.assert_called_once()
    
    def test_call_health_sync_wrapper_exception(self):
        """Test sync wrapper handles exceptions."""
        service = baker.make(Service)
        
        with patch('monitor.health.HealthChecker.call_health_async') as mock_async:
            mock_async.side_effect = Exception("Test error")
            
            result = call_health(service)
            
            assert result['ok'] is False
            assert "Wrapper error" in result['error_text']
    
    def test_call_health_batch(self):
        """Test batch health checking."""
        services = baker.make(Service, _quantity=3)
        
        async def run_batch_test():
            with patch('monitor.health.HealthChecker.call_health_async') as mock_async:
                mock_async.return_value = {
                    'status_code': 200,
                    'ok': True,
                    'latency_ms': 100,
                    'error_text': '',
                    'meta': {}
                }
                
                results = await call_health_batch(services)
                
                assert len(results) == 3
                assert all(result['ok'] for result in results.values())
                assert mock_async.call_count == 3
        
        # Run async test in event loop
        import asyncio
        asyncio.run(run_batch_test())