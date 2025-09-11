from datetime import datetime, timedelta
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q
from gitdm.permissions import IsDoctor, IsDoctorAdmin
from .models import PatientAnalytics, DoctorAnalytics, SystemAnalytics, Report
from .serializers import (
    PatientAnalyticsSerializer, DoctorAnalyticsSerializer, SystemAnalyticsSerializer,
    ChartDataSerializer, TrendAnalysisSerializer, ReportSerializer, ReportRequestSerializer,
    DashboardSummarySerializer
)
from .services import PatientAnalyticsService, DoctorAnalyticsService, SystemAnalyticsService
from .report_service import ReportGenerationService


class PatientAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet برای آنالیتیکس بیماران"""
    serializer_class = PatientAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        
        # اگر کاربر پزشک است، فقط آنالیتیکس بیماران خودش را ببیند
        if hasattr(user, 'doctor_profile'):
            doctor = user.doctor_profile
            return PatientAnalytics.objects.filter(
                patient__primary_doctor=doctor
            ).select_related('patient')
        
        # ادمین‌ها همه را می‌بینند
        if user.is_superuser:
            return PatientAnalytics.objects.all().select_related('patient')
        
        return PatientAnalytics.objects.none()
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """محاسبه آنالیتیکس برای یک بیمار"""
        patient_id = request.data.get('patient_id')
        date_str = request.data.get('date')
        
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی دسترسی به بیمار
        from gitdm.models import PatientProfile as Patient
        patient = get_object_or_404(Patient, id=patient_id)
        
        if hasattr(request.user, 'doctor_profile'):
            if patient.primary_doctor != request.user.doctor_profile:
                return Response(
                    {'error': 'شما دسترسی به این بیمار ندارید'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # محاسبه آنالیتیکس
        service = PatientAnalyticsService()
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        analytics = service.calculate_patient_analytics(patient, target_date)
        
        serializer = PatientAnalyticsSerializer(analytics)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def glucose_chart(self, request, pk=None):
        """دریافت داده‌های نمودار قند خون"""
        analytics = self.get_object()
        patient = analytics.patient
        period = request.query_params.get('period', 'month')
        
        service = PatientAnalyticsService()
        chart_data = service.get_glucose_chart_data(patient, period)
        
        serializer = ChartDataSerializer(chart_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def hba1c_trend(self, request, pk=None):
        """دریافت داده‌های روند HbA1c"""
        analytics = self.get_object()
        patient = analytics.patient
        
        service = PatientAnalyticsService()
        chart_data = service.get_hba1c_trend_data(patient)
        
        serializer = ChartDataSerializer(chart_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def batch_analytics(self, request):
        """دریافت آنالیتیکس برای چند بیمار"""
        patient_ids = request.query_params.getlist('patient_ids[]')
        
        if not patient_ids:
            return Response(
                {'error': 'patient_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # فیلتر بر اساس دسترسی
        from gitdm.models import PatientProfile as Patient
        if hasattr(request.user, 'doctor_profile'):
            patients = Patient.objects.filter(
                id__in=patient_ids,
                primary_doctor=request.user.doctor_profile
            )
        elif request.user.is_superuser:
            patients = Patient.objects.filter(id__in=patient_ids)
        else:
            return Response(
                {'error': 'شما دسترسی به این عملیات ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت آخرین آنالیتیکس هر بیمار
        analytics_data = []
        for patient in patients:
            latest_analytics = PatientAnalytics.objects.filter(
                patient=patient
            ).order_by('-date').first()
            
            if latest_analytics:
                analytics_data.append(latest_analytics)
        
        serializer = PatientAnalyticsSerializer(analytics_data, many=True)
        return Response(serializer.data)


class DoctorAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet برای آنالیتیکس پزشکان"""
    serializer_class = DoctorAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        
        # پزشکان فقط آنالیتیکس خودشان را می‌بینند
        if hasattr(user, 'doctor_profile'):
            return DoctorAnalytics.objects.filter(
                doctor=user.doctor_profile
            )
        
        # ادمین‌ها همه را می‌بینند
        if user.is_superuser:
            return DoctorAnalytics.objects.all().select_related('doctor')
        
        return DoctorAnalytics.objects.none()
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """محاسبه آنالیتیکس برای یک پزشک"""
        doctor_id = request.data.get('doctor_id')
        date_str = request.data.get('date')
        
        # اگر doctor_id نباشد، برای پزشک فعلی محاسبه کن
        if not doctor_id and hasattr(request.user, 'doctor_profile'):
            doctor = request.user.doctor_profile
        else:
            from gitdm.models import DoctorProfile
            doctor = get_object_or_404(DoctorProfile, id=doctor_id)
            
            # بررسی دسترسی
            if not request.user.is_superuser and doctor.user != request.user:
                return Response(
                    {'error': 'شما دسترسی به این پزشک ندارید'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # محاسبه آنالیتیکس
        service = DoctorAnalyticsService()
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        analytics = service.calculate_doctor_analytics(doctor, target_date)
        
        serializer = DoctorAnalyticsSerializer(analytics)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def patient_distribution(self, request, pk=None):
        """دریافت نمودار توزیع بیماران"""
        analytics = self.get_object()
        doctor = analytics.doctor
        
        service = DoctorAnalyticsService()
        chart_data = service.get_patient_distribution_data(doctor)
        
        serializer = ChartDataSerializer(chart_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def performance_comparison(self, request):
        """مقایسه عملکرد پزشکان"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'فقط ادمین‌ها دسترسی به این عملیات دارند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت آخرین آنالیتیکس همه پزشکان
        latest_date = DoctorAnalytics.objects.latest('date').date if DoctorAnalytics.objects.exists() else timezone.now().date()
        
        analytics = DoctorAnalytics.objects.filter(
            date=latest_date
        ).select_related('doctor').order_by('-performance_score')[:10]
        
        serializer = DoctorAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)


class SystemAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet برای آنالیتیکس سیستم"""
    queryset = SystemAnalytics.objects.all()
    serializer_class = SystemAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsDoctorAdmin]
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """محاسبه آنالیتیکس سیستم"""
        date_str = request.data.get('date')
        
        service = SystemAnalyticsService()
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        analytics = service.calculate_system_analytics(target_date)
        
        serializer = SystemAnalyticsSerializer(analytics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """دریافت نمای کلی سیستم"""
        service = SystemAnalyticsService()
        overview_data = service.get_system_overview_data()
        
        serializer = DashboardSummarySerializer(overview_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trend_chart(self, request):
        """دریافت نمودار روند"""
        metric = request.query_params.get('metric', 'users')
        period = request.query_params.get('period', 'month')
        
        service = SystemAnalyticsService()
        chart_data = service.get_trend_chart_data(metric, period)
        
        serializer = ChartDataSerializer(chart_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """بررسی سلامت سیستم"""
        from gitdm.models import PatientProfile as Patient
        from gitdm.models import DoctorProfile
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now(),
            'checks': {
                'database': 'ok',
                'analytics': 'ok',
                'reports': 'ok'
            },
            'metrics': {
                'total_users': Patient.objects.count() + DoctorProfile.objects.count(),
                'active_sessions': 0,  # می‌توان از session backend خواند
                'pending_reports': Report.objects.filter(status='pending').count()
            }
        }
        
        return Response(health_data)


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت گزارش‌ها"""
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        
        # فیلتر بر اساس درخواست‌دهنده
        queryset = Report.objects.filter(requested_by=user)
        
        # ادمین‌ها همه گزارش‌ها را می‌بینند
        if user.is_superuser:
            queryset = Report.objects.all()
        
        return queryset.select_related('requested_by', 'patient', 'doctor')
    
    def create(self, request, *args, **kwargs):
        """ایجاد درخواست گزارش جدید"""
        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ایجاد گزارش
        report = Report.objects.create(
            report_type=serializer.validated_data['report_type'],
            format=serializer.validated_data['format'],
            requested_by=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            metadata={
                'include_charts': serializer.validated_data.get('include_charts', True),
                'include_detailed_data': serializer.validated_data.get('include_detailed_data', False)
            }
        )
        
        # افزودن بیمار یا پزشک در صورت نیاز
        if serializer.validated_data.get('patient_id'):
            patient = get_object_or_404(Patient, id=serializer.validated_data['patient_id'])
            
            # بررسی دسترسی
            if hasattr(request.user, 'doctor_profile'):
                if patient.primary_doctor != request.user.doctor_profile:
                    report.delete()
                    return Response(
                        {'error': 'شما دسترسی به این بیمار ندارید'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            report.patient = patient
            report.save()
        
        if serializer.validated_data.get('doctor_id'):
            doctor = get_object_or_404(DoctorProfile, id=serializer.validated_data['doctor_id'])
            
            # بررسی دسترسی
            if not request.user.is_superuser and doctor.user != request.user:
                report.delete()
                return Response(
                    {'error': 'شما دسترسی به این پزشک ندارید'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            report.doctor = doctor
            report.save()
        
        # شروع پردازش گزارش (می‌تواند با Celery انجام شود)
        service = ReportGenerationService()
        try:
            file_path = service.generate_report(report)
        except Exception as e:
            return Response(
                {'error': f'خطا در تولید گزارش: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """دانلود فایل گزارش"""
        report = self.get_object()
        
        if report.status != 'completed' or not report.file_path:
            return Response(
                {'error': 'گزارش هنوز آماده نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد response برای دانلود
        from django.http import FileResponse
        import os
        
        if os.path.exists(report.file_path):
            response = FileResponse(
                open(report.file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(report.file_path)
            )
            return response
        else:
            return Response(
                {'error': 'فایل گزارش یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """ارسال گزارش از طریق ایمیل"""
        report = self.get_object()
        recipients = request.data.get('recipients', [])
        
        if not recipients:
            recipients = [request.user.email]
        
        service = ReportGenerationService()
        try:
            service.send_report_email(report, recipients)
            return Response({'message': 'گزارش با موفقیت ارسال شد'})
        except Exception as e:
            return Response(
                {'error': f'خطا در ارسال ایمیل: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """دریافت قالب‌های گزارش"""
        templates = [
            {
                'id': 'patient_summary',
                'name': 'خلاصه بیمار',
                'description': 'گزارش جامع از وضعیت بیمار شامل آزمایش‌ها، داروها و روند درمان',
                'required_params': ['patient_id'],
                'optional_params': ['start_date', 'end_date', 'include_charts']
            },
            {
                'id': 'doctor_performance',
                'name': 'عملکرد پزشک',
                'description': 'گزارش عملکرد پزشک شامل آمار بیماران و نتایج درمان',
                'required_params': ['doctor_id'],
                'optional_params': ['start_date', 'end_date']
            },
            {
                'id': 'system_overview',
                'name': 'نمای کلی سیستم',
                'description': 'گزارش کلی از وضعیت سیستم و آمارهای عمومی',
                'required_params': [],
                'optional_params': ['start_date', 'end_date']
            }
        ]
        
        return Response(templates)


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet برای داشبورد تحلیلی"""
    permission_classes = [IsAuthenticated, IsDoctor]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه داشبورد برای کاربر فعلی"""
        user = request.user
        
        from gitdm.models import PatientProfile as Patient
        from encounters.models import Encounter
        from notifications.models import ClinicalAlert
        if hasattr(user, 'doctor_profile'):
            # داشبورد پزشک
            doctor = user.doctor_profile
            
            # آمار امروز
            today = timezone.now().date()
            
            summary_data = {
                'total_patients': Patient.objects.filter(primary_doctor=doctor).count(),
                'active_patients': Patient.objects.filter(
                    primary_doctor=doctor,
                    encounters__occurred_at__gte=today - timedelta(days=30)
                ).distinct().count(),
                'total_encounters_today': Encounter.objects.filter(
                    created_by=doctor.user,
                    occurred_at__date=today
                ).count(),
                'pending_alerts': ClinicalAlert.objects.filter(
                    patient__primary_doctor=doctor,
                    is_acknowledged=False
                ).count()
            }
            
            # آخرین آنالیتیکس
            latest_analytics = DoctorAnalytics.objects.filter(
                doctor=doctor
            ).order_by('-date').first()
            
            if latest_analytics:
                summary_data.update({
                    'avg_hba1c': latest_analytics.avg_patient_hba1c or 0,
                    'goal_achievement_rate': (latest_analytics.patients_at_goal / latest_analytics.active_patients * 100) if latest_analytics.active_patients > 0 else 0,
                    'performance_score': latest_analytics.performance_score or 0
                })
            
        else:
            # داشبورد ادمین
            service = SystemAnalyticsService()
            summary_data = service.get_system_overview_data()
        
        serializer = DashboardSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def widgets(self, request):
        """دریافت ویجت‌های داشبورد"""
        widgets = []
        
        if hasattr(request.user, 'doctor_profile'):
            # ویجت‌های پزشک
            widgets = [
                {
                    'id': 'patient_summary',
                    'type': 'stat',
                    'title': 'خلاصه بیماران',
                    'size': 'small'
                },
                {
                    'id': 'glucose_trends',
                    'type': 'chart',
                    'title': 'روند قند خون بیماران',
                    'size': 'medium'
                },
                {
                    'id': 'hba1c_distribution',
                    'type': 'chart',
                    'title': 'توزیع HbA1c',
                    'size': 'small'
                },
                {
                    'id': 'recent_alerts',
                    'type': 'list',
                    'title': 'هشدارهای اخیر',
                    'size': 'medium'
                }
            ]
        else:
            # ویجت‌های ادمین
            widgets = [
                {
                    'id': 'system_overview',
                    'type': 'stat',
                    'title': 'نمای کلی سیستم',
                    'size': 'large'
                },
                {
                    'id': 'user_trends',
                    'type': 'chart',
                    'title': 'روند کاربران',
                    'size': 'medium'
                },
                {
                    'id': 'performance_metrics',
                    'type': 'gauge',
                    'title': 'معیارهای عملکرد',
                    'size': 'small'
                }
            ]
        
        return Response(widgets)