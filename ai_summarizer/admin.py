from django.contrib import admin
from .models import AISummary


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'resource_type', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['patient__full_name', 'resource_type']