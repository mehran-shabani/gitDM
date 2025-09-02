from django.contrib import admin
from .models import MedicalFile, FileAccessLog


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'patient', 'file_type', 'file_size_display',
        'uploaded_by', 'uploaded_at', 'is_sensitive'
    ]
    list_filter = ['file_type', 'is_sensitive', 'uploaded_at']
    search_fields = [
        'title', 'description', 'patient__full_name',
        'uploaded_by__email', 'uploaded_by__full_name'
    ]
    readonly_fields = [
        'file_size', 'file_size_display', 'mime_type',
        'uploaded_at', 'updated_at'
    ]
    autocomplete_fields = ['patient', 'encounter']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'title', 'description', 'file_type')
        }),
        ('File Details', {
            'fields': (
                'file', 'file_size_display', 'mime_type',
                'is_sensitive'
            )
        }),
        ('Relations', {
            'fields': ('encounter', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set uploaded_by if creating new file."""
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FileAccessLog)
class FileAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'medical_file', 'accessed_by', 'access_type',
        'accessed_at', 'ip_address'
    ]
    list_filter = ['access_type', 'accessed_at']
    search_fields = [
        'medical_file__title', 'accessed_by__email',
        'accessed_by__full_name', 'ip_address'
    ]
    readonly_fields = [
        'medical_file', 'accessed_by', 'access_type',
        'accessed_at', 'ip_address', 'user_agent'
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation of access logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of access logs."""
        return False