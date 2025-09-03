from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MedicalTimeline, TestReminder, TimelineEventCategory,
    PatientTimelinePreference, ReminderTemplate, MedicalTimelineNote
)


@admin.register(MedicalTimeline)
class MedicalTimelineAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'patient', 'event_type', 'severity', 
        'occurred_at', 'is_visible', 'created_by'
    ]
    list_filter = [
        'event_type', 'severity', 'is_visible', 'occurred_at', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'patient__full_name', 
        'patient__user__email', 'created_by__email'
    ]
    readonly_fields = ['created_at', 'content_type', 'object_id']
    date_hierarchy = 'occurred_at'
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('patient', 'event_type', 'title', 'description')
        }),
        ('زمان‌بندی', {
            'fields': ('occurred_at', 'created_at')
        }),
        ('جزئیات', {
            'fields': ('severity', 'metadata', 'is_visible')
        }),
        ('ارتباطات', {
            'fields': ('content_type', 'object_id', 'created_by')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient', 'created_by', 'content_type'
        )


class MedicalTimelineNoteInline(admin.TabularInline):
    model = MedicalTimelineNote
    extra = 0
    readonly_fields = ['added_at']


@admin.register(TestReminder)
class TestReminderAdmin(admin.ModelAdmin):
    list_display = [
        'test_type', 'patient', 'frequency', 'next_due', 
        'priority', 'is_active', 'is_overdue_display'
    ]
    list_filter = [
        'test_type', 'frequency', 'priority', 'is_active', 
        'next_due', 'created_at'
    ]
    search_fields = [
        'patient__full_name', 'patient__user__email', 
        'notes', 'created_by__email'
    ]
    readonly_fields = ['created_at', 'updated_at', 'is_overdue_display', 'days_until_due_display']
    date_hierarchy = 'next_due'
    
    fieldsets = (
        ('اطلاعات آزمایش', {
            'fields': ('patient', 'test_type', 'priority')
        }),
        ('زمان‌بندی', {
            'fields': ('frequency', 'custom_interval_days', 'last_performed', 'next_due')
        }),
        ('تنظیمات یادآوری', {
            'fields': ('reminder_days_before', 'is_active')
        }),
        ('جزئیات', {
            'fields': ('notes', 'created_by')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at', 'is_overdue_display', 'days_until_due_display'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red;">عقب‌افتاده</span>')
        return format_html('<span style="color: green;">به‌موقع</span>')
    is_overdue_display.short_description = 'وضعیت'
    
    def days_until_due_display(self, obj):
        days = obj.days_until_due()
        if days < 0:
            return format_html(f'<span style="color: red;">{abs(days)} روز عقب‌افتاده</span>')
        elif days <= 3:
            return format_html(f'<span style="color: orange;">{days} روز باقی‌مانده</span>')
        else:
            return format_html(f'<span style="color: green;">{days} روز باقی‌مانده</span>')
    days_until_due_display.short_description = 'روزهای باقی‌مانده'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'created_by')
    
    actions = ['mark_as_completed', 'activate_reminders', 'deactivate_reminders']
    
    def mark_as_completed(self, request, queryset):
        """علامت‌گذاری یادآورها به عنوان انجام شده"""
        count = 0
        for reminder in queryset:
            reminder.mark_as_completed()
            count += 1
        
        self.message_user(request, f'{count} یادآوری به عنوان انجام شده علامت‌گذاری شد.')
    mark_as_completed.short_description = 'علامت‌گذاری به عنوان انجام شده'
    
    def activate_reminders(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} یادآوری فعال شد.')
    activate_reminders.short_description = 'فعال‌سازی یادآورها'
    
    def deactivate_reminders(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} یادآوری غیرفعال شد.')
    deactivate_reminders.short_description = 'غیرفعال‌سازی یادآورها'


@admin.register(TimelineEventCategory)
class TimelineEventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_display', 'icon']
    search_fields = ['name', 'description']
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ddd;"></div>',
            obj.color
        )
    color_display.short_description = 'رنگ'


@admin.register(PatientTimelinePreference)
class PatientTimelinePreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'show_lab_results', 'show_medications', 
        'show_encounters', 'enable_email_reminders'
    ]
    list_filter = [
        'show_lab_results', 'show_medications', 'show_encounters',
        'enable_email_reminders', 'enable_sms_reminders'
    ]
    search_fields = ['patient__full_name', 'patient__user__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient')


@admin.register(ReminderTemplate)
class ReminderTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'test_type', 'default_frequency', 'default_priority', 
        'default_reminder_days', 'is_active'
    ]
    list_filter = ['test_type', 'default_frequency', 'default_priority', 'is_active']
    search_fields = ['instructions', 'preparation_notes']
    
    fieldsets = (
        ('تنظیمات پایه', {
            'fields': ('test_type', 'default_frequency', 'default_priority', 'default_reminder_days')
        }),
        ('راهنمایی‌ها', {
            'fields': ('instructions', 'preparation_notes')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )


@admin.register(MedicalTimelineNote)
class MedicalTimelineNoteAdmin(admin.ModelAdmin):
    list_display = ['timeline_event', 'added_by', 'added_at', 'note_preview']
    list_filter = ['added_at']
    search_fields = ['note', 'timeline_event__title', 'added_by__email']
    readonly_fields = ['added_at']
    
    def note_preview(self, obj):
        return obj.note[:50] + "..." if len(obj.note) > 50 else obj.note
    note_preview.short_description = 'پیش‌نمایش یادداشت'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'timeline_event', 'added_by'
        )