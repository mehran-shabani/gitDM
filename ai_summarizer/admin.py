from django.contrib import admin
from .models import AISummary


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
 class AISummaryAdmin(admin.ModelAdmin):
-    list_display = ('patient', 'resource_type', 'created_at')
-    list_filter = ('resource_type', 'created_at')
    list_display = ('patient', 'resource_type', 'created_at')  # اوکی می‌مونه چون callable/prop قابل نمایشه
    list_filter = ('content_type', 'created_at')
    search_fields = ('patient__full_name', 'content_type__model', 'summary')
    readonly_fields = ('id', 'created_at')

