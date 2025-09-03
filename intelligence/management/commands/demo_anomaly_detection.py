from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from gitdm.models import PatientProfile, DoctorProfile
from laboratory.models import LabResult
from encounters.models import Encounter
from pharmacy.models import Medication
from intelligence.services import (
    BaselineCalculationService,
    AnomalyDetectionService,
    PatternAnalysisService,
    PatternAlertService
)

User = get_user_model()


class Command(BaseCommand):
    help = 'ایجاد داده‌های نمونه برای تست سیستم تشخیص ناهنجاری'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=3,
            help='تعداد بیماران نمونه برای ایجاد'
        )

    def handle(self, *args, **options):
        patients_count = options['patients']
        
        self.stdout.write(
            self.style.SUCCESS(f'شروع ایجاد {patients_count} بیمار نمونه...')
        )

        # ایجاد پزشک نمونه
        doctor_user, created = User.objects.get_or_create(
            email='demo_doctor@example.com',
            defaults={
                'full_name': 'دکتر نمونه',
                'is_doctor': True,
                'password': 'demo123'
            }
        )
        
        if created:
            doctor_user.set_password('demo123')
            doctor_user.save()

        doctor_profile, _ = DoctorProfile.objects.get_or_create(
            user=doctor_user,
            defaults={
                'medical_license_number': 'DEMO123',
                'role': DoctorProfile.DoctorRole.ENDOCRINOLOGIST
            }
        )

        for i in range(patients_count):
            # ایجاد بیمار نمونه
            patient_user = User.objects.create_user(
                email=f'demo_patient_{i+1}@example.com',
                password='demo123',
                full_name=f'بیمار نمونه {i+1}',
                is_patient=True
            )

            patient = PatientProfile.objects.create(
                user=patient_user,
                full_name=f'بیمار نمونه {i+1}',
                date_of_birth=timezone.now().date() - timedelta(days=365*(30+i*10)),
                primary_doctor=doctor_user
            )

            # ایجاد داده‌های تاریخی
            self._create_historical_data(patient, i)
            
            # محاسبه baseline
            baseline = BaselineCalculationService.calculate_baseline_metrics(patient.id)
            self.stdout.write(f'  ✓ Baseline محاسبه شد برای {patient.full_name}')
            
            # تحلیل الگوها
            glucose_analysis = PatternAnalysisService.analyze_glucose_trend(patient.id)
            if glucose_analysis:
                self.stdout.write(f'  ✓ تحلیل روند قند خون: {glucose_analysis.trend_direction}')
                
                # ایجاد هشدار در صورت نیاز
                if glucose_analysis.trend_direction == 'WORSENING':
                    alert = PatternAlertService.create_deterioration_alert(patient.id, glucose_analysis)
                    if alert:
                        self.stdout.write(f'  ⚠️  هشدار ایجاد شد: {alert.title}')

            # تست تشخیص ناهنجاری
            if i == 0:  # فقط برای بیمار اول
                self._create_anomaly_example(patient)

        self.stdout.write(
            self.style.SUCCESS(f'✅ {patients_count} بیمار نمونه با موفقیت ایجاد شدند')
        )
        
        self.stdout.write('\n📊 برای مشاهده نتایج:')
        self.stdout.write('  - پنل ادمین: /admin/')
        self.stdout.write('  - API: /api/pattern-analyses/')
        self.stdout.write('  - هشدارها: /api/pattern-alerts/')

    def _create_historical_data(self, patient, patient_index):
        """ایجاد داده‌های تاریخی برای بیمار"""
        base_time = timezone.now() - timedelta(days=180)
        
        # الگوهای مختلف برای بیماران مختلف
        if patient_index == 0:
            # بیمار با روند بدتر شدن
            hba1c_base = 6.5
            glucose_base = 120
            trend = 'worsening'
        elif patient_index == 1:
            # بیمار با روند بهبود
            hba1c_base = 8.5
            glucose_base = 180
            trend = 'improving'
        else:
            # بیمار پایدار
            hba1c_base = 7.0
            glucose_base = 140
            trend = 'stable'

        # ایجاد نتایج آزمایش
        for week in range(24):  # 6 ماه داده
            week_time = base_time + timedelta(weeks=week)
            
            # HbA1c (ماهانه)
            if week % 4 == 0:
                if trend == 'worsening':
                    hba1c_value = hba1c_base + (week/4) * 0.2 + random.uniform(-0.1, 0.1)
                elif trend == 'improving':
                    hba1c_value = hba1c_base - (week/4) * 0.15 + random.uniform(-0.1, 0.1)
                else:
                    hba1c_value = hba1c_base + random.uniform(-0.3, 0.3)
                
                LabResult.objects.create(
                    patient=patient,
                    loinc='4548-4',
                    value=Decimal(str(round(max(4.0, hba1c_value), 1))),
                    unit='%',
                    taken_at=week_time
                )

            # قند خون (هفتگی)
            if trend == 'worsening':
                glucose_value = glucose_base + week * 3 + random.uniform(-15, 15)
            elif trend == 'improving':
                glucose_value = glucose_base - week * 2 + random.uniform(-10, 10)
            else:
                glucose_value = glucose_base + random.uniform(-20, 20)
            
            LabResult.objects.create(
                patient=patient,
                loinc='2345-7',
                value=Decimal(str(round(max(50, glucose_value), 0))),
                unit='mg/dL',
                taken_at=week_time
            )

        # ایجاد مواجهه‌ها
        encounter_frequency = 2 if patient_index != 1 else 5  # بیمار 2 کم ویزیت می‌کند
        for month in range(6):
            if random.random() < (encounter_frequency / 6):
                Encounter.objects.create(
                    patient=patient,
                    occurred_at=base_time + timedelta(days=month*30),
                    subjective=f'ویزیت ماه {month+1}',
                    objective={'vital_signs': 'stable'},
                    assessment={'diabetes_control': 'ongoing'},
                    plan={'follow_up': '1 month'},
                    created_by=patient.primary_doctor
                )

        # ایجاد داروها
        Medication.objects.create(
            patient=patient,
            medication_name='Metformin',
            dosage='1000mg',
            frequency='BID',
            created_at=base_time
        )

    def _create_anomaly_example(self, patient):
        """ایجاد مثال ناهنجاری برای تست"""
        # ایجاد مقدار غیرطبیعی قند خون
        LabResult.objects.create(
            patient=patient,
            loinc='2345-7',
            value=Decimal('350'),  # مقدار خیلی بالا
            unit='mg/dL',
            taken_at=timezone.now()
        )
        
        self.stdout.write(f'  🔍 مقدار ناهنجار ایجاد شد برای تست تشخیص')