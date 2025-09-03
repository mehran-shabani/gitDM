from django.contrib import admin
from .models import PatientAnalytics, DoctorAnalytics, SystemAnalytics


@admin.register(PatientAnalytics)
class PatientAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'date', 'avg_glucose', 'avg_hba1c', 'glucose_trend']
    list_filter = ['date', 'glucose_trend', 'hba1c_trend']
    search_fields = ['patient__first_name', 'patient__last_name']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(DoctorAnalytics)
class DoctorAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'total_patients', 'active_patients', 'avg_patient_hba1c']
    list_filter = ['date']
    search_fields = ['doctor__user__first_name', 'doctor__user__last_name']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(SystemAnalytics)
class SystemAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'total_encounters', 'avg_system_hba1c']
    list_filter = ['date']
    date_hierarchy = 'date'
    ordering = ['-date']