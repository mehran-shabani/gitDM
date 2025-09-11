from django.contrib import admin
from .models import LabResult

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('patient', 'loinc', 'value', 'unit', 'taken_at')
    list_filter = ('loinc', 'taken_at')
    search_fields = ('patient__full_name', 'loinc')
    readonly_fields = ('id',)