from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from typing import List, Dict, Any

from .models import MedicalTimeline, TestReminder, ReminderTemplate
from notifications.services import NotificationService


class TimelineService:
    """
    سرویس مدیریت تایم‌لاین پزشکی
    """
    
    @staticmethod
    def create_timeline_event_from_encounter(encounter):
        """ایجاد رویداد تایم‌لاین از مواجهه"""
        return MedicalTimeline.create_from_encounter(encounter)
    
    @staticmethod
    def create_timeline_event_from_lab_result(lab_result):
        """ایجاد رویداد تایم‌لاین از نتیجه آزمایش"""
        return MedicalTimeline.create_from_lab_result(lab_result)
    
    @staticmethod
    def get_patient_timeline(patient, start_date=None, end_date=None, event_types=None, limit=100):
        """دریافت تایم‌لاین کامل بیمار با فیلترهای مختلف"""
        queryset = MedicalTimeline.objects.filter(
            patient=patient,
            is_visible=True
        ).select_related('patient', 'created_by', 'content_type')
        
        # اعمال فیلترها
        if start_date:
            queryset = queryset.filter(occurred_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(occurred_at__lte=end_date)
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return queryset[:limit]
    
    @staticmethod
    def get_timeline_statistics(patient):
        """آمار کلی تایم‌لاین بیمار"""
        timeline_events = MedicalTimeline.objects.filter(
            patient=patient, is_visible=True
        )
        
        stats = {}
        for event_type in MedicalTimeline.EventType:
            count = timeline_events.filter(event_type=event_type.value).count()
            if count > 0:
                stats[event_type.label] = count
        
        # آخرین رویدادها
        recent_events = timeline_events.order_by('-occurred_at')[:5]
        
        return {
            'total_events': timeline_events.count(),
            'event_type_counts': stats,
            'recent_events': recent_events
        }
    
    @staticmethod
    def create_medication_timeline_event(patient, medication_data, created_by):
        """ایجاد رویداد تایم‌لاین برای دارو"""
        return MedicalTimeline.objects.create(
            patient=patient,
            event_type=MedicalTimeline.EventType.MEDICATION,
            title=f"تجویز دارو: {medication_data.get('name', 'نامشخص')}",
            description=f"دوز: {medication_data.get('dose', '')}, دستور مصرف: {medication_data.get('instructions', '')}",
            occurred_at=medication_data.get('prescribed_at', timezone.now()),
            created_by=created_by,
            metadata=medication_data
        )


class ReminderService:
    """
    سرویس مدیریت یادآورهای آزمایشات
    """
    
    @staticmethod
    def create_default_reminders_for_patient(patient, created_by):
        """ایجاد یادآورهای پیش‌فرض برای بیمار جدید"""
        default_tests = [
            ('HBA1C', TestReminder.Frequency.QUARTERLY, TestReminder.Priority.HIGH),
            ('FBS', TestReminder.Frequency.MONTHLY, TestReminder.Priority.MEDIUM),
            ('BUN', TestReminder.Frequency.QUARTERLY, TestReminder.Priority.MEDIUM),
            ('CREATININE', TestReminder.Frequency.QUARTERLY, TestReminder.Priority.MEDIUM),
            ('EYE_EXAM', TestReminder.Frequency.ANNUALLY, TestReminder.Priority.HIGH),
            ('BMI', TestReminder.Frequency.MONTHLY, TestReminder.Priority.LOW),
        ]
        
        created_reminders = []
        for test_type, frequency, priority in default_tests:
            # محاسبه تاریخ اولیه بر اساس نوع آزمایش
            if frequency == TestReminder.Frequency.MONTHLY:
                next_due = timezone.now() + timedelta(days=30)
            elif frequency == TestReminder.Frequency.QUARTERLY:
                next_due = timezone.now() + timedelta(days=90)
            elif frequency == TestReminder.Frequency.ANNUALLY:
                next_due = timezone.now() + timedelta(days=365)
            else:
                next_due = timezone.now() + timedelta(days=30)
            
            reminder, created = TestReminder.objects.get_or_create(
                patient=patient,
                test_type=test_type,
                defaults={
                    'frequency': frequency,
                    'priority': priority,
                    'next_due': next_due,
                    'created_by': created_by
                }
            )
            
            if created:
                created_reminders.append(reminder)
        
        return created_reminders
    
    @staticmethod
    def get_overdue_reminders(doctor=None):
        """دریافت یادآورهای عقب‌افتاده"""
        now = timezone.now()
        queryset = TestReminder.objects.filter(
            next_due__lt=now,
            is_active=True
        ).select_related('patient', 'created_by')
        
        if doctor and not doctor.is_superuser:
            queryset = queryset.filter(patient__primary_doctor=doctor)
        
        return queryset
    
    @staticmethod
    def get_upcoming_reminders(doctor=None, days_ahead=7):
        """دریافت یادآورهای آتی"""
        now = timezone.now()
        future_date = now + timedelta(days=days_ahead)
        
        queryset = TestReminder.objects.filter(
            next_due__gte=now,
            next_due__lte=future_date,
            is_active=True
        ).select_related('patient', 'created_by')
        
        if doctor and not doctor.is_superuser:
            queryset = queryset.filter(patient__primary_doctor=doctor)
        
        return queryset
    
    @staticmethod
    def send_reminder_notifications():
        """ارسال اطلاع‌رسانی‌های یادآوری (برای اجرا در cron job)"""
        reminders_to_notify = TestReminder.objects.filter(
            is_active=True
        ).select_related('patient', 'created_by')
        
        notifications_sent = 0
        for reminder in reminders_to_notify:
            if reminder.should_send_reminder():
                # ایجاد notification
                NotificationService.create_test_reminder_notification(reminder)
                notifications_sent += 1
        
        return notifications_sent
    
    @staticmethod
    def update_reminder_from_lab_result(lab_result):
        """به‌روزرسانی یادآوری بر اساس نتیجه آزمایش جدید"""
        # نقشه‌برداری LOINC به نوع یادآوری
        loinc_to_reminder_type = {
            '4548-4': 'HBA1C',  # HbA1c
            '17856-6': 'HBA1C',  # HbA1c
            '2345-7': 'FBS',  # Glucose, fasting
            '2339-0': 'FBS',  # Glucose, fasting
            '1558-6': '2HPP',  # Glucose, post-meal
        }
        
        reminder_type = loinc_to_reminder_type.get(lab_result.loinc)
        if not reminder_type:
            return None
        
        try:
            reminder = TestReminder.objects.get(
                patient=lab_result.patient,
                test_type=reminder_type,
                is_active=True
            )
            reminder.mark_as_completed(lab_result.taken_at)
            return reminder
        except TestReminder.DoesNotExist:
            return None


class TimelineVisualizationService:
    """
    سرویس تولید داده‌های تجسم تایم‌لاین
    """
    
    @staticmethod
    def prepare_timeline_chart_data(patient, start_date=None, end_date=None):
        """آماده‌سازی داده‌ها برای نمودار تایم‌لاین"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=365)  # یک سال گذشته
        if not end_date:
            end_date = timezone.now()
        
        events = TimelineService.get_patient_timeline(
            patient, start_date, end_date
        )
        
        # تبدیل به فرمت مناسب برای نمودار
        chart_data = []
        for event in events:
            chart_data.append({
                'date': event.occurred_at.isoformat(),
                'title': event.title,
                'description': event.description,
                'type': event.event_type,
                'severity': event.severity,
                'metadata': event.metadata
            })
        
        return {
            'patient': {
                'id': patient.id,
                'name': patient.full_name,
                'age': patient.age
            },
            'timeline_data': chart_data,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    @staticmethod
    def get_test_trends(patient, test_types=None, months_back=12):
        """تحلیل روند آزمایشات در طول زمان"""
        start_date = timezone.now() - timedelta(days=30 * months_back)
        
        timeline_events = MedicalTimeline.objects.filter(
            patient=patient,
            event_type=MedicalTimeline.EventType.LAB_RESULT,
            occurred_at__gte=start_date
        ).order_by('occurred_at')
        
        trends = {}
        for event in timeline_events:
            loinc = event.metadata.get('loinc')
            value = event.metadata.get('value')
            
            if loinc and value:
                if loinc not in trends:
                    trends[loinc] = []
                
                trends[loinc].append({
                    'date': event.occurred_at.isoformat(),
                    'value': float(value),
                    'unit': event.metadata.get('unit', '')
                })
        
        return trends