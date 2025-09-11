from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from gitdm.models import PatientProfile, DoctorProfile
from encounters.models import Encounter
from laboratory.models import LabResult
from timeline.models import MedicalTimeline, TestReminder
from timeline.services import ReminderService

User = get_user_model()


class Command(BaseCommand):
    help = 'ایجاد داده‌های نمونه برای تایم‌لاین پزشکی'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--patient-id',
            type=int,
            help='شناسه بیمار برای ایجاد داده‌های نمونه',
        )
    
    def handle(self, *args, **options):
        patient_id = options.get('patient_id')
        
        if patient_id:
            try:
                patient = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'بیمار با شناسه {patient_id} یافت نشد')
                )
                return
        else:
            # ایجاد بیمار نمونه
            doctor_user, _ = User.objects.get_or_create(
                email='sample.doctor@test.com',
                defaults={
                    'full_name': 'دکتر نمونه',
                    'is_doctor': True,
                    'password': 'pbkdf2_sha256$320000$test$test'
                }
            )
            
            patient_user, _ = User.objects.get_or_create(
                email='sample.patient@test.com',
                defaults={
                    'full_name': 'بیمار نمونه',
                    'is_patient': True,
                    'password': 'pbkdf2_sha256$320000$test$test'
                }
            )
            
            doctor_profile, _ = DoctorProfile.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'medical_code': '98765',
                    'specialty': 'غدد درون‌ریز'
                }
            )
            
            patient, _ = PatientProfile.objects.get_or_create(
                user=patient_user,
                defaults={
                    'full_name': 'بیمار نمونه',
                    'national_id': '1234567890',
                    'dob': timezone.now().date() - timedelta(days=365*45),  # ۴۵ ساله
                    'sex': 'MALE',
                    'primary_doctor': doctor_user
                }
            )
        
        self.create_sample_encounters(patient)
        self.create_sample_lab_results(patient)
        self.create_sample_reminders(patient)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'داده‌های نمونه برای بیمار {patient.full_name} ایجاد شد'
            )
        )
    
    def create_sample_encounters(self, patient):
        """ایجاد مواجهات نمونه"""
        encounters_data = [
            {
                'subjective': 'بیمار از خستگی و تشنگی زیاد شکایت دارد',
                'assessment': {'diagnosis': 'دیابت نوع ۲', 'severity': 'متوسط'},
                'plan': {'medication': 'متفورمین', 'lifestyle': 'رژیم غذایی'},
                'days_ago': 90
            },
            {
                'subjective': 'کنترل قند خون، وضعیت بهتر',
                'assessment': {'diagnosis': 'دیابت تحت کنترل', 'severity': 'خفیف'},
                'plan': {'continue': 'ادامه درمان فعلی'},
                'days_ago': 60
            },
            {
                'subjective': 'گزارش کاهش وزن ۳ کیلوگرم',
                'assessment': {'weight_loss': '3kg', 'compliance': 'خوب'},
                'plan': {'diet': 'ادامه رژیم', 'exercise': 'افزایش فعالیت'},
                'days_ago': 30
            }
        ]
        
        for encounter_data in encounters_data:
            Encounter.objects.get_or_create(
                patient=patient,
                occurred_at=timezone.now() - timedelta(days=encounter_data['days_ago']),
                defaults={
                    'subjective': encounter_data['subjective'],
                    'assessment': encounter_data['assessment'],
                    'plan': encounter_data['plan'],
                    'created_by': patient.primary_doctor
                }
            )
    
    def create_sample_lab_results(self, patient):
        """ایجاد نتایج آزمایش نمونه"""
        lab_data = [
            {'loinc': '4548-4', 'value': 8.2, 'unit': '%', 'days_ago': 85},  # HbA1c
            {'loinc': '2345-7', 'value': 145, 'unit': 'mg/dL', 'days_ago': 80},  # FBS
            {'loinc': '4548-4', 'value': 7.8, 'unit': '%', 'days_ago': 55},  # HbA1c
            {'loinc': '2345-7', 'value': 125, 'unit': 'mg/dL', 'days_ago': 50},  # FBS
            {'loinc': '4548-4', 'value': 7.1, 'unit': '%', 'days_ago': 25},  # HbA1c
            {'loinc': '2345-7', 'value': 110, 'unit': 'mg/dL', 'days_ago': 20},  # FBS
        ]
        
        for lab in lab_data:
            LabResult.objects.get_or_create(
                patient=patient,
                loinc=lab['loinc'],
                taken_at=timezone.now() - timedelta(days=lab['days_ago']),
                defaults={
                    'value': lab['value'],
                    'unit': lab['unit']
                }
            )
    
    def create_sample_reminders(self, patient):
        """ایجاد یادآورهای نمونه"""
        ReminderService.create_default_reminders_for_patient(
            patient, 
            patient.primary_doctor
        )