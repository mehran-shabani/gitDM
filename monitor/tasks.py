"""Celery tasks for health monitoring and AI analysis."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from sklearn.ensemble import IsolationForest

from .models import Service, HealthCheckResult, AIDigest
from .health import call_health, call_health_batch

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_health_checks(self) -> Dict[str, Any]:
    """Run health checks for all enabled services."""
    try:
        enabled_services = Service.objects.filter(enabled=True)
        
        if not enabled_services.exists():
            logger.info("No enabled services found for health checking")
            return {"status": "success", "checked_services": 0}
        
        results = []
        log_entries = []
        
        # Check each service
        for service in enabled_services:
            try:
                health_result = call_health(service)
                
                # Create database record
                result_obj = HealthCheckResult.objects.create(
                    service=service,
                    status_code=health_result.get('status_code'),
                    ok=health_result['ok'],
                    latency_ms=health_result['latency_ms'],
                    error_text=health_result.get('error_text', ''),
                    meta=health_result.get('meta', {})
                )
                
                results.append({
                    'service': service.name,
                    'ok': result_obj.ok,
                    'latency_ms': result_obj.latency_ms,
                    'status_code': result_obj.status_code
                })
                
                # Prepare log entry
                log_entry = {
                    'service': service.name,
                    'status': result_obj.status_code,
                    'ok': result_obj.ok,
                    'latency_ms': result_obj.latency_ms,
                    'error': result_obj.error_text,
                    'ts': result_obj.checked_at.isoformat()
                }
                log_entries.append(log_entry)
                
            except Exception as e:
                logger.error(f"Error checking service {service.name}: {str(e)}")
                # Create failed record
                result_obj = HealthCheckResult.objects.create(
                    service=service,
                    status_code=None,
                    ok=False,
                    latency_ms=0,
                    error_text=f"Task error: {str(e)}",
                    meta={'task_error': True}
                )
                
                log_entries.append({
                    'service': service.name,
                    'status': None,
                    'ok': False,
                    'latency_ms': 0,
                    'error': f"Task error: {str(e)}",
                    'ts': result_obj.checked_at.isoformat()
                })
        
        # Write to log file
        _write_health_logs(log_entries)
        
        logger.info(f"Health checks completed for {len(enabled_services)} services")
        return {
            "status": "success",
            "checked_services": len(enabled_services),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Health check task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        return {"status": "error", "error": str(e)}


def _write_health_logs(log_entries: List[Dict[str, Any]]) -> None:
    """Write health check results to JSONL log file."""
    try:
        log_dir = Path(settings.BASE_DIR) / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'health.log'
        
        with open(log_file, 'a', encoding='utf-8') as f:
            for entry in log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
    except Exception as e:
        logger.error(f"Failed to write health logs: {str(e)}")


@shared_task(bind=True, max_retries=2)
def analyze_logs(self, period_hours: int = 24) -> Dict[str, Any]:
    """Analyze health check logs using AI and anomaly detection."""
    try:
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        # Get health check data from the period
        results = HealthCheckResult.objects.filter(
            checked_at__gte=start_time,
            checked_at__lte=end_time
        ).select_related('service').order_by('checked_at')
        
        if not results.exists():
            logger.info(f"No health check data found for period {start_time} to {end_time}")
            return {"status": "no_data", "period_hours": period_hours}
        
        # Analyze by service
        services_analyzed = []
        
        for service in Service.objects.filter(enabled=True):
            service_results = results.filter(service=service)
            
            if not service_results.exists():
                continue
                
            anomalies = _detect_anomalies(service_results)
            summary = _generate_summary(service, service_results, anomalies)
            
            # Create AI digest
            digest = AIDigest.objects.create(
                service=service,
                period_start=start_time,
                period_end=end_time,
                anomalies=anomalies,
                summary_text=summary
            )
            
            services_analyzed.append(service.name)
            logger.info(f"Created AI digest for {service.name} with {len(anomalies)} anomalies")
        
        # Create global digest
        if services_analyzed:
            global_anomalies = _detect_global_anomalies(results)
            global_summary = _generate_global_summary(results, global_anomalies, services_analyzed)
            
            AIDigest.objects.create(
                service=None,  # Global digest
                period_start=start_time,
                period_end=end_time,
                anomalies=global_anomalies,
                summary_text=global_summary
            )
        
        return {
            "status": "success",
            "period_hours": period_hours,
            "services_analyzed": services_analyzed,
            "total_results": results.count()
        }
        
    except Exception as e:
        logger.error(f"Log analysis task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)  # 5 minute delay
        return {"status": "error", "error": str(e)}


def _detect_anomalies(results) -> List[Dict[str, Any]]:
    """Detect anomalies in latency and error patterns using IsolationForest."""
    if len(results) < 10:  # Need minimum data points
        return []
    
    try:
        # Prepare features: latency and error flag
        features = []
        timestamps = []
        
        for result in results:
            features.append([
                result.latency_ms,
                1 if not result.ok else 0  # Error flag
            ])
            timestamps.append(result.checked_at)
        
        features_array = np.array(features)
        
        # Detect anomalies
        isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42
        )
        anomaly_labels = isolation_forest.fit_predict(features_array)
        anomaly_scores = isolation_forest.score_samples(features_array)
        
        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:  # Anomaly detected
                anomalies.append({
                    'timestamp': timestamps[i].isoformat(),
                    'latency_ms': features[i][0],
                    'error': bool(features[i][1]),
                    'anomaly_score': float(score)
                })
        
        # Sort by anomaly score (most anomalous first)
        anomalies.sort(key=lambda x: x['anomaly_score'])
        
        return anomalies
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}")
        return []


def _detect_global_anomalies(results) -> List[Dict[str, Any]]:
    """Detect global anomalies across all services."""
    if len(results) < 20:
        return []
    
    try:
        # Group by time windows (e.g., hourly)
        time_windows = {}
        
        for result in results:
            hour_key = result.checked_at.replace(minute=0, second=0, microsecond=0)
            if hour_key not in time_windows:
                time_windows[hour_key] = {'latencies': [], 'errors': 0, 'total': 0}
            
            time_windows[hour_key]['latencies'].append(result.latency_ms)
            if not result.ok:
                time_windows[hour_key]['errors'] += 1
            time_windows[hour_key]['total'] += 1
        
        # Prepare features for global anomaly detection
        features = []
        timestamps = []
        
        for timestamp, data in time_windows.items():
            avg_latency = np.mean(data['latencies'])
            error_rate = data['errors'] / data['total'] if data['total'] > 0 else 0
            
            features.append([avg_latency, error_rate])
            timestamps.append(timestamp)
        
        if len(features) < 5:
            return []
        
        features_array = np.array(features)
        
        isolation_forest = IsolationForest(
            contamination=0.15,  # Expect 15% anomalous time windows
            random_state=42
        )
        anomaly_labels = isolation_forest.fit_predict(features_array)
        anomaly_scores = isolation_forest.score_samples(features_array)
        
        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:
                window_data = time_windows[timestamps[i]]
                anomalies.append({
                    'timestamp': timestamps[i].isoformat(),
                    'avg_latency_ms': float(features[i][0]),
                    'error_rate': float(features[i][1]),
                    'anomaly_score': float(score),
                    'total_checks': window_data['total']
                })
        
        anomalies.sort(key=lambda x: x['anomaly_score'])
        return anomalies
        
    except Exception as e:
        logger.error(f"Global anomaly detection failed: {str(e)}")
        return []


def _generate_summary(service: Service, results, anomalies: List[Dict[str, Any]]) -> str:
    """Generate summary for a specific service."""
    total_checks = len(results)
    failed_checks = sum(1 for r in results if not r.ok)
    success_rate = ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0
    
    latencies = [r.latency_ms for r in results if r.ok]
    avg_latency = np.mean(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    
    # Try OpenAI if available
    openai_summary = _generate_openai_summary(service, results, anomalies)
    if openai_summary:
        return openai_summary
    
    # Fallback to rule-based summary
    summary_parts = [
        f"Service: {service.name}",
        f"Health Check Summary ({total_checks} checks):",
        f"- Success Rate: {success_rate:.1f}%",
        f"- Average Latency: {avg_latency:.0f}ms",
        f"- Max Latency: {max_latency}ms",
        f"- Anomalies Detected: {len(anomalies)}"
    ]
    
    if failed_checks > 0:
        failure_rate = (failed_checks / total_checks * 100)
        summary_parts.append(f"- Failure Rate: {failure_rate:.1f}% ({failed_checks} failures)")
    
    if anomalies:
        summary_parts.append("\nRecommendations:")
        if any(a['latency_ms'] > 5000 for a in anomalies):
            summary_parts.append("- Consider increasing timeout or optimizing service performance")
        if len(anomalies) > total_checks * 0.2:
            summary_parts.append("- High anomaly rate detected, investigate service stability")
        if failed_checks > total_checks * 0.1:
            summary_parts.append("- Consider implementing circuit breaker pattern")
    
    return "\n".join(summary_parts)


def _generate_global_summary(results, anomalies: List[Dict[str, Any]], services: List[str]) -> str:
    """Generate global summary across all services."""
    total_checks = len(results)
    failed_checks = sum(1 for r in results if not r.ok)
    success_rate = ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0
    
    # Try OpenAI if available
    openai_summary = _generate_openai_global_summary(results, anomalies, services)
    if openai_summary:
        return openai_summary
    
    # Fallback to rule-based summary
    summary_parts = [
        "Global Health Monitoring Summary",
        f"Services Monitored: {len(services)}",
        f"Total Health Checks: {total_checks}",
        f"Overall Success Rate: {success_rate:.1f}%",
        f"Global Anomalies: {len(anomalies)}"
    ]
    
    if anomalies:
        summary_parts.append("\nCritical Time Windows:")
        for anomaly in anomalies[:3]:  # Top 3 anomalous windows
            summary_parts.append(
                f"- {anomaly['timestamp']}: {anomaly['error_rate']:.1%} error rate, "
                f"{anomaly['avg_latency_ms']:.0f}ms avg latency"
            )
    
    return "\n".join(summary_parts)


def _generate_openai_summary(service: Service, results, anomalies: List[Dict[str, Any]]) -> Optional[str]:
    """Generate AI summary using OpenAI if available."""
    if not getattr(settings, 'OPENAI_API_KEY', None):
        return None
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prepare data for AI
        total_checks = len(results)
        failed_checks = sum(1 for r in results if not r.ok)
        latencies = [r.latency_ms for r in results if r.ok]
        
        data_summary = {
            'service_name': service.name,
            'total_checks': total_checks,
            'failed_checks': failed_checks,
            'success_rate': ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0,
            'avg_latency_ms': np.mean(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'anomalies_count': len(anomalies),
            'recent_errors': [r.error_text for r in results if not r.ok and r.error_text][:5]
        }
        
        prompt = f"""Analyze this API health monitoring data and provide actionable insights:

