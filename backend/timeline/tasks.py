from celery import shared_task
from django.utils import timezone
from .services import ReminderService
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_daily_test_reminders():
    """
    Task برای ارسال روزانه یادآورهای آزمایشات
    این task باید روزانه اجرا شود
    """
    try:
        notifications_sent = ReminderService.send_reminder_notifications()
        logger.info(f'یادآورهای آزمایشات ارسال شد: {notifications_sent} اطلاع‌رسانی')
        return f'تعداد {notifications_sent} یادآوری ارسال شد'
    except Exception as e:
        logger.error(f'خطا در ارسال یادآورهای آزمایشات: {str(e)}')
        raise


@shared_task
def cleanup_old_timeline_events():
    """
    Task برای پاک‌سازی رویدادهای قدیمی تایم‌لاین
    این task باید ماهانه اجرا شود
    """
    from .models import MedicalTimeline
    
    try:
        # حذف رویدادهای بیش از ۵ سال قدیمی که غیرقابل نمایش هستند
        cutoff_date = timezone.now() - timezone.timedelta(days=5*365)
        
        deleted_count = MedicalTimeline.objects.filter(
            occurred_at__lt=cutoff_date,
            is_visible=False
        ).delete()[0]
        
        logger.info(f'پاک‌سازی تایم‌لاین: {deleted_count} رویداد قدیمی حذف شد')
        return f'تعداد {deleted_count} رویداد قدیمی حذف شد'
    except Exception as e:
        logger.error(f'خطا در پاک‌سازی تایم‌لاین: {str(e)}')
        raise


@shared_task
def generate_monthly_timeline_report():
    """
    Task برای تولید گزارش ماهانه تایم‌لاین
    """
    from .models import MedicalTimeline, TestReminder
    from gitdm.models import PatientProfile
    
    try:
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # آمار کلی
        total_events = MedicalTimeline.objects.filter(
            occurred_at__gte=current_month
        ).count()
        
        overdue_reminders = TestReminder.objects.filter(
            next_due__lt=timezone.now(),
            is_active=True
        ).count()
        
        active_patients = PatientProfile.objects.filter(
            timeline_events__occurred_at__gte=current_month
        ).distinct().count()
        
        report = {
            'month': current_month.strftime('%Y-%m'),
            'total_events': total_events,
            'overdue_reminders': overdue_reminders,
            'active_patients': active_patients
        }
        
        logger.info(f'گزارش ماهانه تایم‌لاین: {report}')
        return report
    except Exception as e:
        logger.error(f'خطا در تولید گزارش ماهانه: {str(e)}')
        raise