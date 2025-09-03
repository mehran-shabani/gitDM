"""
Django admin configuration for monitor app.
"""
from django.contrib import admin
from monitor.models import Service, HealthCheckResult, AIDigest


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""
    
    list_display = [
        'name', 'base_url', 'health_path', 'method',
        'timeout_s', 'enabled', 'created_at'
    ]
    list_filter = ['enabled', 'method', 'created_at']
    search_fields = ['name', 'base_url']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'base_url', 'health_path')
        }),
        ('Request Configuration', {
            'fields': ('method', 'headers', 'timeout_s')
        }),
        ('Status', {
            'fields': ('enabled',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    """Admin interface for HealthCheckResult model."""
    
    list_display = [
        'service', 'status_code', 'ok', 'latency_ms',
        'checked_at', 'has_error'
    ]
    list_filter = ['ok', 'service', 'checked_at']
    search_fields = ['service__name', 'error_text']
    ordering = ['-checked_at']
    date_hierarchy = 'checked_at'
    
    def has_error(self, obj):
        """Check if result has an error."""
        return bool(obj.error_text)
    has_error.boolean = True
    has_error.short_description = 'Has Error'
    
    fieldsets = (
        ('Service', {
            'fields': ('service',)
        }),
        ('Result', {
            'fields': ('status_code', 'ok', 'latency_ms', 'error_text')
        }),
        ('Metadata', {
            'fields': ('meta', 'checked_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['checked_at']
    
    def has_add_permission(self, request):
        """Disable manual addition of health check results."""
        return False


@admin.register(AIDigest)
class AIDigestAdmin(admin.ModelAdmin):
    """Admin interface for AIDigest model."""
    
    list_display = [
        'get_service_name', 'period_start', 'period_end',
        'anomaly_count', 'created_at'
    ]
    list_filter = ['service', 'created_at']
    search_fields = ['service__name', 'summary_text']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def get_service_name(self, obj):
        """Get service name or 'All Services'."""
        return obj.service.name if obj.service else 'All Services'
    get_service_name.short_description = 'Service'
    get_service_name.admin_order_field = 'service__name'
    
    def anomaly_count(self, obj):
        """Get count of anomalies."""
        return len(obj.anomalies) if obj.anomalies else 0
    anomaly_count.short_description = 'Anomalies'
    
    fieldsets = (
        ('Service', {
            'fields': ('service',)
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Analysis', {
            'fields': ('summary_text', 'anomalies')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        """Disable manual addition of AI digests."""
        return False