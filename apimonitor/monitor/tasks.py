"""
Celery tasks for health monitoring and AI analysis.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, Q
import numpy as np
from sklearn.ensemble import IsolationForest

from monitor.models import Service, HealthCheckResult, AIDigest
from monitor.health import call_health

logger = logging.getLogger('monitor.tasks')


@shared_task
def run_health_checks() -> Dict[str, Any]:
    """
    Run health checks for all enabled services.
    
    Returns:
        Summary of health check results
    """
    services = Service.objects.filter(enabled=True)
    results = []
    errors = []
    
    for service in services:
        try:
            # Perform health check
            check_result = call_health(service)
            
            # Save to database
            health_result = HealthCheckResult.objects.create(
                service=service,
                status_code=check_result['status_code'],
                ok=check_result['ok'],
                latency_ms=check_result['latency_ms'],
                error_text=check_result.get('error', ''),
                meta={'attempt': check_result.get('attempt', 1)}
            )
            
            # Log to file (will be rotated automatically)
            health_logger = logging.getLogger('monitor.health')
            health_logger.info(json.dumps({
                'service': service.name,
                'status': check_result['status_code'],
                'ok': check_result['ok'],
                'latency_ms': check_result['latency_ms'],
                'error': check_result.get('error'),
                'ts': health_result.checked_at.isoformat()
            }))
            
            results.append({
                'service': service.name,
                'ok': check_result['ok'],
                'status': check_result['status_code']
            })
            
        except Exception as e:
            logger.error(f"Failed to check {service.name}: {str(e)}", exc_info=True)
            errors.append({
                'service': service.name,
                'error': str(e)
            })
    
    summary = {
        'checked': len(results),
        'successful': sum(1 for r in results if r['ok']),
        'failed': sum(1 for r in results if not r['ok']),
        'errors': len(errors),
        'timestamp': timezone.now().isoformat()
    }
    
    logger.info(f"Health check summary: {summary}")
    return summary


@shared_task
def analyze_logs(period_hours: int = 24) -> Dict[str, Any]:
    """
    Analyze health check logs using AI/ML techniques.
    
    Args:
        period_hours: Number of hours to analyze (default: 24)
        
    Returns:
        Summary of analysis results
    """
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=period_hours)
    
    # Get all health results in the period
    results = HealthCheckResult.objects.filter(
        checked_at__gte=start_time,
        checked_at__lte=end_time
    ).select_related('service').order_by('checked_at')
    
    if not results.exists():
        logger.warning(f"No health check results found for period {start_time} to {end_time}")
        return {'status': 'no_data'}
    
    # Analyze per service
    services = Service.objects.filter(enabled=True)
    all_anomalies = []
    service_summaries = []
    
    for service in services:
        service_results = results.filter(service=service)
        if not service_results.exists():
            continue
            
        # Extract features for anomaly detection
        features = []
        timestamps = []
        
        for result in service_results:
            # Features: latency_ms (normalized), error flag
            latency = result.latency_ms if result.latency_ms else 0
            error_flag = 1 if not result.ok else 0
            features.append([latency, error_flag])
            timestamps.append(result.checked_at)
        
        features = np.array(features)
        
        # Detect anomalies using Isolation Forest
        if len(features) >= 10:  # Need minimum samples
            # Normalize latency
            latencies = features[:, 0]
            if latencies.std() > 0:
                features[:, 0] = (latencies - latencies.mean()) / latencies.std()
            
            # Train Isolation Forest
            clf = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42
            )
            predictions = clf.fit_predict(features)
            anomaly_scores = clf.score_samples(features)
            
            # Collect anomalies
            service_anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:  # Anomaly
                    service_anomalies.append({
                        'timestamp': timestamps[i].isoformat(),
                        'score': float(score),
                        'latency_ms': float(service_results[i].latency_ms) if service_results[i].latency_ms else None,
                        'ok': service_results[i].ok,
                        'status_code': service_results[i].status_code
                    })
            
            if service_anomalies:
                all_anomalies.extend(service_anomalies)
        
        # Calculate service statistics
        error_count = service_results.filter(ok=False).count()
        total_count = service_results.count()
        avg_latency = service_results.filter(latency_ms__isnull=False).aggregate(
            avg=Avg('latency_ms')
        )['avg']
        
        service_summaries.append({
            'service': service.name,
            'error_rate': error_count / total_count if total_count > 0 else 0,
            'avg_latency_ms': avg_latency,
            'total_checks': total_count,
            'errors': error_count
        })
    
    # Generate summary text
    summary_text = generate_summary(
        service_summaries=service_summaries,
        anomalies=all_anomalies,
        period_hours=period_hours
    )
    
    # Save AI digest
    digest = AIDigest.objects.create(
        service=None,  # Global digest
        period_start=start_time,
        period_end=end_time,
        anomalies=all_anomalies,
        summary_text=summary_text
    )
    
    logger.info(f"Created AI digest {digest.id} for period {start_time} to {end_time}")
    
    return {
        'status': 'success',
        'digest_id': digest.id,
        'anomalies_found': len(all_anomalies),
        'services_analyzed': len(service_summaries)
    }


def generate_summary(
    service_summaries: List[Dict],
    anomalies: List[Dict],
    period_hours: int
) -> str:
    """
    Generate a summary text from analysis results.
    
    Uses OpenAI if available, otherwise falls back to rule-based summary.
    """
    # Prepare data for summary
    sorted_by_errors = sorted(
        service_summaries,
        key=lambda x: x['error_rate'],
        reverse=True
    )
    sorted_by_latency = sorted(
        [s for s in service_summaries if s['avg_latency_ms']],
        key=lambda x: x['avg_latency_ms'],
        reverse=True
    )
    
    if settings.OPENAI_API_KEY:
        # Use OpenAI for intelligent summary
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""Analyze the following API health monitoring data from the last {period_hours} hours:

Service Statistics:
{json.dumps(service_summaries, indent=2)}

Detected Anomalies ({len(anomalies)} total):
{json.dumps(anomalies[:10], indent=2)}  # First 10 anomalies

Please provide a concise summary including:
1. Services with highest error rates
2. Services with highest latency
3. Critical time periods (based on anomalies)
4. Actionable recommendations (e.g., increase timeout, add circuit breaker, set up alerts)

Keep the summary under 300 words and focus on actionable insights."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in API monitoring and reliability engineering."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            # Fall back to rule-based summary
    
    # Rule-based summary generation
    summary_parts = [
        f"## Health Check Analysis Report",
        f"Period: Last {period_hours} hours",
        f"Total anomalies detected: {len(anomalies)}",
        ""
    ]
    
    # Services with errors
    if sorted_by_errors and sorted_by_errors[0]['error_rate'] > 0:
        summary_parts.append("### Services with Errors:")
        for svc in sorted_by_errors[:3]:
            if svc['error_rate'] > 0:
                summary_parts.append(
                    f"- {svc['service']}: {svc['error_rate']:.1%} error rate "
                    f"({svc['errors']}/{svc['total_checks']} checks failed)"
                )
        summary_parts.append("")
    
    # High latency services
    if sorted_by_latency:
        summary_parts.append("### Services with High Latency:")
        for svc in sorted_by_latency[:3]:
            if svc['avg_latency_ms'] and svc['avg_latency_ms'] > 1000:
                summary_parts.append(
                    f"- {svc['service']}: {svc['avg_latency_ms']:.0f}ms average"
                )
        summary_parts.append("")
    
    # Critical periods
    if anomalies:
        # Group anomalies by hour
        from collections import defaultdict
        anomalies_by_hour = defaultdict(int)
        for anomaly in anomalies:
            hour = datetime.fromisoformat(anomaly['timestamp'].replace('Z', '+00:00')).hour
            anomalies_by_hour[hour] += 1
        
        critical_hours = sorted(anomalies_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        if critical_hours:
            summary_parts.append("### Critical Time Periods:")
            for hour, count in critical_hours:
                summary_parts.append(f"- {hour:02d}:00-{hour:02d}:59: {count} anomalies")
            summary_parts.append("")
    
    # Recommendations
    summary_parts.append("### Recommendations:")
    
    # Check for timeout recommendations
    high_latency_svcs = [s for s in sorted_by_latency if s['avg_latency_ms'] and s['avg_latency_ms'] > 3000]
    if high_latency_svcs:
        summary_parts.append(
            f"- Consider increasing timeout for: {', '.join(s['service'] for s in high_latency_svcs[:2])}"
        )
    
    # Check for retry recommendations
    high_error_svcs = [s for s in sorted_by_errors if s['error_rate'] > 0.1]
    if high_error_svcs:
        summary_parts.append(
            f"- Implement circuit breaker for: {', '.join(s['service'] for s in high_error_svcs[:2])}"
        )
    
    # Alert recommendations
    if len(anomalies) > 10:
        summary_parts.append("- Set up alerting for anomaly detection (>10 anomalies detected)")
    
    if not any([high_latency_svcs, high_error_svcs, len(anomalies) > 10]):
        summary_parts.append("- All services operating within normal parameters")
    
    return "\n".join(summary_parts)