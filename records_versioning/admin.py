from django.contrib import admin
from .models import RecordVersion

@admin.register(RecordVersion)
class RecordVersionAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'object_id', 'version', 'changed_at')
    list_filter = ('content_type', 'changed_at')
    search_fields = ('content_type__app_label', 'content_type__model', 'object_id')
    readonly_fields = ('id', 'changed_at')