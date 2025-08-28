from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'primary_doctor_id', 'created_at')
    search_fields = ('full_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')