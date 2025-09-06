"""
Django REST Framework serializers for API monitoring.
"""
from rest_framework import serializers
from monitor.models import Service, HealthCheckResult, AIDigest


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""
    
    full_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'base_url', 'health_path', 'full_url',
            'method', 'headers', 'timeout_s', 'enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_headers(self, value):
        """Ensure headers is a dictionary."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Headers must be a dictionary.")
        return value or {}


class HealthCheckResultSerializer(serializers.ModelSerializer):
    """Serializer for HealthCheckResult model."""
    
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_url = serializers.CharField(source='service.full_url', read_only=True)
    
    class Meta:
        model = HealthCheckResult
        fields = [
            'id', 'service', 'service_name', 'service_url',
            'status_code', 'ok', 'latency_ms', 'error_text',
            'checked_at', 'meta'
        ]
        read_only_fields = ['checked_at']


class AIDigestSerializer(serializers.ModelSerializer):
    """Serializer for AIDigest model."""
    
    service_name = serializers.SerializerMethodField()
    anomaly_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AIDigest
        fields = [
            'id', 'service', 'service_name', 'period_start',
            'period_end', 'anomalies', 'anomaly_count',
            'summary_text', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_service_name(self, obj):
        """Get service name or 'All Services' for global digests."""
        return obj.service.name if obj.service else 'All Services'
    
    def get_anomaly_count(self, obj):
        """Get count of anomalies."""
        return len(obj.anomalies) if obj.anomalies else 0


class ServiceHealthSummarySerializer(serializers.Serializer):
    """Serializer for service health summary."""
    
    service_id = serializers.IntegerField()
    service_name = serializers.CharField()
    latest_check = HealthCheckResultSerializer(allow_null=True)
    latest_digest = AIDigestSerializer(allow_null=True)
    
    # Summary statistics
    checks_24h = serializers.IntegerField()
    errors_24h = serializers.IntegerField()
    avg_latency_24h = serializers.FloatField(allow_null=True)
    uptime_percentage_24h = serializers.FloatField()