from django.contrib import admin
from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'reminder_type', 'title', 'due_at', 'status', 'priority')
    list_filter = ('reminder_type', 'status', 'priority')
    search_fields = ('title', 'description', 'patient__full_name')
    readonly_fields = ('created_at', 'completed_at')

