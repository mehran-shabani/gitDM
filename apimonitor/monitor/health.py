"""
Health check implementation with retry and backoff logic.
"""
import time
import logging
from typing import Any
import httpx
from httpx import TimeoutException, NetworkError

from monitor.models import Service

logger = logging.getLogger('monitor.health')


def call_health(service: Service) -> dict[str, Any]:
    """
    Perform health check on a service with retry and backoff.

    Returns:
        {
            'status_code': int | None,
            'ok': bool,
            'latency_ms': float,
            'error': str | None,
            'attempt': int,
        }
    """
    url = service.full_url
    method = (service.method or "GET").upper()
    headers = service.headers or {}
    timeout = httpx.Timeout(timeout=service.timeout_s)

    # Retry configuration
    max_retries = 2
    backoff_delays = [0.5, 1.5]  # len == max_retries

    last_error: str | None = None
    start_time = time.perf_counter()

    # Reuse connections across retries
    with httpx.Client(timeout=timeout, verify=True, follow_redirects=True) as client:
        for attempt in range(max_retries + 1):
            try:
                req_start = time.perf_counter()
                response = client.request(method=method, url=url, headers=headers)
                latency_ms = (time.perf_counter() - req_start) * 1000.0

                status_code = response.status_code
                ok = 200 <= status_code < 400

                result = {
                    'status_code': status_code,
                    'ok': ok,
                    'latency_ms': round(latency_ms, 2),
                    'error': None,
                    'attempt': attempt + 1,
                }

                logger.info(
                    {
                        'service': service.name,
                        'url': url,
                        'status': status_code,
                        'ok': ok,
                        'latency_ms': result['latency_ms'],
                        'attempt': attempt + 1,
                        'ts': time.time(),
                    }
                )
                return result

            except TimeoutException:
                last_error = f"Timeout after {service.timeout_s}s"
                logger.warning(
                    {
                        'service': service.name,
                        'url': url,
                        'error': 'timeout',
                        'attempt': attempt + 1,
                        'ts': time.time(),
                    }
                )

            except NetworkError as e:
                last_error = f"Network error: {e!s}"
                logger.warning(
                    {
                        'service': service.name,
                        'url': url,
                        'error': 'network',
                        'details': str(e),
                        'attempt': attempt + 1,
                        'ts': time.time(),
                    }
                )

            except Exception as e:
                last_error = f"Unexpected error: {type(e).__name__}: {e!s}"
                logger.error(
                    {
                        'service': service.name,
                        'url': url,
                        'error': 'unexpected',
                        'type': type(e).__name__,
                        'details': str(e),
                        'attempt': attempt + 1,
                        'ts': time.time(),
                    },
                    exc_info=True,
                )

            # Backoff (if not last attempt)
            if attempt < max_retries:
                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                time.sleep(delay)

    # All retries failed
    total_time_ms = (time.perf_counter() - start_time) * 1000.0
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
            'total_time_ms': result['latency_ms'],
            'ts': time.time(),
        }
    )
    return result
