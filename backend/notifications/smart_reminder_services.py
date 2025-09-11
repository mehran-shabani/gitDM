"""
سرویس‌های سیستم یادآوری هوشمند
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Avg, Count, F
from django.conf import settings
import logging
import random
from statistics import mode, median

from .models import (
    SmartReminder, ReminderPattern, ReminderSchedule,
    ReminderResponse, Notification
)
from .services import NotificationService

logger = logging.getLogger(__name__)


class BehaviorAnalysisService:
    """
    سرویس تحلیل رفتار بیمار برای بهینه‌سازی زمان یادآوری
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def analyze_patient_behavior(self, patient_id: str, reminder_type: str) -> Dict:
        """
        تحلیل رفتار بیمار برای یک نوع یادآوری
        """
        pattern, created = ReminderPattern.objects.get_or_create(
            patient_id=patient_id,
            reminder_type=reminder_type
        )
        
        # تحلیل پاسخ‌های قبلی
        responses = ReminderResponse.objects.filter(
            schedule__reminder__patient_id=patient_id,
            schedule__reminder__reminder_type=reminder_type
        ).order_by('-created_at')[:100]  # 100 پاسخ اخیر
        
        analysis = {
            'compliance_rate': pattern.compliance_rate,
            'best_times': self._calculate_best_times(responses),
            'worst_times': pattern.worst_response_times,
            'average_response_time': self._calculate_avg_response_time(responses),
            'preferred_channel': pattern.preferred_notification_channel,
            'recommendations': []
        }
        
        # توصیه‌ها بر اساس تحلیل
        if pattern.compliance_rate < 50:
            analysis['recommendations'].append({
                'type': 'low_compliance',
                'message': 'نرخ تبعیت پایین است. پیشنهاد می‌شود زمان یادآوری تغییر کند.',
                'action': 'adjust_timing'
            })
        
        if len(analysis['best_times']) > 0:
            analysis['recommendations'].append({
                'type': 'optimal_timing',
                'message': f'بهترین زمان‌ها برای یادآوری: {analysis["best_times"]}',
                'action': 'use_best_times'
            })
        
        return analysis
    
    def _calculate_best_times(self, responses) -> List[int]:
        """
        محاسبه بهترین زمان‌های یادآوری بر اساس پاسخ‌ها
        """
        immediate_responses = responses.filter(
            response_type='IMMEDIATE',
            action_result__in=['TAKEN', 'COMPLETED']
        )
        
        if not immediate_responses.exists():
            return []
        
        response_hours = [
            resp.response_time.hour 
            for resp in immediate_responses
        ]
        
        # یافتن ساعات پرتکرار
        hour_counts = {}
        for hour in response_hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # ساعاتی که بیش از 20% پاسخ‌ها در آن بوده
        threshold = len(response_hours) * 0.2
        best_hours = [
            hour for hour, count in hour_counts.items()
            if count >= threshold
        ]
        
        return sorted(best_hours)
    
    def _calculate_avg_response_time(self, responses) -> Optional[timedelta]:
        """
        محاسبه میانگین زمان پاسخ
        """
        valid_responses = responses.filter(
            response_delay__isnull=False
        ).values_list('response_delay', flat=True)
        
        if not valid_responses:
            return None
        
        total_seconds = sum(r.total_seconds() for r in valid_responses)
        avg_seconds = total_seconds / len(valid_responses)
        
        return timedelta(seconds=avg_seconds)
    
    def get_patient_preferences(self, patient_id: str) -> Dict:
        """
        دریافت ترجیحات بیمار بر اساس تاریخچه
        """
        patterns = ReminderPattern.objects.filter(patient_id=patient_id)
        
        preferences = {
            'notification_channels': {},
            'best_times_by_type': {},
            'compliance_by_type': {}
        }
        
        for pattern in patterns:
            preferences['notification_channels'][pattern.reminder_type] = pattern.preferred_notification_channel
            preferences['best_times_by_type'][pattern.reminder_type] = pattern.best_response_times
            preferences['compliance_by_type'][pattern.reminder_type] = float(pattern.compliance_rate)
        
        return preferences


