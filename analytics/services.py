import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from django.db.models import Avg, Count, Sum, Q, F, Max, Min, StdDev
from django.utils import timezone
from django.core.cache import cache

from encounters.models import Patient, Encounter
from laboratory.models import LabTest, LabResult
from pharmacy.models import Medication
from notifications.models import ClinicalAlert
from security.models import DoctorProfile
from .models import PatientAnalytics, DoctorAnalytics, SystemAnalytics


class AnalyticsService:
    """سرویس اصلی برای تحلیل داده‌ها"""
    
    @staticmethod
    def calculate_trend(current_value: float, previous_value: float, threshold: float = 5.0) -> str:
        """محاسبه روند بر اساس مقایسه مقادیر"""
        if not previous_value:
            return 'stable'
        
        change_percentage = ((current_value - previous_value) / previous_value) * 100
        
        if change_percentage > threshold:
            return 'worsening'
        elif change_percentage < -threshold:
            return 'improving'
        else:
            return 'stable'
    
    @staticmethod
    def get_date_range(period: str = 'month') -> Tuple[date, date]:
        """بازگرداندن بازه تاریخی بر اساس دوره"""
        end_date = timezone.now().date()
        
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date


class PatientAnalyticsService:
    """سرویس تحلیل داده‌های بیماران"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def calculate_patient_analytics(self, patient: Patient, target_date: Optional[date] = None) -> PatientAnalytics:
        """محاسبه آمارهای یک بیمار برای تاریخ مشخص"""
        if not target_date:
            target_date = timezone.now().date()
        
        # بازه 30 روزه برای محاسبات
        end_date = target_date
        start_date = end_date - timedelta(days=30)
        
        # دریافت یا ایجاد رکورد آنالیتیکس
        analytics, created = PatientAnalytics.objects.get_or_create(
            patient=patient,
            date=target_date
        )
        
        # محاسبه آمارهای قند خون
        glucose_results = LabResult.objects.filter(
            test__patient=patient,
            test__test_type__in=['FBS', 'RBS', 'PPBS'],
            test__test_date__range=[start_date, end_date]
        ).values_list('value', flat=True)
        
        if glucose_results:
            glucose_values = [float(v) for v in glucose_results if v]
            analytics.avg_glucose = np.mean(glucose_values)
            analytics.min_glucose = np.min(glucose_values)
            analytics.max_glucose = np.max(glucose_values)
            analytics.glucose_std_dev = np.std(glucose_values)
            
            # محاسبه روند قند خون
            previous_period_glucose = LabResult.objects.filter(
                test__patient=patient,
                test__test_type__in=['FBS', 'RBS', 'PPBS'],
                test__test_date__range=[start_date - timedelta(days=30), start_date]
            ).aggregate(avg=Avg('value'))['avg']
            
            if previous_period_glucose:
                analytics.glucose_trend = self.analytics_service.calculate_trend(
                    analytics.avg_glucose,
                    float(previous_period_glucose)
                )
        
        # محاسبه آمارهای HbA1c
        hba1c_results = LabResult.objects.filter(
            test__patient=patient,
            test__test_type='HBA1C',
            test__test_date__range=[start_date - timedelta(days=90), end_date]
        ).values_list('value', flat=True)
        
        if hba1c_results:
            hba1c_values = [float(v) for v in hba1c_results if v]
            analytics.avg_hba1c = np.mean(hba1c_values)
            
            # محاسبه روند HbA1c
            previous_hba1c = LabResult.objects.filter(
                test__patient=patient,
                test__test_type='HBA1C',
                test__test_date__range=[start_date - timedelta(days=180), start_date - timedelta(days=90)]
            ).aggregate(avg=Avg('value'))['avg']
            
            if previous_hba1c:
                analytics.hba1c_trend = self.analytics_service.calculate_trend(
                    analytics.avg_hba1c,
                    float(previous_hba1c),
                    threshold=3.0  # آستانه کمتر برای HbA1c
                )
        
        # محاسبه آمارهای فشار خون
        bp_encounters = Encounter.objects.filter(
            patient=patient,
            encounter_date__range=[start_date, end_date]
        ).exclude(
            vital_signs__systolic_bp__isnull=True
        ).values('vital_signs__systolic_bp', 'vital_signs__diastolic_bp')
        
        if bp_encounters:
            systolic_values = [e['vital_signs__systolic_bp'] for e in bp_encounters if e['vital_signs__systolic_bp']]
            diastolic_values = [e['vital_signs__diastolic_bp'] for e in bp_encounters if e['vital_signs__diastolic_bp']]
            
            if systolic_values:
                analytics.avg_systolic = int(np.mean(systolic_values))
            if diastolic_values:
                analytics.avg_diastolic = int(np.mean(diastolic_values))
        
        # شمارش‌ها
        analytics.encounters_count = Encounter.objects.filter(
            patient=patient,
            encounter_date__range=[start_date, end_date]
        ).count()
        
        analytics.medications_count = Medication.objects.filter(
            patient=patient,
            prescribed_date__range=[start_date, end_date]
        ).count()
        
        analytics.lab_tests_count = LabTest.objects.filter(
            patient=patient,
            test_date__range=[start_date, end_date]
        ).count()
        
        analytics.alerts_count = ClinicalAlert.objects.filter(
            patient=patient,
            created_at__date__range=[start_date, end_date]
        ).count()
        
        # محاسبه امتیاز پایبندی به درمان
        analytics.compliance_score = self._calculate_compliance_score(patient, start_date, end_date)
        
        analytics.save()
        return analytics
    
    def _calculate_compliance_score(self, patient: Patient, start_date: date, end_date: date) -> float:
        """محاسبه امتیاز پایبندی به درمان"""
        score = 100.0
        
        # کاهش امتیاز برای ویزیت‌های از دست رفته
        expected_encounters = 1  # حداقل یک ویزیت در ماه
        actual_encounters = Encounter.objects.filter(
            patient=patient,
            encounter_date__range=[start_date, end_date]
        ).count()
        
        if actual_encounters < expected_encounters:
            score -= 20
        
        # کاهش امتیاز برای آزمایش‌های انجام نشده
        # فرض: حداقل یک آزمایش HbA1c در 3 ماه
        last_hba1c = LabTest.objects.filter(
            patient=patient,
            test_type='HBA1C'
        ).order_by('-test_date').first()
        
        if last_hba1c:
            days_since_last_hba1c = (timezone.now().date() - last_hba1c.test_date).days
            if days_since_last_hba1c > 90:
                score -= 15
        else:
            score -= 30
        
        # کاهش امتیاز برای هشدارهای بدون پاسخ
        unacknowledged_alerts = ClinicalAlert.objects.filter(
            patient=patient,
            is_acknowledged=False,
            created_at__date__range=[start_date, end_date]
        ).count()
        
        score -= min(unacknowledged_alerts * 5, 20)
        
        return max(0, score)
    
    def get_glucose_chart_data(self, patient: Patient, period: str = 'month') -> Dict:
        """داده‌های نمودار قند خون"""
        start_date, end_date = self.analytics_service.get_date_range(period)
        
        results = LabResult.objects.filter(
            test__patient=patient,
            test__test_type__in=['FBS', 'RBS', 'PPBS'],
            test__test_date__range=[start_date, end_date]
        ).select_related('test').order_by('test__test_date')
        
        labels = []
        fbs_data = []
        rbs_data = []
        ppbs_data = []
        
        for result in results:
            date_str = result.test.test_date.strftime('%Y-%m-%d')
            if date_str not in labels:
                labels.append(date_str)
            
            value = float(result.value) if result.value else 0
            
            if result.test.test_type == 'FBS':
                fbs_data.append({'x': date_str, 'y': value})
            elif result.test.test_type == 'RBS':
                rbs_data.append({'x': date_str, 'y': value})
            elif result.test.test_type == 'PPBS':
                ppbs_data.append({'x': date_str, 'y': value})
        
        return {
            'labels': sorted(labels),
            'datasets': [
                {
                    'label': 'قند خون ناشتا (FBS)',
                    'data': fbs_data,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.1)',
                    'tension': 0.1
                },
                {
                    'label': 'قند خون رندوم (RBS)',
                    'data': rbs_data,
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'tension': 0.1
                },
                {
                    'label': 'قند خون 2 ساعت بعد غذا (PPBS)',
                    'data': ppbs_data,
                    'borderColor': 'rgb(255, 206, 86)',
                    'backgroundColor': 'rgba(255, 206, 86, 0.1)',
                    'tension': 0.1
                }
            ],
            'chart_type': 'line',
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'روند قند خون'
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False,
                        'min': 50,
                        'max': 400,
                        'title': {
                            'display': True,
                            'text': 'قند خون (mg/dL)'
                        }
                    }
                }
            }
        }
    
    def get_hba1c_trend_data(self, patient: Patient) -> Dict:
        """داده‌های روند HbA1c"""
        # آخرین 12 ماه
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        results = LabResult.objects.filter(
            test__patient=patient,
            test__test_type='HBA1C',
            test__test_date__range=[start_date, end_date]
        ).select_related('test').order_by('test__test_date')
        
        data = []
        for result in results:
            data.append({
                'x': result.test.test_date.strftime('%Y-%m-%d'),
                'y': float(result.value) if result.value else 0
            })
        
        return {
            'labels': [d['x'] for d in data],
            'datasets': [{
                'label': 'HbA1c (%)',
                'data': data,
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                'tension': 0.1,
                'fill': True
            }],
            'chart_type': 'line',
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'روند HbA1c در یک سال گذشته'
                    },
                    'annotation': {
                        'annotations': {
                            'goal': {
                                'type': 'line',
                                'yMin': 7,
                                'yMax': 7,
                                'borderColor': 'rgb(255, 99, 132)',
                                'borderWidth': 2,
                                'borderDash': [5, 5],
                                'label': {
                                    'content': 'هدف درمانی',
                                    'enabled': True,
                                    'position': 'end'
                                }
                            }
                        }
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False,
                        'min': 4,
                        'max': 14,
                        'title': {
                            'display': True,
                            'text': 'HbA1c (%)'
                        }
                    }
                }
            }
        }


class DoctorAnalyticsService:
    """سرویس تحلیل داده‌های پزشکان"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def calculate_doctor_analytics(self, doctor: DoctorProfile, target_date: Optional[date] = None) -> DoctorAnalytics:
        """محاسبه آمارهای یک پزشک برای تاریخ مشخص"""
        if not target_date:
            target_date = timezone.now().date()
        
        # بازه 30 روزه برای محاسبات
        end_date = target_date
        start_date = end_date - timedelta(days=30)
        
        # دریافت یا ایجاد رکورد آنالیتیکس
        analytics, created = DoctorAnalytics.objects.get_or_create(
            doctor=doctor,
            date=target_date
        )
        
        # آمار بیماران
        all_patients = Patient.objects.filter(primary_doctor=doctor)
        analytics.total_patients = all_patients.count()
        
        # بیماران فعال (حداقل یک ویزیت در 3 ماه گذشته)
        active_patients = all_patients.filter(
            encounters__encounter_date__gte=end_date - timedelta(days=90)
        ).distinct()
        analytics.active_patients = active_patients.count()
        
        # بیماران جدید
        analytics.new_patients = all_patients.filter(
            created_at__date__range=[start_date, end_date]
        ).count()
        
        # آمار ویزیت‌ها
        analytics.total_encounters = Encounter.objects.filter(
            doctor=doctor,
            encounter_date__range=[start_date, end_date]
        ).count()
        
        if analytics.active_patients > 0:
            analytics.avg_encounters_per_patient = analytics.total_encounters / analytics.active_patients
        
        # میانگین HbA1c بیماران
        recent_hba1c = LabResult.objects.filter(
            test__patient__in=active_patients,
            test__test_type='HBA1C',
            test__test_date__gte=end_date - timedelta(days=90)
        ).values('test__patient').annotate(
            latest_value=Max('value')
        )
        
        if recent_hba1c:
            hba1c_values = [float(r['latest_value']) for r in recent_hba1c if r['latest_value']]
            if hba1c_values:
                analytics.avg_patient_hba1c = np.mean(hba1c_values)
                analytics.patients_at_goal = sum(1 for v in hba1c_values if v < 7)
                analytics.patients_above_goal = sum(1 for v in hba1c_values if v >= 7)
        
        # آمار هشدارها
        all_alerts = ClinicalAlert.objects.filter(
            patient__in=all_patients,
            created_at__date__range=[start_date, end_date]
        )
        analytics.total_alerts = all_alerts.count()
        analytics.critical_alerts = all_alerts.filter(severity='critical').count()
        
        # محاسبه امتیاز عملکرد
        analytics.performance_score = self._calculate_performance_score(analytics)
        
        analytics.save()
        return analytics
    
    def _calculate_performance_score(self, analytics: DoctorAnalytics) -> float:
        """محاسبه امتیاز عملکرد پزشک"""
        score = 0.0
        weights = {
            'patient_engagement': 0.25,
            'clinical_outcomes': 0.35,
            'alert_management': 0.20,
            'documentation': 0.20
        }
        
        # امتیاز درگیری بیماران
        if analytics.total_patients > 0:
            engagement_rate = analytics.active_patients / analytics.total_patients
            score += engagement_rate * 100 * weights['patient_engagement']
        
        # امتیاز نتایج بالینی
        if analytics.active_patients > 0:
            goal_achievement_rate = analytics.patients_at_goal / analytics.active_patients
            score += goal_achievement_rate * 100 * weights['clinical_outcomes']
        
        # امتیاز مدیریت هشدارها
        if analytics.total_alerts > 0:
            critical_response_rate = 1 - (analytics.critical_alerts / analytics.total_alerts)
            score += critical_response_rate * 100 * weights['alert_management']
        else:
            score += 100 * weights['alert_management']  # اگر هشداری نبوده، امتیاز کامل
        
        # امتیاز مستندسازی
        if analytics.total_encounters > 0 and analytics.active_patients > 0:
            documentation_rate = min(analytics.avg_encounters_per_patient / 1.5, 1)  # حداقل 1.5 ویزیت در ماه
            score += documentation_rate * 100 * weights['documentation']
        
        return round(score, 2)
    
    def get_patient_distribution_data(self, doctor: DoctorProfile) -> Dict:
        """داده‌های توزیع بیماران بر اساس کنترل دیابت"""
        patients = Patient.objects.filter(primary_doctor=doctor)
        
        distribution = {
            'excellent': 0,  # HbA1c < 7
            'good': 0,       # HbA1c 7-8
            'fair': 0,       # HbA1c 8-9
            'poor': 0        # HbA1c > 9
        }
        
        for patient in patients:
            # آخرین HbA1c
            latest_hba1c = LabResult.objects.filter(
                test__patient=patient,
                test__test_type='HBA1C'
            ).order_by('-test__test_date').first()
            
            if latest_hba1c and latest_hba1c.value:
                value = float(latest_hba1c.value)
                if value < 7:
                    distribution['excellent'] += 1
                elif value < 8:
                    distribution['good'] += 1
                elif value < 9:
                    distribution['fair'] += 1
                else:
                    distribution['poor'] += 1
        
        return {
            'labels': ['عالی (<7%)', 'خوب (7-8%)', 'متوسط (8-9%)', 'ضعیف (>9%)'],
            'datasets': [{
                'data': list(distribution.values()),
                'backgroundColor': [
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(255, 99, 132, 0.8)'
                ],
                'borderColor': [
                    'rgb(75, 192, 192)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 206, 86)',
                    'rgb(255, 99, 132)'
                ],
                'borderWidth': 1
            }],
            'chart_type': 'doughnut',
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'توزیع بیماران بر اساس کنترل دیابت'
                    },
                    'legend': {
                        'display': True,
                        'position': 'bottom'
                    }
                }
            }
        }


