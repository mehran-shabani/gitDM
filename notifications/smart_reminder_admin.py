"""
Admin configuration for smart reminder models
"""
from django.contrib import admin
from .models import SmartReminder, ReminderPattern, ReminderSchedule, ReminderResponse


@admin.register(SmartReminder)
class SmartReminderAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'patient', 'reminder_type', 'frequency', 
        'status', 'priority', 'is_critical', 'created_at'
    ]
    list_filter = [
        'reminder_type', 'frequency', 'status', 'is_critical', 
        'is_adaptive', 'created_at'
    ]
    search_fields = ['title', 'description', 'patient__full_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('patient', 'reminder_type', 'title', 'description')
        }),
        ('ارتباط با منابع', {
            'fields': ('medication_id', 'lab_test_id')
        }),
        ('زمان‌بندی', {
            'fields': (
                'start_date', 'end_date', 'frequency', 
                'times_per_day', 'days_of_week', 'preferred_times'
            )
        }),
        ('تنظیمات', {
            'fields': ('status', 'is_adaptive', 'priority', 'is_critical')
        }),
        ('متادیتا', {
            'fields': ('created_by', 'created_at', 'updated_at')
        })
    )


@admin.register(ReminderPattern)
class ReminderPatternAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'reminder_type', 'compliance_rate',
        'total_reminders_sent', 'total_responses',
        'preferred_notification_channel', 'last_pattern_update'
    ]
    list_filter = [
        'reminder_type', 'preferred_notification_channel',
        'last_pattern_update'
    ]
    search_fields = ['patient__full_name']
    readonly_fields = [
        'total_reminders_sent', 'total_responses',
        'compliance_rate', 'last_pattern_update'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('patient', 'reminder_type')
        }),
        ('الگوهای زمانی', {
            'fields': ('best_response_times', 'worst_response_times')
        }),
        ('آمار پاسخ‌دهی', {
            'fields': (
                'total_reminders_sent', 'total_responses',
                'average_response_time', 'compliance_rate'
            )
        }),
        ('ترجیحات', {
            'fields': ('preferred_notification_channel',)
        }),
        ('متادیتا', {
            'fields': ('last_pattern_update',)
        })
    )


@admin.register(ReminderSchedule)
class ReminderScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'reminder', 'scheduled_time', 'is_sent', 'is_acknowledged',
        'action_taken', 'attempt_count'
    ]
    list_filter = [
        'is_sent', 'is_acknowledged', 'action_taken',
        'scheduled_time', 'created_at'
    ]
    search_fields = [
        'reminder__title', 'reminder__patient__full_name',
        'notes'
    ]
    readonly_fields = [
        'sent_at', 'acknowledged_at', 'response_time',
        'attempt_count', 'last_attempt_at', 'created_at'
    ]
    date_hierarchy = 'scheduled_time'
    
    fieldsets = (
        ('یادآوری', {
            'fields': ('reminder', 'scheduled_time')
        }),
        ('وضعیت ارسال', {
            'fields': (
                'is_sent', 'sent_at', 'attempt_count',
                'last_attempt_at', 'notification_id'
            )
        }),
        ('پاسخ بیمار', {
            'fields': (
                'is_acknowledged', 'acknowledged_at',
                'response_time', 'action_taken', 'notes'
            )
        }),
        ('متادیتا', {
            'fields': ('created_at',)
        })
    )


@admin.register(ReminderResponse)
class ReminderResponseAdmin(admin.ModelAdmin):
    list_display = [
        'schedule', 'response_type', 'action_result',
        'satisfaction_score', 'response_time'
    ]
    list_filter = [
        'response_type', 'action_result', 'satisfaction_score',
        'created_at'
    ]
    search_fields = [
        'schedule__reminder__title',
        'schedule__reminder__patient__full_name',
        'patient_feedback'
    ]
    readonly_fields = ['response_time', 'response_delay', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('برنامه یادآوری', {
            'fields': ('schedule',)
        }),
        ('نوع پاسخ', {
            'fields': ('response_type', 'response_time', 'response_delay')
        }),
        ('جزئیات پاسخ', {
            'fields': ('action_result', 'patient_feedback', 'satisfaction_score')
        }),
        ('اطلاعات دستگاه', {
            'fields': ('device_type', 'location')
        }),
        ('متادیتا', {
            'fields': ('created_at',)
        })
    )