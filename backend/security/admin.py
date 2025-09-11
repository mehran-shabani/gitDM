from django.contrib import admin
from .models import AuditLog, SecurityEvent, Role


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    search_fields = ['path']
    readonly_fields = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at', 'meta']

    fieldsets = (
        ('Request', {
            'fields': ('path', 'method', 'status_code')
        }),
        ('User/Meta', {
            'fields': ('user_id', 'meta', 'created_at')
        }),
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


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role']
    list_filter = ['role']
    search_fields = ['user__email']