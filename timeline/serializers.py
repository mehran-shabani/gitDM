from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import MedicalTimeline, TestReminder, TimelineEventCategory, PatientTimelinePreference, ReminderTemplate


class MedicalTimelineSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش رویدادهای تایم‌لاین پزشکی
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    # اطلاعات مرتبط با محتوا
    content_type_name = serializers.SerializerMethodField()
    content_object_data = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalTimeline
        fields = [
            'id', 'patient', 'patient_name', 'event_type', 'event_type_display',
            'title', 'description', 'occurred_at', 'metadata', 'severity',
            'severity_display', 'created_by', 'created_by_name', 'created_at',
            'is_visible', 'content_type_name', 'content_object_data'
        ]
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def get_content_type_name(self, obj):
        """نام نوع محتوا"""
        return obj.content_type.model if obj.content_type else None
    
    def get_content_object_data(self, obj):
        """داده‌های خلاصه از آبجکت مرتبط"""
        if not obj.content_object:
            return None
        
        if obj.event_type == MedicalTimeline.EventType.LAB_RESULT:
            return {
                'loinc': getattr(obj.content_object, 'loinc', ''),
                'value': str(getattr(obj.content_object, 'value', '')),
                'unit': getattr(obj.content_object, 'unit', ''),
            }
        elif obj.event_type == MedicalTimeline.EventType.ENCOUNTER:
            return {
                'subjective': getattr(obj.content_object, 'subjective', '')[:100],
                'assessment': getattr(obj.content_object, 'assessment', {}),
            }
        
        return {'title': str(obj.content_object)}


class TestReminderSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای یادآورهای آزمایشات
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    # فیلدهای محاسبه شده
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    should_send_reminder = serializers.SerializerMethodField()
    
    class Meta:
        model = TestReminder
        fields = [
            'id', 'patient', 'patient_name', 'test_type', 'test_type_display',
            'frequency', 'frequency_display', 'priority', 'priority_display',
            'last_performed', 'next_due', 'reminder_days_before', 'is_active',
            'notes', 'custom_interval_days', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_overdue', 'days_until_due',
            'should_send_reminder'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_days_until_due(self, obj):
        return obj.days_until_due()
    
    def get_should_send_reminder(self, obj):
        return obj.should_send_reminder()


class TimelineEventCategorySerializer(serializers.ModelSerializer):
    """
    سریالایزر برای دسته‌بندی رویدادهای تایم‌لاین
    """
    class Meta:
        model = TimelineEventCategory
        fields = ['id', 'name', 'description', 'color', 'icon']


class PatientTimelinePreferenceSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای تنظیمات تایم‌لاین بیمار
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    
    class Meta:
        model = PatientTimelinePreference
        fields = [
            'patient', 'patient_name', 'show_lab_results', 'show_medications',
            'show_encounters', 'show_alerts', 'show_reminders',
            'enable_email_reminders', 'enable_sms_reminders',
            'default_timeline_range_days'
        ]


class ReminderTemplateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای قالب‌های یادآوری
    """
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    default_frequency_display = serializers.CharField(source='get_default_frequency_display', read_only=True)
    default_priority_display = serializers.CharField(source='get_default_priority_display', read_only=True)
    
    class Meta:
        model = ReminderTemplate
        fields = [
            'id', 'test_type', 'test_type_display', 'default_frequency',
            'default_frequency_display', 'default_priority', 'default_priority_display',
            'default_reminder_days', 'instructions', 'preparation_notes', 'is_active'
        ]


class CreateReminderFromTemplateSerializer(serializers.Serializer):
    """
    سریالایزر برای ایجاد یادآوری از قالب
    """
    patient = serializers.CharField()
    template_id = serializers.IntegerField()
    next_due = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_template_id(self, value):
        try:
            template = ReminderTemplate.objects.get(id=value, is_active=True)
            return value
        except ReminderTemplate.DoesNotExist:
            raise serializers.ValidationError("قالب یادآوری یافت نشد یا غیرفعال است.")


class TimelineFilterSerializer(serializers.Serializer):
    """
    سریالایزر برای فیلتر کردن تایم‌لاین
    """
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    event_types = serializers.MultipleChoiceField(
        choices=MedicalTimeline.EventType.choices,
        required=False
    )
    severity = serializers.MultipleChoiceField(
        choices=MedicalTimeline.Severity.choices,
        required=False
    )
    limit = serializers.IntegerField(default=100, min_value=1, max_value=1000)