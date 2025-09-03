from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from gitdm.models import PatientProfile, DoctorProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from timeline.models import MedicalTimeline, TestReminder
from timeline.services import TimelineService, ReminderService
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'تست یکپارچگی سیستم تایم‌لاین با سایر بخش‌های GitDM'
    
    def handle(self, *args, **options):
        self.stdout.write('شروع تست یکپارچگی سیستم تایم‌لاین...')
        
        # ایجاد داده‌های آزمایشی
        doctor_user = self.create_test_doctor()
        patient_profile = self.create_test_patient(doctor_user)
        
        # تست ۱: ایجاد خودکار تایم‌لاین از مواجهه
        self.test_encounter_timeline_creation(patient_profile, doctor_user)
        
        # تست ۲: ایجاد خودکار تایم‌لاین از نتیجه آزمایش
        self.test_lab_result_timeline_creation(patient_profile, doctor_user)
        
        # تست ۳: سیستم یادآورها
        self.test_reminder_system(patient_profile, doctor_user)
        
        # تست ۴: اطلاع‌رسانی‌ها
        self.test_notification_integration(patient_profile, doctor_user)
        
        # تست ۵: API endpoints
        self.test_api_endpoints(patient_profile)
        
        # پاک‌سازی
        self.cleanup_test_data(doctor_user, patient_profile)
        
        self.stdout.write(
            self.style.SUCCESS('تست یکپارچگی با موفقیت تکمیل شد ✅')
        )
    
    def create_test_doctor(self):
        """ایجاد پزشک آزمایشی"""
        doctor_user, created = User.objects.get_or_create(
            email='test.doctor@timeline.test',
            defaults={
                'full_name': 'دکتر تست',
                'is_doctor': True,
                'password': 'pbkdf2_sha256$320000$test$test'
            }
        )
        
        if created:
            DoctorProfile.objects.create(
                user=doctor_user,
                medical_code='TEST123',
                specialty='غدد'
            )
            self.stdout.write('✅ پزشک آزمایشی ایجاد شد')
        
        return doctor_user
    
    def create_test_patient(self, doctor_user):
        """ایجاد بیمار آزمایشی"""
        patient_user, created = User.objects.get_or_create(
            email='test.patient@timeline.test',
            defaults={
                'full_name': 'بیمار تست',
                'is_patient': True,
                'password': 'pbkdf2_sha256$320000$test$test'
            }
        )
        
        patient_profile, created = PatientProfile.objects.get_or_create(
            user=patient_user,
            defaults={
                'full_name': 'بیمار تست تایم‌لاین',
                'national_id': '9876543210',
                'dob': timezone.now().date() - timedelta(days=365*40),
                'sex': 'MALE',
                'primary_doctor': doctor_user
            }
        )
        
        if created:
            self.stdout.write('✅ بیمار آزمایشی ایجاد شد')
        
        return patient_profile
    
    def test_encounter_timeline_creation(self, patient_profile, doctor_user):
        """تست ایجاد تایم‌لاین از مواجهه"""
        self.stdout.write('📋 تست ایجاد تایم‌لاین از مواجهه...')
        
        encounter = Encounter.objects.create(
            patient=patient_profile,
            occurred_at=timezone.now() - timedelta(days=1),
            subjective='تست شکایت بیمار',
            assessment={'diagnosis': 'تست تشخیص'},
            plan={'medication': 'تست دارو'},
            created_by=doctor_user
        )
        
        # بررسی ایجاد خودکار رویداد تایم‌لاین
        timeline_event = MedicalTimeline.objects.filter(
            patient=patient_profile,
            event_type=MedicalTimeline.EventType.ENCOUNTER,
            content_type__model='encounter',
            object_id=encounter.id
        ).first()
        
        if timeline_event:
            self.stdout.write('✅ رویداد تایم‌لاین از مواجهه ایجاد شد')
        else:
            self.stdout.write('❌ خطا: رویداد تایم‌لاین از مواجهه ایجاد نشد')
    
    def test_lab_result_timeline_creation(self, patient_profile, doctor_user):
        """تست ایجاد تایم‌لاین از نتیجه آزمایش"""
        self.stdout.write('🧪 تست ایجاد تایم‌لاین از نتیجه آزمایش...')
        
        encounter = Encounter.objects.create(
            patient=patient_profile,
            occurred_at=timezone.now(),
            created_by=doctor_user
        )
        
        lab_result = LabResult.objects.create(
            patient=patient_profile,
            encounter=encounter,
            loinc='4548-4',  # HbA1c
            value=8.5,
            unit='%',
            taken_at=timezone.now()
        )
        
        # بررسی ایجاد خودکار رویداد تایم‌لاین
        timeline_event = MedicalTimeline.objects.filter(
            patient=patient_profile,
            event_type=MedicalTimeline.EventType.LAB_RESULT,
            content_type__model='labresult',
            object_id=lab_result.id
        ).first()
        
        if timeline_event:
            self.stdout.write('✅ رویداد تایم‌لاین از نتیجه آزمایش ایجاد شد')
            if timeline_event.severity == MedicalTimeline.Severity.HIGH:
                self.stdout.write('✅ شدت رویداد به درستی تشخیص داده شد (HIGH برای HbA1c > 7%)')
        else:
            self.stdout.write('❌ خطا: رویداد تایم‌لاین از نتیجه آزمایش ایجاد نشد')
    
    def test_reminder_system(self, patient_profile, doctor_user):
        """تست سیستم یادآورها"""
        self.stdout.write('🔔 تست سیستم یادآورها...')
        
        # ایجاد یادآورهای پیش‌فرض
        reminders = ReminderService.create_default_reminders_for_patient(
            patient_profile, 
            doctor_user
        )
        
        if reminders:
            self.stdout.write(f'✅ {len(reminders)} یادآوری پیش‌فرض ایجاد شد')
        
        # تست یادآوری عقب‌افتاده
        overdue_reminder = TestReminder.objects.create(
            patient=patient_profile,
            test_type='FBS',
            frequency='MONTHLY',
            next_due=timezone.now() - timedelta(days=5),
            created_by=doctor_user
        )
        
        if overdue_reminder.is_overdue():
            self.stdout.write('✅ تشخیص یادآوری عقب‌افتاده عمل می‌کند')
        
        # تست علامت‌گذاری انجام شده
        overdue_reminder.mark_as_completed()
        if overdue_reminder.last_performed and overdue_reminder.next_due > timezone.now():
            self.stdout.write('✅ علامت‌گذاری انجام شده عمل می‌کند')
    
    def test_notification_integration(self, patient_profile, doctor_user):
        """تست یکپارچگی با سیستم اطلاع‌رسانی"""
        self.stdout.write('📨 تست یکپارچگی اطلاع‌رسانی...')
        
        # ایجاد یادآوری عقب‌افتاده
        reminder = TestReminder.objects.create(
            patient=patient_profile,
            test_type='HBA1C',
            frequency='QUARTERLY',
            next_due=timezone.now() - timedelta(days=10),
            created_by=doctor_user
        )
        
        # ارسال یادآورها
        notifications_sent = ReminderService.send_reminder_notifications()
        
        # بررسی ایجاد notification
        notification = Notification.objects.filter(
            recipient=doctor_user,
            resource_type='test_reminder',
            resource_id=str(reminder.id)
        ).first()
        
        if notification:
            self.stdout.write('✅ اطلاع‌رسانی یادآوری ایجاد شد')
        else:
            self.stdout.write('❌ خطا: اطلاع‌رسانی یادآوری ایجاد نشد')
    
    def test_api_endpoints(self, patient_profile):
        """تست API endpoints"""
        self.stdout.write('🌐 تست API endpoints...')
        
        from django.test import Client
        
        client = Client()
        
        # لاگین با پزشک
        client.force_login(patient_profile.primary_doctor)
        
        # تست API تایم‌لاین
        response = client.get(f'/timeline/api/timeline/patient_timeline/?patient_id={patient_profile.id}')
        if response.status_code == 200:
            self.stdout.write('✅ API تایم‌لاین بیمار عمل می‌کند')
        else:
            self.stdout.write(f'❌ خطا در API تایم‌لاین: {response.status_code}')
        
        # تست API یادآورها
        response = client.get(f'/timeline/api/reminders/patient_reminders/?patient_id={patient_profile.id}')
        if response.status_code == 200:
            self.stdout.write('✅ API یادآورهای بیمار عمل می‌کند')
        else:
            self.stdout.write(f'❌ خطا در API یادآورها: {response.status_code}')
        
        # تست صفحه تایم‌لاین
        response = client.get(f'/timeline/patient/{patient_profile.id}/timeline/')
        if response.status_code == 200:
            self.stdout.write('✅ صفحه تایم‌لاین بیمار عمل می‌کند')
        else:
            self.stdout.write(f'❌ خطا در صفحه تایم‌لاین: {response.status_code}')
    
    def cleanup_test_data(self, doctor_user, patient_profile):
        """پاک‌سازی داده‌های آزمایشی"""
        self.stdout.write('🧹 پاک‌سازی داده‌های آزمایشی...')
        
        # حذف رویدادهای تایم‌لاین
        MedicalTimeline.objects.filter(patient=patient_profile).delete()
        
        # حذف یادآورها
        TestReminder.objects.filter(patient=patient_profile).delete()
        
        # حذف اطلاع‌رسانی‌ها
        Notification.objects.filter(recipient=doctor_user).delete()
        
        # حذف مواجهات و آزمایشات
        Encounter.objects.filter(patient=patient_profile).delete()
        LabResult.objects.filter(patient=patient_profile).delete()
        
        # حذف بیمار و پزشک
        patient_profile.delete()
        if hasattr(doctor_user, 'doctor_profile'):
            doctor_user.doctor_profile.delete()
        doctor_user.delete()
        
        self.stdout.write('✅ پاک‌سازی تکمیل شد')