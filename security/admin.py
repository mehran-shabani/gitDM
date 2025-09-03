from django.contrib import admin
from .models import AuditLog, SecurityEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'resource_type', 'patient_id', 'timestamp'
    ]
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['user__email', 'patient_id', 'notes']
    readonly_fields = [
        'user', 'action', 'resource_type', 'resource_id', 'patient_id',
        'old_values', 'new_values', 'ip_address', 'user_agent', 'timestamp'
    ]
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('اطلاعات عملیات', {
            'fields': ('action', 'resource_type', 'resource_id', 'patient_id')
        }),
        ('جزئیات تغییرات', {
            'fields': ('old_values', 'new_values', 'notes')
        }),
        ('زمان‌بندی', {
            'fields': ('timestamp',)
        })
    )


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_type', 'user', 'severity', 'resolved', 'timestamp'
    ]
    list_filter = ['event_type', 'severity', 'resolved', 'timestamp']
    search_fields = ['user__email', 'details']
    readonly_fields = [
        'event_type', 'user', 'ip_address', 'user_agent', 'details', 'timestamp'
    ]
    
    fieldsets = (
        ('اطلاعات رویداد', {
            'fields': ('event_type', 'severity', 'resolved')
        }),
        ('اطلاعات کاربر', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('جزئیات', {
            'fields': ('details',)
        }),
        ('زمان‌بندی', {
            'fields': ('timestamp',)
        })
    )