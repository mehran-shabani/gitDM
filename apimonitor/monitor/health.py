"""
Health check implementation with retry and backoff logic.
"""
import time
import logging
from typing import Dict, Any
import httpx
from httpx import TimeoutException, NetworkError, HTTPStatusError

from monitor.models import Service

logger = logging.getLogger('monitor.health')


def call_health(service: Service) -> Dict[str, Any]:
    """
    Perform health check on a service with retry and backoff.
    
    Args:
        service: Service instance to check
        
    Returns:
        Dictionary containing:
        - status_code: HTTP status code (None if error)
        - ok: Boolean indicating success (200-399)
        - latency_ms: Response time in milliseconds
        - error: Error message if any
    """
    url = service.full_url
    method = service.method.upper()
    headers = service.headers or {}
    timeout = httpx.Timeout(timeout=service.timeout_s)
    
    # Retry configuration
    max_retries = 2
    backoff_delays = [0.5, 1.5]  # Exponential backoff
    
    last_error = None
    start_time = time.time()
    
    # Open a single client to reuse connections across retries
    with httpx.Client(timeout=timeout, verify=True) as client:
        for attempt in range(max_retries + 1):
            try:
                # Use a monotonic timer for accurate measurements
                request_start = time.perf_counter()
                
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    follow_redirects=True
                )
                latency_ms = (time.time() - request_start) * 1000
                status_code = response.status_code
                ok = 200 <= status_code < 400
                
                result = {
                    'status_code': status_code,
                    'ok': ok,
                    'latency_ms': round(latency_ms, 2),
                    'error': None,
                    'attempt': attempt + 1,
                }
                
                # Log successful check
                logger.info(
                    {
                        'service': service.name,
                        'url': url,
                        'status': status_code,
                        'ok': ok,
                        'latency_ms': latency_ms,
                        'attempt': attempt + 1,
                        'ts': time.time()
                    }
                )
                
                return result
                
        except TimeoutException as e:
            last_error = f"Timeout after {service.timeout_s}s"
            logger.warning(
                {
                    'service': service.name,
                    'url': url,
                    'error': 'timeout',
                    'attempt': attempt + 1,
                    'ts': time.time()
                }
            )
            
        except NetworkError as e:
            last_error = f"Network error: {str(e)}"
            logger.warning(
                {
                    'service': service.name,
                    'url': url,
                    'error': 'network',
                    'details': str(e),
                    'attempt': attempt + 1,
                    'ts': time.time()
                }
            )
            
        except HTTPStatusError as e:
            # This shouldn't happen since we handle all status codes
            last_error = f"HTTP error: {str(e)}"
            logger.warning(
                {
                    'service': service.name,
                    'url': url,
                    'error': 'http',
                    'details': str(e),
                    'attempt': attempt + 1,
                    'ts': time.time()
                }
            )
            
        except Exception as e:
            last_error = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.error(
                {
                    'service': service.name,
                    'url': url,
                    'error': 'unexpected',
                    'type': type(e).__name__,
                    'details': str(e),
                    'attempt': attempt + 1,
                    'ts': time.time()
                },
                exc_info=True
            )
        
        # Apply backoff delay if not last attempt
        if attempt < max_retries:
            delay = backoff_delays[attempt]
            time.sleep(delay)
    
    # All retries failed
    total_time_ms = (time.time() - start_time) * 1000
    
    result = {
        'status_code': None,
        'ok': False,
        'latency_ms': round(total_time_ms, 2),
        'error': last_error,
        'attempt': max_retries + 1,
    }
    
    logger.error(
        {
            'service': service.name,
            'url': url,
            'error': 'all_retries_failed',
            'last_error': last_error,
            'total_attempts': max_retries + 1,
            'total_time_ms': total_time_ms,
            'ts': time.time()
        }
    )
    
    return result