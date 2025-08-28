from django.contrib import admin
from .models import RecordVersion


@admin.register(RecordVersion)
class RecordVersionAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'resource_id', 'version', 'changed_at']
    list_filter = ['resource_type', 'changed_at']
    search_fields = ['resource_type', 'resource_id']