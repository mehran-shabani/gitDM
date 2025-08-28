from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'national_id', 'dob', 'sex', 'created_at']
    list_filter = ['sex', 'created_at']
    search_fields = ['full_name', 'national_id']