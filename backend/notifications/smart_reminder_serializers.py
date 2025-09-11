"""
Serializers برای سیستم یادآوری هوشمند
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from .models import (
    SmartReminder, ReminderPattern, ReminderSchedule, ReminderResponse
)


class SmartReminderSerializer(serializers.ModelSerializer):
    """
    Serializer برای یادآوری هوشمند
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    active_schedules_count = serializers.SerializerMethodField()
    next_schedule = serializers.SerializerMethodField()
    compliance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = SmartReminder
        fields = [
            'id', 'patient', 'patient_name', 'reminder_type', 'title',
            'description', 'medication_id', 'lab_test_id', 'start_date',
            'end_date', 'frequency', 'times_per_day', 'days_of_week',
            'preferred_times', 'status', 'is_adaptive', 'priority',
            'is_critical', 'created_by', 'created_by_name', 'created_at',
            'updated_at', 'active_schedules_count', 'next_schedule',
            'compliance_rate'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_active_schedules_count(self, obj):
        """
        تعداد برنامه‌های فعال
        """
        return obj.schedules.filter(
            is_sent=False,
            scheduled_time__gte=timezone.now()
        ).count()
    
    def get_next_schedule(self, obj):
        """
        زمان یادآوری بعدی
        """
        next_schedule = obj.schedules.filter(
            is_sent=False,
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time').first()
        
        if next_schedule:
            return {
                'id': next_schedule.id,
                'scheduled_time': next_schedule.scheduled_time,
                'time_remaining': str(next_schedule.scheduled_time - timezone.now())
            }
        return None
    
    def get_compliance_rate(self, obj):
        """
        نرخ تبعیت از یادآوری
        """
        pattern = ReminderPattern.objects.filter(
            patient=obj.patient,
            reminder_type=obj.reminder_type
        ).first()
        
        if pattern:
            return float(pattern.compliance_rate)
        return None
    
    def validate_preferred_times(self, value):
        """
        اعتبارسنجی زمان‌های ترجیحی
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("preferred_times باید لیست باشد")
        
        for time_str in value:
            try:
                hour, minute = time_str.split(':')
                hour = int(hour)
                minute = int(minute)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                raise serializers.ValidationError(
                    f"فرمت زمان نامعتبر: {time_str}. فرمت صحیح: HH:MM"
                )
        
        return value
    
    def validate_days_of_week(self, value):
        """
        اعتبارسنجی روزهای هفته
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("days_of_week باید لیست باشد")
        
        for day in value:
            if not isinstance(day, int) or not (0 <= day <= 6):
                raise serializers.ValidationError(
                    "روزهای هفته باید اعداد 0 تا 6 باشند (0=یکشنبه، 6=شنبه)"
                )
        
        return value
    
    def validate(self, data):
        """
        اعتبارسنجی کلی
        """
        # بررسی تاریخ پایان
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد"
                )
        
        # بررسی تعداد دفعات در روز با زمان‌های ترجیحی
        if data.get('times_per_day') and data.get('preferred_times'):
            if len(data['preferred_times']) != data['times_per_day']:
                raise serializers.ValidationError(
                    f"تعداد زمان‌های ترجیحی ({len(data['preferred_times'])}) "
                    f"باید برابر با times_per_day ({data['times_per_day']}) باشد"
                )
        
        # بررسی روزهای هفته برای فرکانس هفتگی
        if data.get('frequency') == 'WEEKLY' and not data.get('days_of_week'):
            raise serializers.ValidationError(
                "برای یادآوری هفتگی، روزهای هفته باید مشخص شود"
            )
        
        return data


class ReminderPatternSerializer(serializers.ModelSerializer):
    """
    Serializer برای الگوی رفتاری
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    reminder_type_display = serializers.CharField(
        source='get_reminder_type_display', 
        read_only=True
    )
    
    class Meta:
        model = ReminderPattern
        fields = [
            'id', 'patient', 'patient_name', 'reminder_type',
            'reminder_type_display', 'best_response_times',
            'worst_response_times', 'total_reminders_sent',
            'total_responses', 'average_response_time',
            'preferred_notification_channel', 'compliance_rate',
            'last_pattern_update'
        ]
        read_only_fields = [
            'total_reminders_sent', 'total_responses',
            'average_response_time', 'compliance_rate',
            'last_pattern_update'
        ]
    
    def to_representation(self, instance):
        """
        نمایش سفارشی داده‌ها
        """
        data = super().to_representation(instance)
        
        # تبدیل average_response_time به فرمت خوانا
        if instance.average_response_time:
            total_seconds = instance.average_response_time.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            data['average_response_time_display'] = f"{hours}h {minutes}m"
        
        # اضافه کردن تحلیل ساعات
        data['best_response_hours'] = [
            f"{hour:02d}:00" for hour in instance.best_response_times
        ]
        data['worst_response_hours'] = [
            f"{hour:02d}:00" for hour in instance.worst_response_times
        ]
        
        return data


class ReminderScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer برای برنامه زمان‌بندی
    """
    reminder_title = serializers.CharField(source='reminder.title', read_only=True)
    reminder_type = serializers.CharField(source='reminder.reminder_type', read_only=True)
    patient_name = serializers.CharField(
        source='reminder.patient.full_name', 
        read_only=True
    )
    time_until = serializers.SerializerMethodField()
    
    class Meta:
        model = ReminderSchedule
        fields = [
            'id', 'reminder', 'reminder_title', 'reminder_type',
            'patient_name', 'scheduled_time', 'is_sent', 'sent_at',
            'is_acknowledged', 'acknowledged_at', 'response_time',
            'attempt_count', 'last_attempt_at', 'action_taken',
            'notes', 'created_at', 'notification_id', 'time_until'
        ]
        read_only_fields = [
            'is_sent', 'sent_at', 'is_acknowledged', 'acknowledged_at',
            'response_time', 'attempt_count', 'last_attempt_at',
            'created_at', 'notification_id'
        ]
    
    def get_time_until(self, obj):
        """
        زمان باقی‌مانده تا یادآوری
        """
        if not obj.is_sent and obj.scheduled_time > timezone.now():
            delta = obj.scheduled_time - timezone.now()
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if days > 0:
                return f"{days} روز و {hours} ساعت"
            elif hours > 0:
                return f"{hours} ساعت و {minutes} دقیقه"
            else:
                return f"{minutes} دقیقه"
        return None
    
    def validate_scheduled_time(self, value):
        """
        اعتبارسنجی زمان برنامه‌ریزی
        """
        if value < timezone.now():
            raise serializers.ValidationError(
                "زمان برنامه‌ریزی نمی‌تواند در گذشته باشد"
            )
        return value


class ReminderResponseSerializer(serializers.ModelSerializer):
    """
    Serializer برای پاسخ به یادآوری
    """
    schedule_time = serializers.DateTimeField(
        source='schedule.scheduled_time', 
        read_only=True
    )
    reminder_title = serializers.CharField(
        source='schedule.reminder.title', 
        read_only=True
    )
    reminder_type = serializers.CharField(
        source='schedule.reminder.reminder_type', 
        read_only=True
    )
    patient_name = serializers.CharField(
        source='schedule.reminder.patient.full_name', 
        read_only=True
    )
    response_delay_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ReminderResponse
        fields = [
            'id', 'schedule', 'schedule_time', 'reminder_title',
            'reminder_type', 'patient_name', 'response_type',
            'response_time', 'response_delay', 'response_delay_display',
            'action_result', 'patient_feedback', 'satisfaction_score',
            'device_type', 'location', 'created_at'
        ]
        read_only_fields = [
            'response_time', 'response_delay', 'created_at'
        ]
    
    def get_response_delay_display(self, obj):
        """
        نمایش خوانای تاخیر پاسخ
        """
        if obj.response_delay:
            total_seconds = obj.response_delay.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            if hours > 0:
                return f"{hours} ساعت و {minutes} دقیقه"
            else:
                return f"{minutes} دقیقه"
        return None
    
    def validate_satisfaction_score(self, value):
        """
        اعتبارسنجی امتیاز رضایت
        """
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError(
                "امتیاز رضایت باید بین 1 تا 5 باشد"
            )
        return value
    
    def validate_action_result(self, value):
        """
        اعتبارسنجی نتیجه اقدام
        """
        valid_actions = ['TAKEN', 'POSTPONED', 'SKIPPED', 'PARTIAL']
        if value and value not in valid_actions:
            raise serializers.ValidationError(
                f"نتیجه اقدام باید یکی از موارد {valid_actions} باشد"
            )
        return value


class SmartReminderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer برای ایجاد یادآوری جدید با قابلیت‌های پیشرفته
    """
    auto_schedule = serializers.BooleanField(
        default=True,
        help_text="آیا برنامه‌های زمان‌بندی به صورت خودکار ایجاد شوند"
    )
    use_behavior_analysis = serializers.BooleanField(
        default=True,
        help_text="آیا از تحلیل رفتاری برای زمان‌بندی استفاده شود"
    )
    
    class Meta:
        model = SmartReminder
        fields = [
            'patient', 'reminder_type', 'title', 'description',
            'medication_id', 'lab_test_id', 'start_date', 'end_date',
            'frequency', 'times_per_day', 'days_of_week', 'preferred_times',
            'status', 'is_adaptive', 'priority', 'is_critical',
            'auto_schedule', 'use_behavior_analysis'
        ]
    
    def create(self, validated_data):
        """
        ایجاد یادآوری با تنظیمات هوشمند
        """
        # حذف فیلدهای اضافی
        auto_schedule = validated_data.pop('auto_schedule', True)
        use_behavior_analysis = validated_data.pop('use_behavior_analysis', True)
        
        # ایجاد یادآوری
        reminder = SmartReminder.objects.create(**validated_data)
        
        # اگر تحلیل رفتاری فعال است
        if use_behavior_analysis and reminder.is_adaptive:
            from .smart_reminder_services import BehaviorAnalysisService
            behavior_service = BehaviorAnalysisService()
            
            # دریافت بهترین زمان‌ها از تحلیل رفتاری
            analysis = behavior_service.analyze_patient_behavior(
                str(reminder.patient.id),
                reminder.reminder_type
            )
            
            if analysis['best_times']:
                reminder.preferred_times = [
                    f"{hour:02d}:00" for hour in analysis['best_times'][:reminder.times_per_day]
                ]
                reminder.save()
        
        return reminder


class ReminderStatisticsSerializer(serializers.Serializer):
    """
    Serializer برای آمار یادآورها
    """
    total_reminders = serializers.IntegerField()
    active_reminders = serializers.IntegerField()
    total_schedules = serializers.IntegerField()
    sent_schedules = serializers.IntegerField()
    acknowledged_schedules = serializers.IntegerField()
    overall_compliance_rate = serializers.FloatField()
    
    reminders_by_type = serializers.DictField(
        child=serializers.IntegerField()
    )
    compliance_by_type = serializers.DictField(
        child=serializers.FloatField()
    )
    upcoming_schedules = serializers.ListField(
        child=serializers.DictField()
    )