class SmartSchedulerService:
    """
    سرویس زمان‌بندی هوشمند یادآورها
    """
    
    def __init__(self):
        self.behavior_service = BehaviorAnalysisService()
    
    def create_schedules_for_reminder(self, reminder: SmartReminder) -> List[ReminderSchedule]:
        """
        ایجاد برنامه زمان‌بندی برای یک یادآوری
        """
        schedules = []
        
        if reminder.frequency == 'ONCE':
            # یکبار
            schedule_time = self._get_optimal_time_for_date(
                reminder, 
                reminder.start_date
            )
            schedules.append(self._create_schedule(reminder, schedule_time))
            
        elif reminder.frequency == 'DAILY':
            # روزانه
            current_date = reminder.start_date
            end_date = reminder.end_date or (current_date + timedelta(days=365))
            
            while current_date <= end_date:
                for i in range(reminder.times_per_day):
                    schedule_time = self._get_optimal_time_for_date(
                        reminder, 
                        current_date,
                        occurrence=i
                    )
                    schedules.append(self._create_schedule(reminder, schedule_time))
                current_date += timedelta(days=1)
                
        elif reminder.frequency == 'WEEKLY':
            # هفتگی
            current_date = reminder.start_date
            end_date = reminder.end_date or (current_date + timedelta(days=365))
            
            while current_date <= end_date:
                if not reminder.days_of_week or current_date.weekday() in reminder.days_of_week:
                    schedule_time = self._get_optimal_time_for_date(
                        reminder, 
                        current_date
                    )
                    schedules.append(self._create_schedule(reminder, schedule_time))
                current_date += timedelta(days=7)
                
        elif reminder.frequency == 'MONTHLY':
            # ماهانه
            current_date = reminder.start_date
            end_date = reminder.end_date or (current_date + timedelta(days=365))
            
            while current_date <= end_date:
                schedule_time = self._get_optimal_time_for_date(
                    reminder, 
                    current_date
                )
                schedules.append(self._create_schedule(reminder, schedule_time))
                
                # به ماه بعد
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, 
                        month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        # ذخیره در دیتابیس
        created_schedules = ReminderSchedule.objects.bulk_create(schedules)
        
        logger.info(f"Created {len(created_schedules)} schedules for reminder {reminder.id}")
        
        return created_schedules
    
    def _get_optimal_time_for_date(
        self, 
        reminder: SmartReminder, 
        date, 
        occurrence: int = 0
    ) -> datetime:
        """
        محاسبه زمان بهینه برای یادآوری در یک تاریخ مشخص
        """
        if reminder.is_adaptive:
            # استفاده از تحلیل رفتاری
            behavior = self.behavior_service.analyze_patient_behavior(
                reminder.patient_id,
                reminder.reminder_type
            )
            best_times = behavior.get('best_times', [])
            
            if best_times:
                # انتخاب یکی از بهترین زمان‌ها
                if occurrence < len(best_times):
                    hour = best_times[occurrence]
                else:
                    hour = best_times[occurrence % len(best_times)]
            else:
                # زمان‌های پیش‌فرض بر اساس نوع یادآوری
                hour = self._get_default_time_for_type(
                    reminder.reminder_type, 
                    occurrence
                )
        else:
            # استفاده از زمان‌های ترجیحی تنظیم شده
            if reminder.preferred_times and occurrence < len(reminder.preferred_times):
                time_str = reminder.preferred_times[occurrence]
                hour = int(time_str.split(':')[0])
            else:
                hour = self._get_default_time_for_type(
                    reminder.reminder_type, 
                    occurrence
                )
        
        # تنظیم دقیقه به صورت تصادفی برای طبیعی‌تر شدن
        minute = random.randint(0, 59)
        
        return timezone.make_aware(
            datetime.combine(date, time(hour=hour, minute=minute))
        )
    
    def _get_default_time_for_type(self, reminder_type: str, occurrence: int) -> int:
        """
        زمان‌های پیش‌فرض بر اساس نوع یادآوری
        """
        default_times = {
            'MEDICATION': [8, 12, 20],  # صبح، ظهر، شب
            'LAB_TEST': [9],  # صبح
            'APPOINTMENT': [8],  # صبح روز ویزیت
            'EXERCISE': [7, 17],  # صبح زود، عصر
            'DIET': [7, 12, 19],  # قبل از وعده‌های غذایی
            'GLUCOSE_CHECK': [7, 11, 16, 21]  # قبل و بعد از وعده‌ها
        }
        
        times = default_times.get(reminder_type, [9])
        if occurrence < len(times):
            return times[occurrence]
        return times[0]
    
    def _create_schedule(self, reminder: SmartReminder, schedule_time: datetime) -> ReminderSchedule:
        """
        ایجاد یک برنامه زمان‌بندی
        """
        return ReminderSchedule(
            reminder=reminder,
            scheduled_time=schedule_time
        )
    
    def adjust_schedule_based_on_feedback(
        self, 
        schedule: ReminderSchedule, 
        feedback: Dict
    ):
        """
        تنظیم زمان‌بندی بر اساس بازخورد
        """
        if feedback.get('response_type') == 'NO_RESPONSE':
            # اگر پاسخی نداده، زمان را تغییر دهیم
            new_hour = (schedule.scheduled_time.hour + 2) % 24
            new_time = schedule.scheduled_time.replace(hour=new_hour)
            
            # ایجاد یادآوری جدید
            new_schedule = ReminderSchedule.objects.create(
                reminder=schedule.reminder,
                scheduled_time=new_time
            )
            
            logger.info(f"Adjusted schedule time from {schedule.scheduled_time} to {new_time}")
            
        elif feedback.get('response_type') == 'DELAYED':
            # اگر با تاخیر پاسخ داده، زمان را به زمان پاسخ نزدیک کنیم
            response_time = feedback.get('response_time')
            if response_time:
                pattern = ReminderPattern.objects.get(
                    patient=schedule.reminder.patient,
                    reminder_type=schedule.reminder.reminder_type
                )
                pattern.best_response_times.append(response_time.hour)
                pattern.save()


