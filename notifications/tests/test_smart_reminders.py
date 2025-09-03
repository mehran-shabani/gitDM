"""
تست‌های سیستم یادآوری هوشمند
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, date
from rest_framework.test import APIClient
from rest_framework import status

from notifications.models import (
    SmartReminder, ReminderPattern, ReminderSchedule, 
    ReminderResponse, Notification
)
from notifications.smart_reminder_services import (
    BehaviorAnalysisService, SmartSchedulerService,
    ReminderDeliveryService, AdaptiveLearningService
)
from gitdm.models import DoctorProfile, PatientProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def doctor_user():
    user = User.objects.create_user(
        email='doctor@test.com',
        password='testpass123',
        first_name='دکتر',
        last_name='تست'
    )
    DoctorProfile.objects.create(
        user=user,
        medical_council_code='12345',
        specialty='ENDOCRINOLOGY',
        role='ENDOCRINOLOGIST'
    )
    return user


@pytest.fixture
def patient(doctor_user):
    return PatientProfile.objects.create(
        national_id='1234567890',
        full_name='بیمار تست',
        date_of_birth=date(1990, 1, 1),
        gender='M',
        primary_doctor=doctor_user.doctor_profile
    )


@pytest.fixture
def smart_reminder(patient):
    return SmartReminder.objects.create(
        patient=patient,
        reminder_type='MEDICATION',
        title='مصرف متفورمین',
        description='قرص متفورمین 500 میلی‌گرم',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        frequency='DAILY',
        times_per_day=2,
        preferred_times=['08:00', '20:00'],
        priority=8,
        is_critical=True,
        created_by=patient.primary_doctor.user
    )


@pytest.fixture
def reminder_pattern(patient):
    return ReminderPattern.objects.create(
        patient=patient,
        reminder_type='MEDICATION',
        best_response_times=[8, 20],
        worst_response_times=[14, 23],
        total_reminders_sent=50,
        total_responses=40,
        compliance_rate=80.0,
        preferred_notification_channel='IN_APP'
    )


class TestSmartReminderModels:
    """تست مدل‌های یادآوری هوشمند"""
    
    @pytest.mark.django_db
    def test_create_smart_reminder(self, patient):
        """تست ایجاد یادآوری هوشمند"""
        reminder = SmartReminder.objects.create(
            patient=patient,
            reminder_type='LAB_TEST',
            title='آزمایش HbA1c',
            description='آزمایش سه ماهه قند خون',
            start_date=date.today(),
            frequency='MONTHLY',
            times_per_day=1,
            priority=7
        )
        
        assert reminder.id is not None
        assert reminder.status == SmartReminder.Status.ACTIVE
        assert reminder.is_adaptive is True
        assert reminder.reminder_type == 'LAB_TEST'
    
    @pytest.mark.django_db
    def test_is_active_on_date(self, smart_reminder):
        """تست بررسی فعال بودن یادآوری در تاریخ مشخص"""
        # تاریخ در محدوده
        assert smart_reminder.is_active_on_date(date.today()) is True
        
        # تاریخ قبل از شروع
        past_date = date.today() - timedelta(days=10)
        assert smart_reminder.is_active_on_date(past_date) is False
        
        # تاریخ بعد از پایان
        future_date = date.today() + timedelta(days=60)
        assert smart_reminder.is_active_on_date(future_date) is False
    
    @pytest.mark.django_db
    def test_reminder_pattern_update(self, reminder_pattern):
        """تست بروزرسانی الگوی رفتاری"""
        initial_sent = reminder_pattern.total_reminders_sent
        initial_responses = reminder_pattern.total_responses
        
        # پاسخ مثبت
        reminder_pattern.update_pattern(
            response_time=timezone.now().replace(hour=9),
            responded=True
        )
        
        assert reminder_pattern.total_reminders_sent == initial_sent + 1
        assert reminder_pattern.total_responses == initial_responses + 1
        assert 9 in reminder_pattern.best_response_times
        
        # عدم پاسخ
        reminder_pattern.update_pattern(
            response_time=timezone.now().replace(hour=15),
            responded=False
        )
        
        assert reminder_pattern.total_reminders_sent == initial_sent + 2
        assert reminder_pattern.total_responses == initial_responses + 1
        assert 15 in reminder_pattern.worst_response_times
    
    @pytest.mark.django_db
    def test_reminder_schedule_acknowledge(self, smart_reminder):
        """تست تایید یادآوری توسط بیمار"""
        schedule = ReminderSchedule.objects.create(
            reminder=smart_reminder,
            scheduled_time=timezone.now()
        )
        
        # ارسال یادآوری
        schedule.mark_as_sent()
        assert schedule.is_sent is True
        assert schedule.sent_at is not None
        
        # تایید توسط بیمار
        schedule.acknowledge(action_taken='COMPLETED', notes='دارو مصرف شد')
        assert schedule.is_acknowledged is True
        assert schedule.acknowledged_at is not None
        assert schedule.action_taken == 'COMPLETED'
        assert schedule.response_time is not None


class TestBehaviorAnalysisService:
    """تست سرویس تحلیل رفتاری"""
    
    @pytest.mark.django_db
    def test_analyze_patient_behavior(self, patient, reminder_pattern):
        """تست تحلیل رفتار بیمار"""
        service = BehaviorAnalysisService()
        analysis = service.analyze_patient_behavior(
            str(patient.id),
            'MEDICATION'
        )
        
        assert 'compliance_rate' in analysis
        assert 'best_times' in analysis
        assert 'worst_times' in analysis
        assert 'recommendations' in analysis
        assert analysis['compliance_rate'] == 80.0
    
    @pytest.mark.django_db
    def test_get_patient_preferences(self, patient, reminder_pattern):
        """تست دریافت ترجیحات بیمار"""
        service = BehaviorAnalysisService()
        preferences = service.get_patient_preferences(str(patient.id))
        
        assert 'notification_channels' in preferences
        assert 'best_times_by_type' in preferences
        assert 'compliance_by_type' in preferences
        assert preferences['notification_channels']['MEDICATION'] == 'IN_APP'
        assert preferences['compliance_by_type']['MEDICATION'] == 80.0


class TestSmartSchedulerService:
    """تست سرویس زمان‌بندی هوشمند"""
    
    @pytest.mark.django_db
    def test_create_daily_schedules(self, smart_reminder):
        """تست ایجاد برنامه‌های روزانه"""
        service = SmartSchedulerService()
        schedules = service.create_schedules_for_reminder(smart_reminder)
        
        # برای 30 روز و 2 بار در روز = 60 برنامه
        assert len(schedules) == 60
        
        # بررسی زمان‌بندی
        first_schedule = schedules[0]
        assert first_schedule.scheduled_time.date() == smart_reminder.start_date
    
    @pytest.mark.django_db
    def test_create_weekly_schedules(self, patient):
        """تست ایجاد برنامه‌های هفتگی"""
        reminder = SmartReminder.objects.create(
            patient=patient,
            reminder_type='EXERCISE',
            title='ورزش',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=28),
            frequency='WEEKLY',
            days_of_week=[1, 3, 5],  # دوشنبه، چهارشنبه، جمعه
            times_per_day=1
        )
        
        service = SmartSchedulerService()
        schedules = service.create_schedules_for_reminder(reminder)
        
        # بررسی روزهای هفته
        for schedule in schedules:
            assert schedule.scheduled_time.weekday() in [1, 3, 5]
    
    @pytest.mark.django_db
    def test_adaptive_scheduling(self, patient, reminder_pattern):
        """تست زمان‌بندی تطبیقی"""
        reminder = SmartReminder.objects.create(
            patient=patient,
            reminder_type='MEDICATION',
            title='دارو',
            start_date=date.today(),
            frequency='DAILY',
            times_per_day=1,
            is_adaptive=True
        )
        
        service = SmartSchedulerService()
        schedules = service.create_schedules_for_reminder(reminder)
        
        # بررسی استفاده از بهترین زمان‌ها
        first_schedule = schedules[0]
        assert first_schedule.scheduled_time.hour in reminder_pattern.best_response_times


class TestReminderDeliveryService:
    """تست سرویس ارسال یادآوری"""
    
    @pytest.mark.django_db
    def test_process_pending_reminders(self, smart_reminder):
        """تست پردازش یادآورهای در انتظار"""
        # ایجاد یادآوری برای الان
        schedule = ReminderSchedule.objects.create(
            reminder=smart_reminder,
            scheduled_time=timezone.now()
        )
        
        service = ReminderDeliveryService()
        sent_count = service.process_pending_reminders()
        
        assert sent_count == 1
        
        # بررسی ارسال
        schedule.refresh_from_db()
        assert schedule.is_sent is True
        assert schedule.sent_at is not None
    
    @pytest.mark.django_db
    def test_handle_reminder_response(self, smart_reminder):
        """تست ثبت پاسخ به یادآوری"""
        schedule = ReminderSchedule.objects.create(
            reminder=smart_reminder,
            scheduled_time=timezone.now()
        )
        schedule.mark_as_sent()
        
        service = ReminderDeliveryService()
        response = service.handle_reminder_response(
            schedule.id,
            {
                'action_result': 'TAKEN',
                'feedback': 'دارو مصرف شد',
                'satisfaction_score': 5
            }
        )
        
        assert response.response_type == 'IMMEDIATE'
        assert response.action_result == 'TAKEN'
        assert response.satisfaction_score == 5
        
        # بررسی بروزرسانی schedule
        schedule.refresh_from_db()
        assert schedule.is_acknowledged is True


class TestAdaptiveLearningService:
    """تست سرویس یادگیری تطبیقی"""
    
    @pytest.mark.django_db
    def test_optimize_reminder_timing(self, patient, smart_reminder, reminder_pattern):
        """تست بهینه‌سازی زمان‌بندی"""
        # تنظیم نرخ تبعیت پایین
        reminder_pattern.compliance_rate = 40.0
        reminder_pattern.save()
        
        service = AdaptiveLearningService()
        service.optimize_reminder_timing(str(patient.id))
        
        # بررسی بروزرسانی زمان‌های ترجیحی
        smart_reminder.refresh_from_db()
        assert smart_reminder.preferred_times is not None
    
    @pytest.mark.django_db
    def test_generate_insights(self, patient, smart_reminder, reminder_pattern):
        """تست تولید بینش‌ها"""
        # تنظیم نرخ تبعیت پایین
        reminder_pattern.compliance_rate = 30.0
        reminder_pattern.save()
        
        service = AdaptiveLearningService()
        insights = service.generate_insights(str(patient.id))
        
        assert len(insights) > 0
        assert any(i['type'] == 'low_compliance' for i in insights)
    
    @pytest.mark.django_db
    def test_predict_best_time(self, patient):
        """تست پیش‌بینی بهترین زمان"""
        service = AdaptiveLearningService()
        predictions = service.predict_best_time(
            str(patient.id),
            'MEDICATION',
            datetime.now()
        )
        
        assert len(predictions) == 3
        assert all(0 <= hour <= 23 for hour, _ in predictions)
        assert all(0 <= prob <= 1 for _, prob in predictions)


class TestSmartReminderAPI:
    """تست API یادآوری هوشمند"""
    
    @pytest.mark.django_db
    def test_create_reminder(self, api_client, doctor_user, patient):
        """تست ایجاد یادآوری از طریق API"""
        api_client.force_authenticate(user=doctor_user)
        
        data = {
            'patient': str(patient.id),
            'reminder_type': 'MEDICATION',
            'title': 'مصرف انسولین',
            'description': 'تزریق انسولین قبل از غذا',
            'start_date': str(date.today()),
            'frequency': 'DAILY',
            'times_per_day': 3,
            'priority': 9,
            'is_critical': True
        }
        
        response = api_client.post('/api/smart-reminders/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'reminder' in response.data
        assert 'schedules_created' in response.data
    
    @pytest.mark.django_db
    def test_get_reminder_statistics(self, api_client, doctor_user, smart_reminder):
        """تست دریافت آمار یادآوری"""
        api_client.force_authenticate(user=doctor_user)
        
        # ایجاد چند schedule و response
        for i in range(5):
            schedule = ReminderSchedule.objects.create(
                reminder=smart_reminder,
                scheduled_time=timezone.now() - timedelta(hours=i)
            )
            schedule.mark_as_sent()
            if i < 3:  # 3 تا پاسخ داده شده
                schedule.acknowledge(action_taken='COMPLETED')
        
        response = api_client.get(f'/api/smart-reminders/{smart_reminder.id}/statistics/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_schedules'] == 5
        assert response.data['sent_count'] == 5
        assert response.data['acknowledged_count'] == 3
        assert response.data['response_rate'] == 60.0
    
    @pytest.mark.django_db
    def test_pause_resume_reminder(self, api_client, doctor_user, smart_reminder):
        """تست توقف و از سرگیری یادآوری"""
        api_client.force_authenticate(user=doctor_user)
        
        # توقف
        response = api_client.post(f'/api/smart-reminders/{smart_reminder.id}/pause/')
        assert response.status_code == status.HTTP_200_OK
        
        smart_reminder.refresh_from_db()
        assert smart_reminder.status == SmartReminder.Status.PAUSED
        
        # از سرگیری
        response = api_client.post(f'/api/smart-reminders/{smart_reminder.id}/resume/')
        assert response.status_code == status.HTTP_200_OK
        
        smart_reminder.refresh_from_db()
        assert smart_reminder.status == SmartReminder.Status.ACTIVE
    
    @pytest.mark.django_db
    def test_patient_behavior_analysis(self, api_client, doctor_user, patient, reminder_pattern):
        """تست تحلیل رفتار بیمار از طریق API"""
        api_client.force_authenticate(user=doctor_user)
        
        response = api_client.get(
            f'/api/reminder-patterns/patient_analysis/?patient_id={patient.id}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'notification_channels' in response.data
        assert 'best_times_by_type' in response.data
        assert 'compliance_by_type' in response.data
        assert 'insights' in response.data
    
    @pytest.mark.django_db
    def test_acknowledge_schedule(self, api_client, doctor_user, smart_reminder):
        """تست تایید برنامه یادآوری"""
        api_client.force_authenticate(user=doctor_user)
        
        schedule = ReminderSchedule.objects.create(
            reminder=smart_reminder,
            scheduled_time=timezone.now()
        )
        schedule.mark_as_sent()
        
        data = {
            'action_taken': 'COMPLETED',
            'notes': 'دارو به موقع مصرف شد',
            'response_details': {
                'action_result': 'TAKEN',
                'satisfaction_score': 4,
                'device_type': 'mobile'
            }
        }
        
        response = api_client.post(
            f'/api/reminder-schedules/{schedule.id}/acknowledge/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'schedule' in response.data
        assert 'response' in response.data
        
        schedule.refresh_from_db()
        assert schedule.is_acknowledged is True
        assert schedule.action_taken == 'COMPLETED'