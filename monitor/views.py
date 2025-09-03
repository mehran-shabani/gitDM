"""DRF views for monitoring API."""

from datetime import datetime
from typing import Dict, Any

from django.db.models import Q, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Service, HealthCheckResult, AIDigest
from .serializers import (
    ServiceSerializer, 
    HealthCheckResultSerializer,
    HealthCheckResultListSerializer,
    AIDigestSerializer,
    HealthSummarySerializer
)


class MonitoringThrottle(UserRateThrottle):
    """Custom throttle for monitoring endpoints."""
    rate = '1000/hour'


class ServiceViewSet(viewsets.ModelViewSet):
    """CRUD operations for services."""
    
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [MonitoringThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['enabled', 'method']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']


class HealthCheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to health check results with filtering."""
    
    queryset = HealthCheckResult.objects.select_related('service').all()
    permission_classes = [IsAuthenticated]
    throttle_classes = [MonitoringThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'ok']
    ordering_fields = ['checked_at', 'latency_ms']
    ordering = ['-checked_at']
    
    def get_serializer_class(self):
        """Use optimized serializer for list view."""
        if self.action == 'list':
            return HealthCheckResultListSerializer
        return HealthCheckResultSerializer
    
    def get_queryset(self):
        """Filter queryset by date range."""
        queryset = super().get_queryset()
        
        # Date filtering
        since = self.request.query_params.get('since')
        until = self.request.query_params.get('until')
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                queryset = queryset.filter(checked_at__gte=since_dt)
            except ValueError:
                pass  # Invalid date format, ignore
        
        if until:
            try:
                until_dt = datetime.fromisoformat(until.replace('Z', '+00:00'))
                queryset = queryset.filter(checked_at__lte=until_dt)
            except ValueError:
                pass  # Invalid date format, ignore
        
        return queryset


class AIDigestViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to AI digests."""
    
    queryset = AIDigest.objects.select_related('service').all()
    serializer_class = AIDigestSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [MonitoringThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service']
    ordering_fields = ['created_at', 'period_start', 'period_end']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def latest(self, request) -> Response:
        """Get the latest digest, optionally filtered by service."""
        service_id = request.query_params.get('service')
        
        queryset = self.get_queryset()
        if service_id:
            try:
                queryset = queryset.filter(service_id=int(service_id))
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid service ID"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        latest_digest = queryset.first()
        if not latest_digest:
            return Response(
                {"message": "No digest found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(latest_digest)
        return Response(serializer.data)


@action(detail=False, methods=['get'], url_path='health/summary')
def health_summary(request) -> Response:
    """Get health summary for all services with latest results and digests."""
    
    # Get all enabled services with their latest health check
    services = Service.objects.filter(enabled=True).prefetch_related(
        Prefetch(
            'health_results',
            queryset=HealthCheckResult.objects.order_by('-checked_at')[:1],
            to_attr='latest_result'
        ),
        Prefetch(
            'ai_digests',
            queryset=AIDigest.objects.order_by('-created_at')[:1],
            to_attr='latest_digest'
        )
    )
    
    summary_data = []
    
    for service in services:
        latest_check = service.latest_result[0] if service.latest_result else None
        latest_digest = service.latest_digest[0] if service.latest_digest else None
        
        service_summary = {
            'service_id': service.id,
            'service_name': service.name,
            'latest_check': HealthCheckResultListSerializer(latest_check).data if latest_check else None,
            'latest_digest': AIDigestSerializer(latest_digest).data if latest_digest else None
        }
        
        summary_data.append(service_summary)
    
    # Add global digest
    global_digest = AIDigest.objects.filter(service__isnull=True).order_by('-created_at').first()
    
    response_data = {
        'services': summary_data,
        'global_digest': AIDigestSerializer(global_digest).data if global_digest else None,
        'generated_at': timezone.now().isoformat()
    }
    
    return Response(response_data)


# Register the custom action as a standalone view
from rest_framework.decorators import api_view, permission_classes, throttle_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([MonitoringThrottle])
def health_summary_view(request):
    """Standalone view for health summary."""
    return health_summary(request)