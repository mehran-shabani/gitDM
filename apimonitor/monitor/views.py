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
        """Apply custom filters for service, since, and until."""
        queryset = super().get_queryset()
        
        # Filter by service
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        
        # Filter by time range
        since = self.request.query_params.get('since')
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
                queryset = queryset.filter(checked_at__gte=since_dt)
            except ValueError:
                pass
        
        until = self.request.query_params.get('until')
        if until:
            try:
                until_dt = timezone.datetime.fromisoformat(until.replace('Z', '+00:00'))
                queryset = queryset.filter(checked_at__lte=until_dt)
            except ValueError:
                pass
        
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
        """Get the latest digest, optionally filtered by service."""
        service_id = request.query_params.get('service')
        
        if service_id:
            digest = self.get_queryset().filter(service_id=service_id).first()
        else:
            digest = self.get_queryset().filter(service__isnull=True).first()
        
        if digest:
            serializer = self.get_serializer(digest)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'No digest found'},
            status=status.HTTP_404_NOT_FOUND
        )


class HealthSummaryView(viewsets.ViewSet):
    """Custom view for health summary endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        Get health summary for all services.
        
        Returns latest health check result and AI digest for each service,
        plus 24-hour statistics.
        """
        services = Service.objects.filter(enabled=True)
        summaries = []
        
        # Calculate 24 hours ago
        now = timezone.now()
        day_ago = now - timedelta(hours=24)
        
        for service in services:
            # Get latest health check
            latest_check = HealthCheckResult.objects.filter(
                service=service
            ).order_by('-checked_at').first()
            
            # Get latest AI digest (service-specific or global)
            latest_digest = AIDigest.objects.filter(
                Q(service=service) | Q(service__isnull=True)
            ).order_by('-created_at').first()
            
            # Calculate 24h statistics
            results_24h = HealthCheckResult.objects.filter(
                service=service,
                checked_at__gte=day_ago
            )
            
            stats = results_24h.aggregate(
                total=Count('id'),
                errors=Count('id', filter=Q(ok=False)),
                avg_latency=Avg('latency_ms')
            )
            
            uptime_pct = (
                ((stats['total'] - stats['errors']) / stats['total'] * 100)
                if stats['total'] > 0 else 0
            )
            
            summary_data = {
                'service_id': service.id,
                'service_name': service.name,
                'latest_check': latest_check,
                'latest_digest': latest_digest,
                'checks_24h': stats['total'],
                'errors_24h': stats['errors'],
                'avg_latency_24h': stats['avg_latency'],
                'uptime_percentage_24h': round(uptime_pct, 2)
            }
            
            summaries.append(summary_data)
        
        # Serialize the summaries
        serializer = ServiceHealthSummarySerializer(summaries, many=True)
        
        # Get global latest digest
        global_digest = AIDigest.objects.filter(
            service__isnull=True
        ).order_by('-created_at').first()
        
        response_data = {
            'services': serializer.data,
            'global_digest': AIDigestSerializer(global_digest).data if global_digest else None,
            'timestamp': now.isoformat()
        }
        
        return Response(response_data)