class ReminderDeliveryService:
    """
    سرویس ارسال یادآورها
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def process_pending_reminders(self):
        """
        پردازش یادآورهای در انتظار ارسال
        """
        now = timezone.now()
        window_start = now - timedelta(minutes=5)
        window_end = now + timedelta(minutes=5)
        
        # یادآورهای آماده ارسال
        pending_schedules = ReminderSchedule.objects.filter(
            is_sent=False,
            scheduled_time__gte=window_start,
            scheduled_time__lte=window_end,
            reminder__status=SmartReminder.Status.ACTIVE
        ).select_related('reminder', 'reminder__patient')
        
        sent_count = 0
        
        for schedule in pending_schedules:
            try:
                self._send_reminder(schedule)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending reminder {schedule.id}: {str(e)}")
        
        logger.info(f"Sent {sent_count} reminders")
        
        return sent_count
    
    def _send_reminder(self, schedule: ReminderSchedule):
        """
        ارسال یک یادآوری
        """
        reminder = schedule.reminder
        patient = reminder.patient
        
        # تعیین کانال ارسال
        pattern = ReminderPattern.objects.filter(
            patient=patient,
            reminder_type=reminder.reminder_type
        ).first()
        
        channel = pattern.preferred_notification_channel if pattern else 'IN_APP'
        
        # ساخت پیام
        message = self._build_reminder_message(reminder, schedule)
        
        # ارسال نوتیفیکیشن
        if channel == 'IN_APP':
            notification = self.notification_service.create_notification(
                recipient=patient.primary_doctor.user,
                title=reminder.title,
                message=message['body'],
                notification_type=Notification.NotificationType.REMINDER,
                priority=self._get_priority_level(reminder),
                patient_id=str(patient.id),
                resource_type='SmartReminder',
                resource_id=str(reminder.id)
            )
            
            schedule.notification_id = str(notification.id)
        
        # علامت‌گذاری به عنوان ارسال شده
        schedule.mark_as_sent()
        
        logger.info(f"Sent reminder {reminder.id} via {channel}")
    
    def _build_reminder_message(self, reminder: SmartReminder, schedule: ReminderSchedule) -> Dict:
        """
        ساخت پیام یادآوری
        """
        templates = {
            'MEDICATION': {
                'title': 'یادآوری مصرف دارو',
                'body': f'زمان مصرف {reminder.title} فرا رسیده است. {reminder.description}'
            },
            'LAB_TEST': {
                'title': 'یادآوری آزمایش',
                'body': f'لطفاً برای انجام {reminder.title} اقدام کنید. {reminder.description}'
            },
            'APPOINTMENT': {
                'title': 'یادآوری ویزیت',
                'body': f'نوبت ویزیت شما: {reminder.title}. {reminder.description}'
            },
            'EXERCISE': {
                'title': 'یادآوری ورزش',
                'body': f'زمان {reminder.title} است. {reminder.description}'
            },
            'DIET': {
                'title': 'یادآوری رژیم غذایی',
                'body': f'{reminder.title}. {reminder.description}'
            },
            'GLUCOSE_CHECK': {
                'title': 'یادآوری چک قند خون',
                'body': f'لطفاً قند خون خود را چک کنید. {reminder.description}'
            }
        }
        
        template = templates.get(
            reminder.reminder_type,
            {'title': reminder.title, 'body': reminder.description}
        )
        
        # شخصی‌سازی پیام
        if schedule.attempt_count > 0:
            template['body'] += f' (یادآوری مجدد - تلاش {schedule.attempt_count + 1})'
        
        return template
    
    def _get_priority_level(self, reminder: SmartReminder) -> str:
        """
        تعیین سطح اولویت نوتیفیکیشن
        """
        if reminder.is_critical:
            return Notification.Priority.URGENT
        elif reminder.priority >= 8:
            return Notification.Priority.HIGH
        elif reminder.priority >= 5:
            return Notification.Priority.MEDIUM
        else:
            return Notification.Priority.LOW
    
    def handle_reminder_response(
        self, 
        schedule_id: int, 
        response_data: Dict
    ) -> ReminderResponse:
        """
        ثبت پاسخ بیمار به یادآوری
        """
        schedule = ReminderSchedule.objects.get(id=schedule_id)
        
        # محاسبه تاخیر در پاسخ
        response_time = timezone.now()
        response_delay = response_time - schedule.sent_at if schedule.sent_at else None
        
        # تعیین نوع پاسخ
        if response_delay and response_delay < timedelta(minutes=5):
            response_type = 'IMMEDIATE'
        elif response_delay and response_delay < timedelta(hours=1):
            response_type = 'DELAYED'
        else:
            response_type = 'NO_RESPONSE'
        
        # ثبت پاسخ
        response = ReminderResponse.objects.create(
            schedule=schedule,
            response_type=response_type,
            response_time=response_time,
            response_delay=response_delay,
            action_result=response_data.get('action_result'),
            patient_feedback=response_data.get('feedback', ''),
            satisfaction_score=response_data.get('satisfaction_score'),
            device_type=response_data.get('device_type', ''),
            location=response_data.get('location', '')
        )
        
        # بروزرسانی schedule
        schedule.acknowledge(
            action_taken=response_data.get('action_result'),
            notes=response_data.get('notes', '')
        )
        
        # بروزرسانی الگوی رفتاری
        self._update_behavior_pattern(schedule, response)
        
        return response
    
    def _update_behavior_pattern(
        self, 
        schedule: ReminderSchedule, 
        response: ReminderResponse
    ):
        """
        بروزرسانی الگوی رفتاری بر اساس پاسخ
        """
        pattern, created = ReminderPattern.objects.get_or_create(
            patient=schedule.reminder.patient,
            reminder_type=schedule.reminder.reminder_type
        )
        
        # بروزرسانی آمار
        if response.response_type in ['IMMEDIATE', 'DELAYED']:
            pattern.update_pattern(response.response_time, True)
        else:
            pattern.update_pattern(schedule.scheduled_time, False)
        
        # بروزرسانی میانگین زمان پاسخ
        if response.response_delay:
            delays = ReminderResponse.objects.filter(
                schedule__reminder__patient=schedule.reminder.patient,
                schedule__reminder__reminder_type=schedule.reminder.reminder_type,
                response_delay__isnull=False
            ).values_list('response_delay', flat=True)[:50]
            
            if delays:
                avg_seconds = sum(d.total_seconds() for d in delays) / len(delays)
                pattern.average_response_time = timedelta(seconds=avg_seconds)
                pattern.save()


class AdaptiveLearningService:
    """
    سرویس یادگیری و بهبود مستمر سیستم یادآوری
    """
    
    def __init__(self):
        self.behavior_service = BehaviorAnalysisService()
        self.scheduler_service = SmartSchedulerService()
    
    def optimize_reminder_timing(self, patient_id: str):
        """
        بهینه‌سازی زمان‌بندی یادآورها برای یک بیمار
        """
        reminders = SmartReminder.objects.filter(
            patient_id=patient_id,
            status=SmartReminder.Status.ACTIVE,
            is_adaptive=True
        )
        
        for reminder in reminders:
            # تحلیل رفتار
            behavior = self.behavior_service.analyze_patient_behavior(
                patient_id,
                reminder.reminder_type
            )
            
            # اگر نرخ تبعیت پایین است، زمان‌ها را تنظیم کنیم
            if behavior['compliance_rate'] < 70:
                self._adjust_reminder_times(reminder, behavior)
            
            # بروزرسانی زمان‌های ترجیحی
            if behavior['best_times']:
                reminder.preferred_times = [f"{h}:00" for h in behavior['best_times']]
                reminder.save()
    
    def _adjust_reminder_times(self, reminder: SmartReminder, behavior: Dict):
        """
        تنظیم زمان‌های یادآوری بر اساس تحلیل رفتاری
        """
        # حذف برنامه‌های آینده
        future_schedules = ReminderSchedule.objects.filter(
            reminder=reminder,
            scheduled_time__gt=timezone.now(),
            is_sent=False
        )
        future_schedules.delete()
        
        # ایجاد برنامه‌های جدید با زمان‌های بهینه
        if behavior['best_times']:
            reminder.preferred_times = [f"{h}:00" for h in behavior['best_times']]
            reminder.save()
        
        # ایجاد مجدد برنامه‌ها
        self.scheduler_service.create_schedules_for_reminder(reminder)
        
        logger.info(f"Adjusted timing for reminder {reminder.id}")
    
    def generate_insights(self, patient_id: str) -> List[Dict]:
        """
        تولید بینش‌ها و پیشنهادات برای بهبود
        """
        insights = []
        
        # بررسی الگوهای رفتاری
        patterns = ReminderPattern.objects.filter(patient_id=patient_id)
        
        for pattern in patterns:
            if pattern.compliance_rate < 50:
                insights.append({
                    'type': 'low_compliance',
                    'severity': 'high',
                    'message': f'نرخ تبعیت از یادآورهای {pattern.get_reminder_type_display()} پایین است ({pattern.compliance_rate:.1f}%)',
                    'suggestion': 'تغییر زمان یادآوری یا روش ارتباط را در نظر بگیرید'
                })
            
            if pattern.average_response_time and pattern.average_response_time > timedelta(hours=2):
                insights.append({
                    'type': 'slow_response',
                    'severity': 'medium',
                    'message': f'میانگین زمان پاسخ به یادآورهای {pattern.get_reminder_type_display()} بالا است',
                    'suggestion': 'یادآورهای تکراری یا تغییر محتوای پیام را امتحان کنید'
                })
        
        # بررسی یادآورهای بحرانی
        critical_reminders = SmartReminder.objects.filter(
            patient_id=patient_id,
            is_critical=True,
            status=SmartReminder.Status.ACTIVE
        )
        
        for reminder in critical_reminders:
            recent_responses = ReminderResponse.objects.filter(
                schedule__reminder=reminder,
                created_at__gte=timezone.now() - timedelta(days=7)
            )
            
            missed_count = recent_responses.filter(
                response_type='NO_RESPONSE'
            ).count()
            
            if missed_count > 2:
                insights.append({
                    'type': 'critical_missed',
                    'severity': 'critical',
                    'message': f'یادآوری بحرانی "{reminder.title}" چندین بار نادیده گرفته شده',
                    'suggestion': 'تماس مستقیم یا پیگیری فوری توصیه می‌شود'
                })
        
        return insights
    
    def predict_best_time(
        self, 
        patient_id: str, 
        reminder_type: str, 
        date: datetime
    ) -> List[Tuple[int, float]]:
        """
        پیش‌بینی بهترین زمان‌ها برای یادآوری در یک روز مشخص
        """
        # دریافت داده‌های تاریخی
        responses = ReminderResponse.objects.filter(
            schedule__reminder__patient_id=patient_id,
            schedule__reminder__reminder_type=reminder_type,
            response_type__in=['IMMEDIATE', 'DELAYED']
        ).order_by('-created_at')[:200]
        
        if not responses.exists():
            # زمان‌های پیش‌فرض
            return [(8, 0.7), (12, 0.6), (20, 0.5)]
        
        # محاسبه احتمال پاسخ برای هر ساعت
        hour_success = {}
        hour_total = {}
        
        for response in responses:
            hour = response.response_time.hour
            hour_total[hour] = hour_total.get(hour, 0) + 1
            
            if response.action_result in ['TAKEN', 'COMPLETED']:
                hour_success[hour] = hour_success.get(hour, 0) + 1
        
        # محاسبه احتمال موفقیت
        probabilities = []
        for hour in range(24):
            if hour in hour_total and hour_total[hour] >= 5:
                success_rate = hour_success.get(hour, 0) / hour_total[hour]
                probabilities.append((hour, success_rate))
        
        # مرتب‌سازی بر اساس احتمال موفقیت
        probabilities.sort(key=lambda x: x[1], reverse=True)
        
        # بازگشت 3 بهترین زمان
        return probabilities[:3]