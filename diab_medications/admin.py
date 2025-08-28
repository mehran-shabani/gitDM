from django.contrib import admin
from .models import MedicationOrder


@admin.register(MedicationOrder)
class MedicationOrderAdmin(admin.ModelAdmin):
    list_display = ('patient', 'name', 'dose', 'frequency', 'created_at')
    list_filter = ('name', 'created_at')
    search_fields = ('patient__full_name', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')