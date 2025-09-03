from django.contrib import admin
from .models import Notification, ClinicalAlert


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient', 'notification_type', 'priority',
        'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'created_at'
    ]
    search_fields = ['title', 'message', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('recipient', 'title', 'message')
        }),
        ('طبقه‌بندی', {
            'fields': ('notification_type', 'priority')
        }),
        ('ارتباط با منابع', {
            'fields': ('patient_id', 'resource_type', 'resource_id')
        }),
        ('وضعیت', {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        ('کانال‌های ارسال', {
            'fields': ('sent_email', 'sent_sms')
        }),
        ('زمان‌بندی', {
            'fields': ('created_at',)
        })
    )


@admin.register(ClinicalAlert)
class ClinicalAlertAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'alert_type', 'severity', 'is_active',
        'acknowledged_by', 'created_at'
    ]
    list_filter = [
        'alert_type', 'severity', 'is_active', 'created_at'
    ]
    search_fields = ['patient__full_name', 'message']
    readonly_fields = ['created_at', 'acknowledged_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('patient', 'alert_type', 'severity', 'message')
        }),
        ('مقادیر', {
            'fields': ('trigger_value', 'threshold_value')
        }),
        ('وضعیت', {
            'fields': ('is_active', 'acknowledged_by', 'acknowledged_at')
        }),
        ('زمان‌بندی', {
            'fields': ('created_at',)
        })
    )