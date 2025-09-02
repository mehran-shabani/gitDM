from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'priority', 'title', 
        'is_read', 'is_sent', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_sent', 'created_at'
    ]
    search_fields = ['user__email', 'user__full_name', 'title', 'message']
    readonly_fields = ['created_at', 'read_at', 'sent_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'created_at', 'read_at', 'sent_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_enabled', 'sms_enabled', 'push_enabled',
        'critical_lab_alerts', 'blood_sugar_alerts'
    ]
    list_filter = [
        'email_enabled', 'sms_enabled', 'push_enabled',
        'critical_lab_alerts', 'blood_sugar_alerts'
    ]
    search_fields = ['user__email', 'user__full_name']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Channels', {
            'fields': ('email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Alert Types', {
            'fields': (
                'critical_lab_alerts', 'blood_sugar_alerts',
                'medication_reminders', 'appointment_reminders'
            )
        }),
        ('Thresholds', {
            'fields': (
                'high_blood_sugar_threshold', 'low_blood_sugar_threshold'
            )
        }),
    )