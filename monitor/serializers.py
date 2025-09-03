"""DRF serializers for monitoring models."""

from rest_framework import serializers
from .models import Service, HealthCheckResult, AIDigest


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""
    
    full_health_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'base_url', 'health_path', 'method', 
            'headers', 'timeout_s', 'enabled', 'created_at', 
            'updated_at', 'full_health_url'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_headers(self, value):
        """Validate headers field."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Headers must be a valid JSON object")
        return value

    def validate_timeout_s(self, value):
        """Validate timeout."""
        if value < 1 or value > 300:
            raise serializers.ValidationError("Timeout must be between 1 and 300 seconds")
        return value


class HealthCheckResultSerializer(serializers.ModelSerializer):
    """Serializer for HealthCheckResult model."""
    
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.ReadOnlyField()
    
    class Meta:
        model = HealthCheckResult
        fields = [
            'id', 'service', 'service_name', 'status_code', 'ok', 
            'latency_ms', 'error_text', 'checked_at', 'meta', 'status_display'
        ]
        read_only_fields = ['id', 'checked_at']


class HealthCheckResultListSerializer(serializers.ModelSerializer):
    """Optimized serializer for listing health check results."""
    
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = HealthCheckResult
        fields = [
            'id', 'service', 'service_name', 'status_code', 'ok', 
            'latency_ms', 'error_text', 'checked_at'
        ]


class AIDigestSerializer(serializers.ModelSerializer):
    """Serializer for AIDigest model."""
    
    service_name = serializers.CharField(source='service.name', read_only=True)
    anomaly_count = serializers.ReadOnlyField()
    period_duration_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = AIDigest
        fields = [
            'id', 'service', 'service_name', 'period_start', 'period_end',
            'anomalies', 'summary_text', 'created_at', 'anomaly_count',
            'period_duration_hours'
        ]
        read_only_fields = ['id', 'created_at']


class HealthSummarySerializer(serializers.Serializer):
    """Serializer for health summary endpoint."""
    
    service_id = serializers.IntegerField()
    service_name = serializers.CharField()
    latest_check = HealthCheckResultListSerializer(allow_null=True)
    latest_digest = AIDigestSerializer(allow_null=True)
    
    class Meta:
        fields = ['service_id', 'service_name', 'latest_check', 'latest_digest']