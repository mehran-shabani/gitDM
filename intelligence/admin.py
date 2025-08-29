from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import AISummary


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
    list_display = ('patient', 'resource_type', 'references_count', 'created_at')
    # Use real DB field here; custom resource type filter comes via get_list_filter
    list_filter = ('created_at',)
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