from django.contrib import admin
from .models import AuditLog, Role

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    readonly_fields = ['id', 'user_id', 'path', 'method', 'status_code', 'created_at', 'meta']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role']
    list_filter = ['role']