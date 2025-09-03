"""Health checking logic with retry and backoff."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from django.conf import settings

from .models import Service

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker with retry logic and backoff."""
    
    def __init__(self, max_retries: int = 2, base_delay: float = 0.5):
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    async def call_health_async(self, service: Service) -> Dict[str, Any]:
        """Async health check with retry and backoff."""
        start_time = time.time()
        last_error = None
        
        headers = service.get_headers_dict()
        url = service.full_health_url
        
        # Add user agent
        headers.setdefault('User-Agent', 'Django-Health-Monitor/1.0')
        
        timeout = httpx.Timeout(service.timeout_s, connect=service.timeout_s)
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method=service.method,
                        url=url,
                        headers=headers,
                        follow_redirects=True
                    )
                    
                    latency_ms = int((time.time() - start_time) * 1000)
                    ok = 200 <= response.status_code < 400
                    
                    result = {
                        'status_code': response.status_code,
                        'ok': ok,
                        'latency_ms': latency_ms,
                        'error_text': '' if ok else f"HTTP {response.status_code}",
                        'meta': {
                            'attempt': attempt + 1,
                            'url': url,
                            'method': service.method,
                            'response_size': len(response.content) if hasattr(response, 'content') else 0
                        }
                    }
                    
                    if ok:
                        logger.info(f"Health check OK: {service.name} - {latency_ms}ms")
                        return result
                    else:
                        logger.warning(f"Health check failed: {service.name} - HTTP {response.status_code}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.base_delay * (2 ** attempt))
                            continue
                        return result
                        
            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(f"Health check timeout: {service.name} - attempt {attempt + 1}")
                
            except (httpx.ConnectError, httpx.NetworkError) as e:
                last_error = f"Network error: {str(e)}"
                logger.warning(f"Health check network error: {service.name} - attempt {attempt + 1}")
                
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Health check unexpected error: {service.name} - {str(e)}")
            
            # Exponential backoff for retries
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # All attempts failed
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            'status_code': None,
            'ok': False,
            'latency_ms': latency_ms,
            'error_text': last_error or "Unknown error",
            'meta': {
                'attempt': self.max_retries + 1,
                'url': url,
                'method': service.method,
                'failed_after_retries': True
            }
        }


def call_health(service: Service) -> Dict[str, Any]:
    """Synchronous wrapper for health check."""
    checker = HealthChecker()
    
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(checker.call_health_async(service))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Health check wrapper error for {service.name}: {str(e)}")
        return {
            'status_code': None,
            'ok': False,
            'latency_ms': 0,
            'error_text': f"Wrapper error: {str(e)}",
            'meta': {'wrapper_error': True}
        }


async def call_health_batch(services: list[Service]) -> Dict[str, Dict[str, Any]]:
    """Check multiple services concurrently."""
    checker = HealthChecker()
    
    tasks = []
    for service in services:
        task = asyncio.create_task(
            checker.call_health_async(service),
            name=f"health_check_{service.name}"
        )
        tasks.append((service, task))
    
    results = {}
    for service, task in tasks:
        try:
            result = await task
            results[service.name] = result
        except Exception as e:
            logger.error(f"Batch health check error for {service.name}: {str(e)}")
            results[service.name] = {
                'status_code': None,
                'ok': False,
                'latency_ms': 0,
                'error_text': f"Batch error: {str(e)}",
                'meta': {'batch_error': True}
            }
    
    return results