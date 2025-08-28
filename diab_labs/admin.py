from django.contrib import admin
from .models import LabResult


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('patient', 'loinc', 'value', 'unit', 'created_at')
    list_filter = ('loinc', 'created_at')
    search_fields = ('patient__full_name', 'loinc')
    readonly_fields = ('id', 'created_at', 'updated_at')