"""Django admin configuration for monitoring models."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Service, HealthCheckResult, AIDigest


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""
    
    list_display = [
        'name', 'base_url', 'method', 'timeout_s', 
        'enabled_status', 'health_url_link', 'created_at'
    ]
    list_filter = ['enabled', 'method', 'created_at']
    search_fields = ['name', 'base_url']
    readonly_fields = ['created_at', 'updated_at', 'full_health_url']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'base_url', 'health_path', 'enabled')
        }),
        ('Request Configuration', {
            'fields': ('method', 'headers', 'timeout_s')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'full_health_url'),
            'classes': ('collapse',)
        })
    )
    
    def enabled_status(self, obj):
        """Display enabled status with color."""
        if obj.enabled:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Enabled</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Disabled</span>'
        )
    enabled_status.short_description = 'Status'
    
    def health_url_link(self, obj):
        """Display health URL as clickable link."""
        url = obj.full_health_url
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            url[:50] + '...' if len(url) > 50 else url
        )
    health_url_link.short_description = 'Health URL'


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    """Admin interface for HealthCheckResult model."""
    
    list_display = [
        'service', 'status_indicator', 'status_code', 'latency_ms',
        'checked_at', 'error_summary'
    ]
    list_filter = [
        'ok', 'service', 'checked_at', 'status_code'
    ]
    search_fields = ['service__name', 'error_text']
    readonly_fields = ['checked_at', 'status_display']
    date_hierarchy = 'checked_at'
    
    fieldsets = (
        ('Check Information', {
            'fields': ('service', 'checked_at', 'status_display')
        }),
        ('Results', {
            'fields': ('status_code', 'ok', 'latency_ms', 'error_text')
        }),
        ('Metadata', {
            'fields': ('meta',),
            'classes': ('collapse',)
        })
    )
    
    def status_indicator(self, obj):
        """Visual status indicator."""
        if obj.ok:
            return format_html(
                '<span style="color: green; font-size: 16px;">✓</span>'
            )
        return format_html(
            '<span style="color: red; font-size: 16px;">✗</span>'
        )
    status_indicator.short_description = '✓'
    
    def error_summary(self, obj):
        """Short error summary."""
        if not obj.error_text:
            return '-'
        return obj.error_text[:50] + '...' if len(obj.error_text) > 50 else obj.error_text
    error_summary.short_description = 'Error'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('service')


@admin.register(AIDigest)
class AIDigestAdmin(admin.ModelAdmin):
    """Admin interface for AIDigest model."""
    
    list_display = [
        'service_or_global', 'period_range', 'anomaly_count',
        'created_at', 'summary_preview'
    ]
    list_filter = ['service', 'created_at', 'period_start']
    search_fields = ['service__name', 'summary_text']
    readonly_fields = ['created_at', 'anomaly_count', 'period_duration_hours']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('service', 'period_start', 'period_end', 'created_at')
        }),
        ('Results', {
            'fields': ('anomaly_count', 'period_duration_hours', 'summary_text')
        }),
        ('Anomalies Data', {
            'fields': ('anomalies',),
            'classes': ('collapse',)
        })
    )
    
    def service_or_global(self, obj):
        """Display service name or 'Global'."""
        if obj.service:
            return obj.service.name
        return format_html(
            '<strong style="color: blue;">Global Analysis</strong>'
        )
    service_or_global.short_description = 'Service'
    
    def period_range(self, obj):
        """Display analysis period."""
        start = obj.period_start.strftime('%m/%d %H:%M')
        end = obj.period_end.strftime('%m/%d %H:%M')
        return f"{start} - {end}"
    period_range.short_description = 'Period'
    
    def summary_preview(self, obj):
        """Short summary preview."""
        if not obj.summary_text:
            return '-'
        preview = obj.summary_text[:100] + '...' if len(obj.summary_text) > 100 else obj.summary_text
        return mark_safe(preview.replace('\n', '<br>'))
    summary_preview.short_description = 'Summary'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('service')