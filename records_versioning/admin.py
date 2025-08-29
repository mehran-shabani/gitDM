from django.contrib import admin
from .models import RecordVersion


@admin.register(RecordVersion)
class RecordVersionAdmin(admin.ModelAdmin):
    list_display = (
        'resource_type',
        'resource_id',
        'version',
        'changed_by',
        'changed_at',
    )
    list_filter = ('resource_type', 'changed_at')
    search_fields = ('resource_type', 'resource_id', 'changed_by__username')
    readonly_fields = (
        'id',
        'resource_type',
        'resource_id',
        'version',
        'prev_version',
        'snapshot',
        'diff',
        'meta',
        'changed_by',
        'changed_at',
    )
    ordering = ('-changed_at',)
    list_select_related = ('changed_by',)
    date_hierarchy = 'changed_at'

