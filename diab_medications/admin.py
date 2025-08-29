from django.contrib import admin
from .models import MedicationOrder

@admin.register(MedicationOrder)
class MedicationOrderAdmin(admin.ModelAdmin):
    list_display = ('patient', 'name', 'dose', 'frequency', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('patient__full_name', 'name', 'atc')
    readonly_fields = ('id',)
