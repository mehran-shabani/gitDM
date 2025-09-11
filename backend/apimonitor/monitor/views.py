"""
Django REST Framework views for API monitoring.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from monitor.models import Service, HealthCheckResult, AIDigest
from monitor.serializers import (
    ServiceSerializer,
    HealthCheckResultSerializer,
    AIDigestSerializer,
    ServiceHealthSummarySerializer
)


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Service CRUD operations."""
    
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['enabled']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class HealthCheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing health check results."""
    
    queryset = HealthCheckResult.objects.select_related('service').all()
    serializer_class = HealthCheckResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['checked_at']
    ordering = ['-checked_at']
    
    def get_queryset(self):
        """
        Apply custom filters for:
        - service: service id
        - since / until: ISO-8601 datetime (e.g. 2025-09-06T12:00:00Z)
        """
        queryset = super().get_queryset()

        # Filter by service
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        # Helper to parse and normalize datetimes
        def _parse_iso_dt(param_name: str):
            val = self.request.query_params.get(param_name)
            if not val:
                return None
            # Normalize trailing 'Z' to '+00:00'
            if val.endswith('Z'):
                val = val.replace('Z', '+00:00')
            dt = parse_datetime(val)
            if dt is None:
                # Invalid format -> 400 Bad Request
                raise ValueError(
                    f"Invalid '{param_name}' datetime. "
                    "Use ISO-8601, e.g. 2025-09-06T12:00:00Z or with timezone offset."
                )
            if is_naive(dt):
                # Assume UTC if naive (explicit behavior)
                dt = make_aware(dt, timezone=utc)
            return dt

        # since / until filters
        try:
            since_dt = _parse_iso_dt('since')
            until_dt = _parse_iso_dt('until')
        except ValueError as e:
            # Return a clear 400 instead of silently ignoring
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': str(e)})

        if since_dt:
            queryset = queryset.filter(checked_at__gte=since_dt)
        if until_dt:
            queryset = queryset.filter(checked_at__lte=until_dt)

        return queryset


class AIDigestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing AI analysis digests."""
    
    queryset = AIDigest.objects.select_related('service').all()
    serializer_class = AIDigestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Return the latest digest.
        If 'service' is provided -> latest for that service.
        Else -> latest global (service is NULL).
        """
        service_id = request.query_params.get('service')

        qs = self.get_queryset()
        if service_id:
            digest = qs.filter(service_id=service_id).order_by('-created_at').first()
        else:
            digest = qs.filter(service__isnull=True).order_by('-created_at').first()

        if not digest:
            return Response({'detail': 'No digest found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(digest).data)


class HealthSummaryView(viewsets.ViewSet):
    """
    Custom view for health summary endpoint.

    - Considers only enabled services.
    - 24-hour window computed from 'now' (timezone-aware).
    - Returns latest health check and latest digest (service-specific or global).
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        now = timezone.now()
        day_ago = now - timedelta(hours=24)

        services = Service.objects.filter(enabled=True)

        summaries = []
        # Prefetch only needed relations on the fly
        for service in services:
            latest_check = (
                HealthCheckResult.objects
                .select_related('service')
                .filter(service=service)
                .order_by('-checked_at')
                .first()
            )

            latest_digest = (
                AIDigest.objects
                .select_related('service')
                .filter(Q(service=service) | Q(service__isnull=True))
                .order_by('-created_at')
                .first()
            )

            results_24h = HealthCheckResult.objects.filter(
                service=service,
                checked_at__gte=day_ago
            )
            stats = results_24h.aggregate(
                total=Count('id'),
                errors=Count('id', filter=Q(ok=False)),
                avg_latency=Avg('latency_ms'),
            )

            total = stats['total'] or 0
            errors = stats['errors'] or 0
            avg_latency = stats['avg_latency']  # may be None
            uptime_pct = ( ((total - errors) / total) * 100 ) if total else 0.0

            summary_data = {
                'service_id': service.id,
                'service_name': service.name,
                'latest_check': latest_check,
                'latest_digest': latest_digest,
                'checks_24h': total,
                'errors_24h': errors,
                'avg_latency_24h': avg_latency,
                'uptime_percentage_24h': round(uptime_pct, 2),
            }
            summaries.append(summary_data)

        serializer = ServiceHealthSummarySerializer(summaries, many=True)

        global_digest = (
            AIDigest.objects
            .filter(service__isnull=True)
            .order_by('-created_at')
            .first()
        )

        response_data = {
            'services': serializer.data,
            'global_digest': AIDigestSerializer(global_digest).data if global_digest else None,
            'timestamp': now.isoformat(),
        }
        return Response(response_data)

        
        return Response(response_data)