class SystemAnalyticsService:
    """سرویس تحلیل داده‌های سیستم"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
    
    def calculate_system_analytics(self, target_date: Optional[date] = None) -> SystemAnalytics:
        """محاسبه آمارهای کلی سیستم"""
        if not target_date:
            target_date = timezone.now().date()
        
        # دریافت یا ایجاد رکورد آنالیتیکس
        analytics, created = SystemAnalytics.objects.get_or_create(
            date=target_date
        )
        
        # آمار کاربران
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        analytics.total_users = User.objects.filter(is_active=True).count()
        analytics.total_doctors = DoctorProfile.objects.filter(is_active=True).count()
        analytics.total_patients = Patient.objects.filter(is_active=True).count()
        
        # کاربران فعال (ورود در 30 روز گذشته)
        analytics.active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # کاربران فعال روزانه
        analytics.daily_active_users = User.objects.filter(
            last_login__date=target_date
        ).count()
        
        # آمار داده‌ها
        analytics.total_encounters = Encounter.objects.count()
        analytics.total_lab_tests = LabTest.objects.count()
        analytics.total_medications = Medication.objects.count()
        analytics.total_alerts = ClinicalAlert.objects.count()
        
        # میانگین HbA1c سیستم
        recent_hba1c = LabResult.objects.filter(
            test__test_type='HBA1C',
            test__test_date__gte=target_date - timedelta(days=90)
        ).values_list('value', flat=True)
        
        if recent_hba1c:
            hba1c_values = [float(v) for v in recent_hba1c if v]
            if hba1c_values:
                analytics.avg_system_hba1c = np.mean(hba1c_values)
                
                # درصد دستیابی به اهداف
                at_goal = sum(1 for v in hba1c_values if v < 7)
                analytics.system_goal_achievement = (at_goal / len(hba1c_values)) * 100
        
        # شمارش تقریبی API calls (می‌توان از لاگ‌ها استفاده کرد)
        # فعلاً یک مقدار نمونه
        analytics.api_calls = 1000
        
        analytics.save()
        return analytics
    
    def get_system_overview_data(self) -> Dict:
        """خلاصه‌ای از وضعیت کلی سیستم"""
        cache_key = 'system_overview_data'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        today = timezone.now().date()
        
        # آمار امروز
        today_analytics = self.calculate_system_analytics(today)
        
        # آمار هفته گذشته برای مقایسه
        week_ago = today - timedelta(days=7)
        week_ago_analytics = SystemAnalytics.objects.filter(date=week_ago).first()
        
        # محاسبه روندها
        patient_trend = {
            'current_value': today_analytics.total_patients,
            'previous_value': week_ago_analytics.total_patients if week_ago_analytics else 0,
            'change_percentage': 0,
            'trend': 'stable'
        }
        
        if week_ago_analytics and week_ago_analytics.total_patients > 0:
            change = ((today_analytics.total_patients - week_ago_analytics.total_patients) / 
                     week_ago_analytics.total_patients) * 100
            patient_trend['change_percentage'] = round(change, 2)
            patient_trend['trend'] = 'up' if change > 0 else 'down' if change < 0 else 'stable'
        
        # توزیع HbA1c
        hba1c_distribution = {
            'excellent': 0,
            'good': 0,
            'fair': 0,
            'poor': 0
        }
        
        recent_results = LabResult.objects.filter(
            test__test_type='HBA1C',
            test__test_date__gte=today - timedelta(days=90)
        ).values_list('value', flat=True)
        
        for value in recent_results:
            if value:
                v = float(value)
                if v < 7:
                    hba1c_distribution['excellent'] += 1
                elif v < 8:
                    hba1c_distribution['good'] += 1
                elif v < 9:
                    hba1c_distribution['fair'] += 1
                else:
                    hba1c_distribution['poor'] += 1
        
        # توزیع هشدارها
        alert_distribution = ClinicalAlert.objects.filter(
            created_at__date=today
        ).values('severity').annotate(count=Count('id'))
        
        alert_dist_dict = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        for item in alert_distribution:
            alert_dist_dict[item['severity']] = item['count']
        
        data = {
            'total_patients': today_analytics.total_patients,
            'active_patients': Patient.objects.filter(
                encounters__encounter_date__gte=today - timedelta(days=30)
            ).distinct().count(),
            'total_encounters_today': Encounter.objects.filter(
                encounter_date=today
            ).count(),
            'pending_alerts': ClinicalAlert.objects.filter(
                is_acknowledged=False
            ).count(),
            'avg_hba1c': today_analytics.avg_system_hba1c or 0,
            'avg_glucose': 0,  # محاسبه میانگین قند خون امروز
            'patient_trend': patient_trend,
            'hba1c_trend': {
                'current_value': today_analytics.avg_system_hba1c or 0,
                'previous_value': week_ago_analytics.avg_system_hba1c if week_ago_analytics else 0,
                'change_percentage': 0,
                'trend': 'stable'
            },
            'glucose_trend': {
                'current_value': 0,
                'previous_value': 0,
                'change_percentage': 0,
                'trend': 'stable'
            },
            'hba1c_distribution': hba1c_distribution,
            'alert_distribution': alert_dist_dict,
            'goal_achievement_rate': today_analytics.system_goal_achievement or 0,
            'compliance_rate': 0  # محاسبه نرخ پایبندی کلی
        }
        
        # کش برای 5 دقیقه
        cache.set(cache_key, data, 300)
        
        return data
    
    def get_trend_chart_data(self, metric: str, period: str = 'month') -> Dict:
        """داده‌های نمودار روند برای متریک مشخص"""
        start_date, end_date = self.analytics_service.get_date_range(period)
        
        analytics = SystemAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        labels = []
        data = []
        
        for record in analytics:
            labels.append(record.date.strftime('%Y-%m-%d'))
            
            if metric == 'users':
                data.append(record.total_users)
            elif metric == 'patients':
                data.append(record.total_patients)
            elif metric == 'encounters':
                data.append(record.total_encounters)
            elif metric == 'hba1c':
                data.append(record.avg_system_hba1c or 0)
            elif metric == 'active_users':
                data.append(record.daily_active_users)
        
        metric_labels = {
            'users': 'تعداد کاربران',
            'patients': 'تعداد بیماران',
            'encounters': 'تعداد ویزیت‌ها',
            'hba1c': 'میانگین HbA1c',
            'active_users': 'کاربران فعال روزانه'
        }
        
        return {
            'labels': labels,
            'datasets': [{
                'label': metric_labels.get(metric, metric),
                'data': data,
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                'tension': 0.1,
                'fill': True
            }],
            'chart_type': 'line',
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'روند {metric_labels.get(metric, metric)}'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }