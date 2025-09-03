from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Report, PatientAnalytics, DoctorAnalytics, SystemAnalytics
from .services import PatientAnalyticsService, DoctorAnalyticsService, SystemAnalyticsService
from .report_service import ReportGenerationService
from encounters.models import Patient
from security.models import DoctorProfile

User = get_user_model()


@shared_task
def calculate_daily_analytics():
    """محاسبه آنالیتیکس روزانه برای همه بیماران و پزشکان"""
    today = timezone.now().date()
    
    # محاسبه آنالیتیکس بیماران
    patient_service = PatientAnalyticsService()
    patients = Patient.objects.filter(is_active=True)
    
    for patient in patients:
        try:
            patient_service.calculate_patient_analytics(patient, today)
        except Exception as e:
            print(f"Error calculating analytics for patient {patient.id}: {e}")
    
    # محاسبه آنالیتیکس پزشکان
    doctor_service = DoctorAnalyticsService()
    doctors = DoctorProfile.objects.filter(is_active=True)
    
    for doctor in doctors:
        try:
            doctor_service.calculate_doctor_analytics(doctor, today)
        except Exception as e:
            print(f"Error calculating analytics for doctor {doctor.id}: {e}")
    
    # محاسبه آنالیتیکس سیستم
    system_service = SystemAnalyticsService()
    try:
        system_service.calculate_system_analytics(today)
    except Exception as e:
        print(f"Error calculating system analytics: {e}")
    
    return f"Analytics calculated for {patients.count()} patients and {doctors.count()} doctors"


@shared_task
def generate_scheduled_reports():
    """تولید گزارش‌های زمان‌بندی شده"""
    # گزارش‌های ماهانه برای پزشکان
    if timezone.now().day == 1:  # اول هر ماه
        generate_monthly_doctor_reports.delay()
    
    # گزارش‌های هفتگی سیستم
    if timezone.now().weekday() == 0:  # دوشنبه‌ها
        generate_weekly_system_report.delay()
    
    return "Scheduled reports generation triggered"


@shared_task
def generate_monthly_doctor_reports():
    """تولید گزارش ماهانه برای همه پزشکان"""
    service = ReportGenerationService()
    doctors = DoctorProfile.objects.filter(is_active=True)
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    reports_created = 0
    
    for doctor in doctors:
        try:
            # ایجاد گزارش
            report = Report.objects.create(
                report_type='doctor_performance',
                format='pdf',
                requested_by=doctor.user,
                doctor=doctor,
                start_date=start_date,
                end_date=end_date,
                metadata={
                    'scheduled': True,
                    'report_period': 'monthly'
                }
            )
            
            # تولید گزارش
            service.generate_report(report)
            
            # ارسال ایمیل
            if doctor.user.email:
                service.send_report_email(report, [doctor.user.email])
            
            reports_created += 1
            
        except Exception as e:
            print(f"Error generating report for doctor {doctor.id}: {e}")
    
    return f"Generated {reports_created} monthly doctor reports"


@shared_task
def generate_weekly_system_report():
    """تولید گزارش هفتگی سیستم"""
    service = ReportGenerationService()
    
    # ارسال به ادمین‌ها
    admin_users = User.objects.filter(is_superuser=True, is_active=True)
    
    if not admin_users.exists():
        return "No admin users found"
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    try:
        # ایجاد گزارش
        report = Report.objects.create(
            report_type='system_overview',
            format='pdf',
            requested_by=admin_users.first(),
            start_date=start_date,
            end_date=end_date,
            metadata={
                'scheduled': True,
                'report_period': 'weekly'
            }
        )
        
        # تولید گزارش
        service.generate_report(report)
        
        # ارسال به همه ادمین‌ها
        admin_emails = list(admin_users.values_list('email', flat=True).exclude(email=''))
        if admin_emails:
            service.send_report_email(report, admin_emails)
        
        return f"Weekly system report sent to {len(admin_emails)} admins"
        
    except Exception as e:
        return f"Error generating weekly system report: {e}"


@shared_task
def cleanup_old_analytics():
    """پاکسازی داده‌های آنالیتیکس قدیمی"""
    # حذف آنالیتیکس بیش از 1 سال
    cutoff_date = timezone.now().date() - timedelta(days=365)
    
    deleted_counts = {
        'patient': PatientAnalytics.objects.filter(date__lt=cutoff_date).delete()[0],
        'doctor': DoctorAnalytics.objects.filter(date__lt=cutoff_date).delete()[0],
        'system': SystemAnalytics.objects.filter(date__lt=cutoff_date).delete()[0],
    }
    
    return f"Deleted old analytics: {deleted_counts}"


@shared_task
def check_critical_values():
    """بررسی مقادیر بحرانی و ارسال هشدار"""
    from notifications.models import ClinicalAlert
    
    # بررسی آخرین آنالیتیکس بیماران
    recent_analytics = PatientAnalytics.objects.filter(
        date=timezone.now().date()
    ).select_related('patient')
    
    alerts_created = 0
    
    for analytics in recent_analytics:
        # بررسی HbA1c بحرانی
        if analytics.avg_hba1c and analytics.avg_hba1c > 10:
            alert, created = ClinicalAlert.objects.get_or_create(
                patient=analytics.patient,
                alert_type='critical_hba1c',
                severity='critical',
                defaults={
                    'message': f'HbA1c بحرانی: {analytics.avg_hba1c}% - نیاز به اقدام فوری',
                    'data': {'hba1c': analytics.avg_hba1c}
                }
            )
            if created:
                alerts_created += 1
        
        # بررسی قند خون بحرانی
        if analytics.avg_glucose:
            if analytics.avg_glucose < 50 or analytics.avg_glucose > 400:
                alert, created = ClinicalAlert.objects.get_or_create(
                    patient=analytics.patient,
                    alert_type='critical_glucose',
                    severity='critical',
                    defaults={
                        'message': f'قند خون بحرانی: {analytics.avg_glucose} mg/dL',
                        'data': {'glucose': analytics.avg_glucose}
                    }
                )
                if created:
                    alerts_created += 1
    
    return f"Created {alerts_created} critical alerts"


# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'calculate-daily-analytics': {
        'task': 'analytics.tasks.calculate_daily_analytics',
        'schedule': crontab(hour=2, minute=0),  # هر روز ساعت 2 صبح
    },
    'generate-scheduled-reports': {
        'task': 'analytics.tasks.generate_scheduled_reports',
        'schedule': crontab(hour=8, minute=0),  # هر روز ساعت 8 صبح
    },
    'cleanup-old-analytics': {
        'task': 'analytics.tasks.cleanup_old_analytics',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # یکشنبه‌ها ساعت 3 صبح
    },
    'check-critical-values': {
        'task': 'analytics.tasks.check_critical_values',
        'schedule': crontab(minute='*/30'),  # هر 30 دقیقه
    },
}