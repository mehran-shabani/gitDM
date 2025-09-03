from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from gitdm.models import PatientProfile, DoctorProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from .models import MedicalTimeline, TestReminder, ReminderTemplate
from .services import TimelineService, ReminderService

User = get_user_model()


class MedicalTimelineTestCase(TestCase):
    def setUp(self):
        # ایجاد کاربران آزمایشی
        self.doctor_user = User.objects.create_user(
            email='doctor@test.com',
            password='testpass123',
            full_name='دکتر آزمایش',
            is_doctor=True
        )
        
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            full_name='بیمار آزمایش',
            is_patient=True
        )
        
        # ایجاد پروفایل‌ها
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_code='12345',
            specialty='غدد'
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            full_name='بیمار آزمایش',
            national_id='1234567890',
            primary_doctor=self.doctor_user
        )
    
    def test_timeline_creation_from_encounter(self):
        """تست ایجاد رویداد تایم‌لاین از مواجهه"""
        encounter = Encounter.objects.create(
            patient=self.patient_profile,
            occurred_at=timezone.now(),
            subjective='شکایت بیمار',
            created_by=self.doctor_user
        )
        
        timeline_event = TimelineService.create_timeline_event_from_encounter(encounter)
        
        self.assertEqual(timeline_event.patient, self.patient_profile)
        self.assertEqual(timeline_event.event_type, MedicalTimeline.EventType.ENCOUNTER)
        self.assertEqual(timeline_event.content_object, encounter)
    
    def test_timeline_creation_from_lab_result(self):
        """تست ایجاد رویداد تایم‌لاین از نتیجه آزمایش"""
        encounter = Encounter.objects.create(
            patient=self.patient_profile,
            occurred_at=timezone.now(),
            created_by=self.doctor_user
        )
        
        lab_result = LabResult.objects.create(
            patient=self.patient_profile,
            encounter=encounter,
            loinc='4548-4',  # HbA1c
            value=8.5,
            unit='%',
            taken_at=timezone.now()
        )
        
        timeline_event = TimelineService.create_timeline_event_from_lab_result(lab_result)
        
        self.assertEqual(timeline_event.patient, self.patient_profile)
        self.assertEqual(timeline_event.event_type, MedicalTimeline.EventType.LAB_RESULT)
        self.assertEqual(timeline_event.severity, MedicalTimeline.Severity.HIGH)  # HbA1c > 7%


class TestReminderTestCase(TestCase):
    def setUp(self):
        # ایجاد کاربران و پروفایل‌ها (مشابه بالا)
        self.doctor_user = User.objects.create_user(
            email='doctor@test.com',
            password='testpass123',
            full_name='دکتر آزمایش',
            is_doctor=True
        )
        
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            full_name='بیمار آزمایش',
            is_patient=True
        )
        
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_code='12345'
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            full_name='بیمار آزمایش',
            national_id='1234567890',
            primary_doctor=self.doctor_user
        )
    
    def test_reminder_creation(self):
        """تست ایجاد یادآوری آزمایش"""
        reminder = TestReminder.objects.create(
            patient=self.patient_profile,
            test_type='HBA1C',
            frequency='QUARTERLY',
            priority='HIGH',
            next_due=timezone.now() + timedelta(days=90),
            created_by=self.doctor_user
        )
        
        self.assertEqual(reminder.patient, self.patient_profile)
        self.assertEqual(reminder.test_type, 'HBA1C')
        self.assertFalse(reminder.is_overdue())
    
    def test_overdue_reminder(self):
        """تست یادآوری عقب‌افتاده"""
        reminder = TestReminder.objects.create(
            patient=self.patient_profile,
            test_type='FBS',
            frequency='MONTHLY',
            next_due=timezone.now() - timedelta(days=5),  # ۵ روز عقب‌افتاده
            created_by=self.doctor_user
        )
        
        self.assertTrue(reminder.is_overdue())
        self.assertEqual(reminder.days_until_due(), -5)
    
    def test_mark_reminder_completed(self):
        """تست علامت‌گذاری یادآوری به عنوان انجام شده"""
        reminder = TestReminder.objects.create(
            patient=self.patient_profile,
            test_type='HBA1C',
            frequency='QUARTERLY',
            next_due=timezone.now(),
            created_by=self.doctor_user
        )
        
        old_next_due = reminder.next_due
        reminder.mark_as_completed()
        
        self.assertIsNotNone(reminder.last_performed)
        self.assertGreater(reminder.next_due, old_next_due)
    
    def test_default_reminders_creation(self):
        """تست ایجاد یادآورهای پیش‌فرض"""
        reminders = ReminderService.create_default_reminders_for_patient(
            self.patient_profile, 
            self.doctor_user
        )
        
        self.assertGreater(len(reminders), 0)
        
        # بررسی وجود یادآوری HbA1c
        hba1c_reminder = TestReminder.objects.filter(
            patient=self.patient_profile,
            test_type='HBA1C'
        ).first()
        
        self.assertIsNotNone(hba1c_reminder)
        self.assertEqual(hba1c_reminder.frequency, 'QUARTERLY')


class ReminderTemplateTestCase(TestCase):
    def test_template_creation(self):
        """تست ایجاد قالب یادآوری"""
        template = ReminderTemplate.objects.create(
            test_type='HBA1C',
            default_frequency='QUARTERLY',
            default_priority='HIGH',
            default_reminder_days=14,
            instructions='آزمایش HbA1c',
            preparation_notes='ناشتا نیست'
        )
        
        self.assertEqual(template.test_type, 'HBA1C')
        self.assertTrue(template.is_active)


class TimelineVisualizationTestCase(TestCase):
    def setUp(self):
        # ایجاد داده‌های آزمایشی
        self.doctor_user = User.objects.create_user(
            email='doctor@test.com',
            password='testpass123',
            is_doctor=True
        )
        
        self.patient_profile = PatientProfile.objects.create(
            full_name='بیمار آزمایش',
            national_id='1234567890',
            primary_doctor=self.doctor_user
        )
        
        # ایجاد چند رویداد تایم‌لاین
        for i in range(5):
            MedicalTimeline.objects.create(
                patient=self.patient_profile,
                event_type=MedicalTimeline.EventType.ENCOUNTER,
                title=f'ویزیت {i+1}',
                description=f'توضیحات ویزیت {i+1}',
                occurred_at=timezone.now() - timedelta(days=i*30),
                created_by=self.doctor_user
            )
    
    def test_timeline_data_preparation(self):
        """تست آماده‌سازی داده‌ها برای نمودار"""
        from .services import TimelineVisualizationService
        
        chart_data = TimelineVisualizationService.prepare_timeline_chart_data(
            self.patient_profile
        )
        
        self.assertIn('patient', chart_data)
        self.assertIn('timeline_data', chart_data)
        self.assertEqual(len(chart_data['timeline_data']), 5)
    
    def test_patient_timeline_view_access(self):
        """تست دسترسی به صفحه تایم‌لاین"""
        self.client.force_login(self.doctor_user)
        
        response = self.client.get(f'/patient/{self.patient_profile.id}/timeline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تایم‌لاین پزشکی')
    
    def test_unauthorized_access(self):
        """تست دسترسی غیرمجاز"""
        other_doctor = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            is_doctor=True
        )
        
        self.client.force_login(other_doctor)
        
        response = self.client.get(f'/patient/{self.patient_profile.id}/timeline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'دسترسی غیرمجاز')