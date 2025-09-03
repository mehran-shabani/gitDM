from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from gitdm.models import PatientProfile, DoctorProfile
from laboratory.models import LabResult
from encounters.models import Encounter
from .models import BaselineMetrics, PatternAnalysis, AnomalyDetection, PatternAlert
from .services import (
    BaselineCalculationService,
    AnomalyDetectionService, 
    PatternAnalysisService,
    PatternAlertService
)

User = get_user_model()


class BaselineCalculationServiceTest(TestCase):
    """تست‌های سرویس محاسبه معیارهای پایه"""
    
    def setUp(self):
        # ایجاد کاربر و بیمار تست
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.patient = PatientProfile.objects.create(
            user=self.user,
            full_name='Test Patient',
            date_of_birth=timezone.now().date() - timedelta(days=365*40)
        )
        
        # ایجاد داده‌های آزمایشگاهی تست
        base_time = timezone.now() - timedelta(days=30)
        for i in range(5):
            LabResult.objects.create(
                patient=self.patient,
                loinc='4548-4',  # HbA1c
                value=Decimal(str(7.0 + i * 0.2)),
                unit='%',
                taken_at=base_time + timedelta(days=i*7)
            )
            
            LabResult.objects.create(
                patient=self.patient,
                loinc='2345-7',  # Glucose
                value=Decimal(str(120 + i * 10)),
                unit='mg/dL',
                taken_at=base_time + timedelta(days=i*7)
            )
    
    def test_calculate_baseline_metrics(self):
        """تست محاسبه معیارهای پایه"""
        baseline = BaselineCalculationService.calculate_baseline_metrics(self.patient.id)
        
        self.assertIsNotNone(baseline.avg_hba1c)
        self.assertIsNotNone(baseline.avg_blood_glucose)
        self.assertEqual(baseline.patient, self.patient)
        self.assertGreater(baseline.data_points_count, 0)


class AnomalyDetectionServiceTest(TestCase):
    """تست‌های سرویس تشخیص ناهنجاری"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.patient = PatientProfile.objects.create(
            user=self.user,
            full_name='Anomaly Test Patient',
            date_of_birth=timezone.now().date() - timedelta(days=365*35)
        )
        
        # ایجاد baseline metrics
        BaselineMetrics.objects.create(
            patient=self.patient,
            avg_hba1c=Decimal('7.0'),
            std_hba1c=Decimal('0.5'),
            avg_blood_glucose=Decimal('130.0'),
            std_blood_glucose=Decimal('20.0'),
            data_points_count=10
        )
    
    def test_detect_statistical_anomaly_high_severity(self):
        """تست تشخیص ناهنجاری با شدت بالا"""
        # مقدار خیلی بالای HbA1c (3.5 * std بالاتر از میانگین)
        high_value = Decimal('8.75')  # 7.0 + 3.5 * 0.5
        
        anomaly = AnomalyDetectionService.detect_statistical_anomalies(
            self.patient.id, high_value, 'hba1c'
        )
        
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly.severity_level, AnomalyDetection.SeverityLevel.CRITICAL)
        self.assertEqual(anomaly.anomaly_type, AnomalyDetection.AnomalyType.STATISTICAL_OUTLIER)


class PatternAnalysisAPITest(APITestCase):
    """تست‌های API تحلیل الگو"""
    
    def setUp(self):
        # ایجاد پزشک
        self.doctor_user = User.objects.create_user(
            email='doctor@test.com',
            password='testpass123',
            is_doctor=True
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_license_number='12345',
            role=DoctorProfile.DoctorRole.ENDOCRINOLOGIST
        )
        
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            is_patient=True
        )
        self.patient = PatientProfile.objects.create(
            user=self.patient_user,
            full_name='API Test Patient',
            date_of_birth=timezone.now().date() - timedelta(days=365*45),
            primary_doctor=self.doctor_user
        )
        
        # ایجاد توکن احراز هویت
        refresh = RefreshToken.for_user(self.doctor_user)
        self.access_token = str(refresh.access_token)
    
    def test_pattern_analysis_api_endpoint(self):
        """تست endpoint تحلیل الگو"""
        # ایجاد داده‌های تست
        base_time = timezone.now() - timedelta(days=90)
        for i in range(4):
            LabResult.objects.create(
                patient=self.patient,
                loinc='2345-7',
                value=Decimal(str(120 + i * 5)),
                unit='mg/dL',
                taken_at=base_time + timedelta(days=i*20)
            )
        
        url = '/api/pattern-analyses/analyze/'
        data = {
            'patient_id': self.patient.id,
            'pattern_types': ['GLUCOSE_TREND'],
            'months_back': 6
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')