Service: {data_summary['service_name']}
Period: Last 24 hours
Total Checks: {data_summary['total_checks']}
Success Rate: {data_summary['success_rate']:.1f}%
Average Latency: {data_summary['avg_latency_ms']:.0f}ms
Max Latency: {data_summary['max_latency_ms']:.0f}ms
Anomalies Detected: {data_summary['anomalies_count']}

Recent Errors: {data_summary['recent_errors']}

Please provide:
1. Service health assessment
2. Key issues identified
3. Specific recommendations for improvement
4. Suggested monitoring thresholds

Keep the summary concise and actionable for DevOps teams."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI summary generation failed: {str(e)}")
        return None


def _generate_openai_global_summary(results, anomalies: List[Dict[str, Any]], services: List[str]) -> Optional[str]:
    """Generate global AI summary using OpenAI if available."""
    if not getattr(settings, 'OPENAI_API_KEY', None):
        return None
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prepare global data
        total_checks = len(results)
        failed_checks = sum(1 for r in results if not r.ok)
        
        # Service-level statistics
        service_stats = {}
        for result in results:
            service_name = result.service.name
            if service_name not in service_stats:
                service_stats[service_name] = {'total': 0, 'failed': 0, 'latencies': []}
            
            service_stats[service_name]['total'] += 1
            if not result.ok:
                service_stats[service_name]['failed'] += 1
            else:
                service_stats[service_name]['latencies'].append(result.latency_ms)
        
        prompt = f"""Analyze this global API monitoring data across {len(services)} services:

Total Health Checks: {total_checks}
Overall Success Rate: {((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0:.1f}%
Global Anomalies: {len(anomalies)}

Service Performance:
{json.dumps(service_stats, indent=2)}

Critical Time Windows: {len(anomalies)}

Please provide:
1. Overall system health assessment
2. Services requiring immediate attention
3. System-wide patterns and trends
4. Infrastructure recommendations
5. Alerting strategy suggestions

Focus on actionable insights for maintaining service reliability."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI global summary generation failed: {str(e)}")
        return None