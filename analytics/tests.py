from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from encounters.models import Encounter
from laboratory.models import LabResult
from gitdm.models import PatientProfile as Patient
from gitdm.models import DoctorProfile
from .models import PatientAnalytics, DoctorAnalytics, SystemAnalytics, Report
from .services import PatientAnalyticsService, DoctorAnalyticsService, SystemAnalyticsService

User = get_user_model()


class PatientAnalyticsServiceTest(TestCase):
    """تست‌های سرویس آنالیتیکس بیماران"""
    
    def setUp(self):
        # ایجاد کاربر و پزشک
        self.user = User.objects.create_user(email='doctor1@example.com', password='testpass123')
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            medical_code='12345',
            specialty='ENDOCRINOLOGIST'
        )
        
        # ایجاد بیمار
        self.patient = Patient.objects.create(full_name='بیمار تست', national_id='1234567890', primary_doctor=self.doctor)
        
        self.service = PatientAnalyticsService()
    
    def test_calculate_patient_analytics(self):
        """تست محاسبه آنالیتیکس بیمار"""
        # ایجاد داده‌های تست
        # آزمایش قند خون
        LabResult.objects.create(patient=self.patient, loinc='2345-7', value='120', unit='mg/dL', taken_at=timezone.now())
        
        # آزمایش HbA1c
        LabResult.objects.create(patient=self.patient, loinc='4548-4', value='6.5', unit='%', taken_at=timezone.now())
        
        # محاسبه آنالیتیکس
        analytics = self.service.calculate_patient_analytics(self.patient)
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.patient, self.patient)
        self.assertEqual(analytics.avg_glucose, 120.0)
        self.assertEqual(analytics.avg_hba1c, 6.5)
        self.assertEqual(analytics.lab_tests_count, 2)
    
    def test_glucose_trend_calculation(self):
        """تست محاسبه روند قند خون"""
        # ایجاد آزمایش‌های قبلی و فعلی
        past_date = timezone.now().date() - timedelta(days=45)
        current_date = timezone.now().date()
        
        # آزمایش قبلی
        LabResult.objects.create(patient=self.patient, loinc='2345-7', value='150', unit='mg/dL', taken_at=past_date)
        
        # آزمایش فعلی
        LabResult.objects.create(patient=self.patient, loinc='2345-7', value='120', unit='mg/dL', taken_at=current_date)
        
        analytics = self.service.calculate_patient_analytics(self.patient)
        
        # روند باید بهبود باشد چون قند خون کاهش یافته
        self.assertEqual(analytics.glucose_trend, 'improving')
    
    def test_compliance_score_calculation(self):
        """تست محاسبه امتیاز پایبندی"""
        # ایجاد ویزیت
        Encounter.objects.create(patient=self.patient, created_by=self.user, occurred_at=timezone.now())
        
        analytics = self.service.calculate_patient_analytics(self.patient)
        
        # با یک ویزیت در ماه، امتیاز پایبندی باید بالا باشد
        self.assertGreater(analytics.compliance_score, 70)


class DoctorAnalyticsServiceTest(TestCase):
    """تست‌های سرویس آنالیتیکس پزشکان"""
    
    def setUp(self):
        self.service = DoctorAnalyticsService()
        
        # ایجاد پزشک
        self.user = User.objects.create_user(email='doctor1@example.com', password='testpass123')
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            medical_code='12345'
        )
        
        # ایجاد چند بیمار
        for i in range(5):
            patient = Patient.objects.create(full_name=f'بیمار{i} تست', national_id=f'123456789{i}', primary_doctor=self.doctor)
            
            # ایجاد ویزیت برای بیماران فعال
            if i < 3:
                Encounter.objects.create(patient=patient, created_by=self.user, occurred_at=timezone.now())
    
    def test_calculate_doctor_analytics(self):
        """تست محاسبه آنالیتیکس پزشک"""
        analytics = self.service.calculate_doctor_analytics(self.doctor)
        
        self.assertEqual(analytics.total_patients, 5)
        self.assertEqual(analytics.active_patients, 3)
        self.assertEqual(analytics.total_encounters, 3)
        self.assertGreater(analytics.performance_score, 0)


class SystemAnalyticsServiceTest(TestCase):
    """تست‌های سرویس آنالیتیکس سیستم"""
    
    def setUp(self):
        self.service = SystemAnalyticsService()
        
        # ایجاد داده‌های تست
        for i in range(3):
            user = User.objects.create_user(email=f'doctor{i}@example.com', password='testpass123')
            DoctorProfile.objects.create(
                user=user,
                medical_code=f'1234{i}'
            )
        
        for i in range(10):
            Patient.objects.create(full_name=f'بیمار{i} تست', national_id=f'123456789{i}')
    
    def test_calculate_system_analytics(self):
        """تست محاسبه آنالیتیکس سیستم"""
        analytics = self.service.calculate_system_analytics()
        
        self.assertEqual(analytics.total_doctors, 3)
        self.assertEqual(analytics.total_patients, 10)
        self.assertEqual(analytics.total_users, 3)  # فقط پزشکان کاربر دارند


class AnalyticsAPITest(APITestCase):
    """تست‌های API آنالیتیکس"""
    
    def setUp(self):
        # ایجاد پزشک
        self.user = User.objects.create_user(email='doctor1@example.com', password='testpass123')
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            medical_code='12345'
        )
        
        # ایجاد بیمار
        self.patient = Patient.objects.create(full_name='بیمار تست', national_id='1234567890', primary_doctor=self.doctor)
        
        self.client.force_authenticate(user=self.user)
    
    def test_calculate_patient_analytics_api(self):
        """تست API محاسبه آنالیتیکس بیمار"""
        response = self.client.post('/api/analytics/patient-analytics/calculate/', {
            'patient_id': self.patient.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['patient'], self.patient.id)
    
    def test_dashboard_summary_api(self):
        """تست API خلاصه داشبورد"""
        response = self.client.get('/api/analytics/dashboard/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_patients', response.data)
        self.assertIn('active_patients', response.data)
    
    def test_create_report_api(self):
        """تست API ایجاد گزارش"""
        response = self.client.post('/api/analytics/reports/', {
            'report_type': 'patient_summary',
            'format': 'pdf',
            'patient_id': self.patient.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['report_type'], 'patient_summary')
        self.assertEqual(response.data['requested_by'], self.user.id)
    
    def test_unauthorized_access(self):
        """تست دسترسی غیرمجاز"""
        # ایجاد پزشک دیگر
        other_user = User.objects.create_user(email='doctor2@example.com', password='testpass123')
        other_doctor = DoctorProfile.objects.create(
            user=other_user,
            medical_code='54321'
        )
        
        # ایجاد بیمار برای پزشک دیگر
        other_patient = Patient.objects.create(full_name='بیمار دیگر', national_id='0987654321', primary_doctor=other_doctor)
        
        # تلاش برای دسترسی به بیمار پزشک دیگر
        response = self.client.post('/api/analytics/patient-analytics/calculate/', {
            'patient_id': other_patient.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)