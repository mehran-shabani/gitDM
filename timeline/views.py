from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from gitdm.models import PatientProfile
from gitdm.permissions import IsDoctor, IsPatientOwnerOrDoctor
from .models import (
    MedicalTimeline, TestReminder, TimelineEventCategory, 
    PatientTimelinePreference, ReminderTemplate
)
from .serializers import (
    MedicalTimelineSerializer, TestReminderSerializer,
    TimelineEventCategorySerializer, PatientTimelinePreferenceSerializer,
    ReminderTemplateSerializer, CreateReminderFromTemplateSerializer,
    TimelineFilterSerializer
)


class MedicalTimelineViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت تایم‌لاین پزشکی
    """
    serializer_class = MedicalTimelineSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        """فیلتر کردن تایم‌لاین بر اساس دسترسی کاربر"""
        if self.request.user.is_superuser:
            return MedicalTimeline.objects.select_related(
                'patient', 'created_by', 'content_type'
            ).prefetch_related('notes')
        
        # پزشکان فقط بیماران خود را می‌بینند
        return MedicalTimeline.objects.filter(
            patient__primary_doctor=self.request.user
        ).select_related('patient', 'created_by', 'content_type').prefetch_related('notes')
    
    @action(detail=False, methods=['get'])
    def patient_timeline(self, request):
        """دریافت تایم‌لاین یک بیمار خاص"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient = get_object_or_404(PatientProfile, id=patient_id)
        
        # بررسی دسترسی
        if not request.user.is_superuser and patient.primary_doctor != request.user:
            return Response(
                {'error': 'دسترسی غیرمجاز'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # فیلتر کردن
        filter_serializer = TimelineFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        filters = filter_serializer.validated_data
        
        queryset = MedicalTimeline.objects.filter(
            patient=patient,
            is_visible=True
        ).select_related('patient', 'created_by', 'content_type')
        
        # اعمال فیلترها
        if filters.get('start_date'):
            queryset = queryset.filter(occurred_at__gte=filters['start_date'])
        if filters.get('end_date'):
            queryset = queryset.filter(occurred_at__lte=filters['end_date'])
        if filters.get('event_types'):
            queryset = queryset.filter(event_type__in=filters['event_types'])
        if filters.get('severity'):
            queryset = queryset.filter(severity__in=filters['severity'])
        
        # محدود کردن تعداد نتایج
        limit = filters.get('limit', 100)
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'patient': {
                'id': patient.id,
                'name': patient.full_name,
                'age': patient.age
            },
            'timeline': serializer.data,
            'total_events': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def timeline_summary(self, request):
        """خلاصه‌ای از تایم‌لاین بیمار"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient = get_object_or_404(PatientProfile, id=patient_id)
        
        # بررسی دسترسی
        if not request.user.is_superuser and patient.primary_doctor != request.user:
            return Response(
                {'error': 'دسترسی غیرمجاز'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # آمار کلی
        timeline_stats = MedicalTimeline.objects.filter(
            patient=patient, is_visible=True
        ).values('event_type').annotate(count=Count('id'))
        
        # آخرین رویدادها
        recent_events = MedicalTimeline.objects.filter(
            patient=patient, is_visible=True
        ).select_related('created_by')[:10]
        
        return Response({
            'patient': {
                'id': patient.id,
                'name': patient.full_name,
                'age': patient.age
            },
            'statistics': {
                event['event_type']: event['count'] 
                for event in timeline_stats
            },
            'recent_events': MedicalTimelineSerializer(recent_events, many=True).data
        })


class TestReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت یادآورهای آزمایشات
    """
    serializer_class = TestReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        """فیلتر کردن یادآورها بر اساس دسترسی کاربر"""
        if self.request.user.is_superuser:
            return TestReminder.objects.select_related('patient', 'created_by')
        
        return TestReminder.objects.filter(
            patient__primary_doctor=self.request.user
        ).select_related('patient', 'created_by')
    
    @action(detail=False, methods=['get'])
    def patient_reminders(self, request):
        """دریافت یادآورهای یک بیمار خاص"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient = get_object_or_404(PatientProfile, id=patient_id)
        
        # بررسی دسترسی
        if not request.user.is_superuser and patient.primary_doctor != request.user:
            return Response(
                {'error': 'دسترسی غیرمجاز'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        reminders = TestReminder.objects.filter(
            patient=patient, is_active=True
        ).select_related('created_by')
        
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue_reminders(self, request):
        """یادآورهای عقب‌افتاده"""
        now = timezone.now()
        reminders = self.get_queryset().filter(
            next_due__lt=now,
            is_active=True
        )
        
        serializer = self.get_serializer(reminders, many=True)
        return Response({
            'overdue_count': reminders.count(),
            'reminders': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming_reminders(self, request):
        """یادآورهای آتی (در ۷ روز آینده)"""
        now = timezone.now()
        week_later = now + timedelta(days=7)
        
        reminders = self.get_queryset().filter(
            next_due__gte=now,
            next_due__lte=week_later,
            is_active=True
        )
        
        serializer = self.get_serializer(reminders, many=True)
        return Response({
            'upcoming_count': reminders.count(),
            'reminders': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """علامت‌گذاری یادآوری به عنوان انجام شده"""
        reminder = self.get_object()
        performed_date = request.data.get('performed_date')
        
        if performed_date:
            try:
                performed_date = timezone.datetime.fromisoformat(performed_date.replace('Z', '+00:00'))
            except ValueError:
                return Response(
                    {'error': 'فرمت تاریخ نامعتبر'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        reminder.mark_as_completed(performed_date)
        
        return Response({
            'message': 'یادآوری به عنوان انجام شده علامت‌گذاری شد',
            'next_due': reminder.next_due
        })
    
    @action(detail=False, methods=['post'])
    def create_from_template(self, request):
        """ایجاد یادآوری از قالب"""
        serializer = CreateReminderFromTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        patient = get_object_or_404(PatientProfile, id=serializer.validated_data['patient'])
        template = get_object_or_404(ReminderTemplate, id=serializer.validated_data['template_id'])
        
        # بررسی دسترسی
        if not request.user.is_superuser and patient.primary_doctor != request.user:
            return Response(
                {'error': 'دسترسی غیرمجاز'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ایجاد یادآوری
        reminder = TestReminder.objects.create(
            patient=patient,
            test_type=template.test_type,
            frequency=template.default_frequency,
            priority=template.default_priority,
            next_due=serializer.validated_data['next_due'],
            reminder_days_before=template.default_reminder_days,
            notes=serializer.validated_data.get('notes', ''),
            created_by=request.user
        )
        
        return Response(
            TestReminderSerializer(reminder).data,
            status=status.HTTP_201_CREATED
        )


class ReminderTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده قالب‌های یادآوری
    """
    queryset = ReminderTemplate.objects.filter(is_active=True)
    serializer_class = ReminderTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    
    @action(detail=False, methods=['get'])
    def by_test_type(self, request):
        """دریافت قالب بر اساس نوع آزمایش"""
        test_type = request.query_params.get('test_type')
        if not test_type:
            return Response(
                {'error': 'test_type الزامی است'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template = self.queryset.get(test_type=test_type)
            return Response(self.get_serializer(template).data)
        except ReminderTemplate.DoesNotExist:
            return Response(
                {'error': 'قالب برای این نوع آزمایش یافت نشد'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class TimelineEventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده دسته‌بندی‌های رویدادهای تایم‌لاین
    """
    queryset = TimelineEventCategory.objects.all()
    serializer_class = TimelineEventCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class PatientTimelinePreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت تنظیمات تایم‌لاین بیمار
    """
    serializer_class = PatientTimelinePreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctor]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return PatientTimelinePreference.objects.select_related('patient')
        
        return PatientTimelinePreference.objects.filter(
            patient__primary_doctor=self.request.user
        ).select_related('patient')
    
    @action(detail=False, methods=['get', 'post', 'put'])
    def my_preferences(self, request):
        """تنظیمات تایم‌لاین کاربر جاری (اگر بیمار است)"""
        if not request.user.is_patient:
            return Response(
                {'error': 'فقط بیماران می‌توانند تنظیمات شخصی داشته باشند'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient = request.user.patient_profile
        except AttributeError:
            return Response(
                {'error': 'پروفایل بیمار یافت نشد'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        preference, created = PatientTimelinePreference.objects.get_or_create(
            patient=patient
        )
        
        if request.method == 'GET':
            return Response(self.get_serializer(preference).data)
        
        elif request.method in ['POST', 'PUT']:
            serializer = self.get_serializer(preference, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


@login_required
@require_http_methods(["GET"])
def patient_timeline_view(request, patient_id):
    """
    نمایش صفحه تایم‌لاین بیمار
    """
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # بررسی دسترسی
    if not request.user.is_superuser and patient.primary_doctor != request.user:
        return render(request, 'timeline/access_denied.html', {
            'message': 'شما به این بیمار دسترسی ندارید'
        })
    
    context = {
        'patient': {
            'id': patient.id,
            'name': patient.full_name,
            'age': patient.age
        }
    }
    
    return render(request, 'timeline/patient_timeline.html', context)


@login_required
@require_http_methods(["GET"])  
def timeline_dashboard_view(request):
    """
    داشبورد کلی تایم‌لاین برای پزشک
    """
    if not request.user.is_doctor:
        return render(request, 'timeline/access_denied.html', {
            'message': 'فقط پزشکان به داشبورد دسترسی دارند'
        })
    
    from .utils import TimelineAnalyzer
    from .services import ReminderService
    
    # آمار کلی
    overdue_reminders = ReminderService.get_overdue_reminders(request.user)
    upcoming_reminders = ReminderService.get_upcoming_reminders(request.user)
    
    # بیماران با هشدارهای بحرانی
    critical_patients = []
    if hasattr(request.user, 'patients'):
        for patient in request.user.patients.all()[:10]:  # ۱۰ بیمار اول
            critical_alerts = TimelineAnalyzer.get_critical_alerts(patient)
            if critical_alerts:
                critical_patients.append({
                    'patient': patient,
                    'alerts_count': len(critical_alerts),
                    'latest_alert': critical_alerts[0] if critical_alerts else None
                })
    
    context = {
        'overdue_count': overdue_reminders.count(),
        'upcoming_count': upcoming_reminders.count(),
        'critical_patients': critical_patients,
        'overdue_reminders': overdue_reminders[:5],  # ۵ مورد اول
        'upcoming_reminders': upcoming_reminders[:5]  # ۵ مورد اول
    }
    
    return render(request, 'timeline/dashboard.html', context)