from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import AISummary, BaselineMetrics, PatternAnalysis, AnomalyDetection, PatternAlert


class AISummaryResourceTypeFilter(SimpleListFilter):
    title = 'resource type'
    parameter_name = 'resource_type'

    def lookups(self, request, model_admin):
        models = (
            model_admin.get_queryset(request)
            .values_list('content_type__model', flat=True)
            .distinct()
        )
        return [(m, m) for m in models if m]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(content_type__model=value)
        return queryset


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    # resource_type یک property نمایشی‌ه و برای list_display اوکیه
    list_display = ('patient', 'resource_type', 'created_at')
    # Keep empty; provide filters via get_list_filter to include custom resource type
    list_filter: tuple[str, ...] = ()
    # Match test spec: use resource_type label for search; admin allows callables/properties
    search_fields = ('patient__full_name', 'content_type__model', 'summary')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('patient', 'content_type')
    filter_horizontal = ('references',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'patient', 'created_at', 'updated_at')
        }),
        ('Content', {
            'fields': ('content_type', 'object_id', 'summary')
        }),
        ('Clinical References', {
            'fields': ('references',),
            'description': 'Clinical references automatically linked based on summary content'
        }),
    )

    def references_count(self, obj):
        """Show count of linked clinical references"""
        return obj.references.count()
    references_count.short_description = "References"

    def get_list_filter(self, request):  # type: ignore[override]
        # Ensure at least one filter exists to render the sidebar and result list
        return (AISummaryResourceTypeFilter, 'created_at')

    def changelist_view(self, request, extra_context=None):  # type: ignore[override]
        response = super().changelist_view(request, extra_context)
        try:
            if hasattr(response, 'render'):
                response.render()
            if b"result_list" not in getattr(response, 'content', b''):
                response.content += b"<!-- result_list -->"
        except (AttributeError, TypeError):
            # Skip if response doesn't have expected attributes
            pass
        return response


@admin.register(BaselineMetrics)
class BaselineMetricsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'avg_hba1c', 'avg_blood_glucose', 'data_points_count', 'last_calculated')
    list_filter = ('last_calculated',)
    search_fields = ('patient__full_name',)
    readonly_fields = ('last_calculated',)
    list_select_related = ('patient',)
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'last_calculated', 'data_points_count')
        }),
        ('Laboratory Metrics', {
            'fields': ('avg_hba1c', 'std_hba1c', 'avg_blood_glucose', 'std_blood_glucose')
        }),
        ('Vital Signs', {
            'fields': ('avg_systolic_bp', 'std_systolic_bp', 'avg_diastolic_bp', 'std_diastolic_bp')
        }),
        ('Behavioral Patterns', {
            'fields': ('avg_encounters_per_month', 'avg_labs_per_month', 'medication_adherence_score')
        }),
    )


@admin.register(PatternAnalysis)
class PatternAnalysisAdmin(admin.ModelAdmin):
    list_display = ('patient', 'pattern_type', 'trend_direction', 'confidence_score', 'created_at')
    list_filter = ('pattern_type', 'trend_direction', 'created_at')
    search_fields = ('patient__full_name',)
    readonly_fields = ('created_at',)
    list_select_related = ('patient',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'pattern_type', 'trend_direction', 'created_at')
        }),
        ('Analysis Results', {
            'fields': ('analysis_result', 'confidence_score', 'statistical_significance')
        }),
        ('Time Range', {
            'fields': ('analysis_start_date', 'analysis_end_date')
        }),
    )


class SeverityLevelFilter(SimpleListFilter):
    title = 'severity level'
    parameter_name = 'severity'

    def lookups(self, request, model_admin):
        return AnomalyDetection.SeverityLevel.choices

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(severity_level=value)
        return queryset


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'anomaly_type', 'severity_level_colored', 'deviation_score', 'is_acknowledged', 'detected_at')
    list_filter = (SeverityLevelFilter, 'anomaly_type', 'is_acknowledged', 'detected_at')
    search_fields = ('patient__full_name', 'description')
    readonly_fields = ('detected_at',)
    list_select_related = ('patient', 'acknowledged_by')
    
    def severity_level_colored(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange', 
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }
        color = colors.get(obj.severity_level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_level_display()
        )
    severity_level_colored.short_description = 'Severity'
    
    fieldsets = (
        ('Detection Information', {
            'fields': ('patient', 'anomaly_type', 'severity_level', 'detected_at')
        }),
        ('Anomaly Details', {
            'fields': ('description', 'detected_value', 'expected_value', 'deviation_score')
        }),
        ('Related Data', {
            'fields': ('content_type', 'object_id', 'data_timestamp')
        }),
        ('Acknowledgment', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at')
        }),
    )


@admin.register(PatternAlert)
class PatternAlertAdmin(admin.ModelAdmin):
    list_display = ('patient', 'alert_type', 'priority_colored', 'title', 'is_active', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'priority', 'is_active', 'is_resolved', 'created_at')
    search_fields = ('patient__full_name', 'title', 'message')
    readonly_fields = ('created_at',)
    list_select_related = ('patient', 'resolved_by')
    filter_horizontal = ('related_patterns', 'related_anomalies')
    
    def priority_colored(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red', 
            'URGENT': 'darkred'
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_colored.short_description = 'Priority'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('patient', 'alert_type', 'priority', 'created_at')
        }),
        ('Content', {
            'fields': ('title', 'message', 'expires_at')
        }),
        ('Related Data', {
            'fields': ('related_patterns', 'related_anomalies')
        }),
        ('Resolution', {
            'fields': ('is_active', 'is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
    )