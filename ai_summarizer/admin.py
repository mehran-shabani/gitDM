from django.contrib import admin
from .models import AISummary


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    # resource_type یک property نمایشی‌ه و برای list_display اوکیه
    list_display = ('patient', 'resource_type', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('patient__full_name', 'content_type__model', 'summary')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('patient', 'content_type')

