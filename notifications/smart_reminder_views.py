"""
API Views برای سیستم یادآوری هوشمند
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta

from .models import (
    SmartReminder, ReminderPattern, ReminderSchedule, ReminderResponse
)
from .serializers import (
    SmartReminderSerializer, ReminderPatternSerializer,
    ReminderScheduleSerializer, ReminderResponseSerializer
)
from .smart_reminder_services import (
    BehaviorAnalysisService, SmartSchedulerService,
    ReminderDeliveryService, AdaptiveLearningService
)
from security.permissions import IsDoctor, IsPatientOwnerOrDoctor


class SmartReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت یادآورهای هوشمند
    """
    serializer_class = SmartReminderSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = SmartReminder.objects.all()
        
        # فیلتر بر اساس دسترسی پزشک
        if hasattr(user, 'doctor_profile'):
            # پزشک فقط یادآورهای بیماران خود را می‌بیند
            queryset = queryset.filter(
                patient__primary_doctor=user.doctor_profile
            )
        
        # فیلترهای اضافی
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        reminder_type = self.request.query_params.get('type')
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('patient', 'created_by')
    
    def create(self, request):
        """
        ایجاد یادآوری جدید
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # بررسی دسترسی به بیمار
        patient_id = serializer.validated_data['patient'].id
        if not self._has_patient_access(request.user, patient_id):
            return Response(
                {'error': 'شما دسترسی به این بیمار ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ذخیره یادآوری
        reminder = serializer.save(created_by=request.user)
        
        # ایجاد برنامه زمان‌بندی
        scheduler_service = SmartSchedulerService()
        schedules = scheduler_service.create_schedules_for_reminder(reminder)
        
        return Response(
            {
                'reminder': SmartReminderSerializer(reminder).data,
                'schedules_created': len(schedules)
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        متوقف کردن موقت یادآوری
        """
        reminder = self.get_object()
        reminder.status = SmartReminder.Status.PAUSED
        reminder.save()
        
        # لغو برنامه‌های آینده
        ReminderSchedule.objects.filter(
            reminder=reminder,
            scheduled_time__gt=timezone.now(),
            is_sent=False
        ).delete()
        
        return Response({'status': 'paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        از سرگیری یادآوری
        """
        reminder = self.get_object()
        reminder.status = SmartReminder.Status.ACTIVE
        reminder.save()
        
        # ایجاد مجدد برنامه‌ها
        scheduler_service = SmartSchedulerService()
        schedules = scheduler_service.create_schedules_for_reminder(reminder)
        
        return Response({
            'status': 'resumed',
            'schedules_created': len(schedules)
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        تکمیل یادآوری
        """
        reminder = self.get_object()
        reminder.status = SmartReminder.Status.COMPLETED
        reminder.save()
        
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        آمار و تحلیل یادآوری
        """
        reminder = self.get_object()
        
        schedules = ReminderSchedule.objects.filter(reminder=reminder)
        responses = ReminderResponse.objects.filter(
            schedule__reminder=reminder
        )
        
        stats = {
            'total_schedules': schedules.count(),
            'sent_count': schedules.filter(is_sent=True).count(),
            'acknowledged_count': schedules.filter(is_acknowledged=True).count(),
            'response_rate': 0,
            'average_response_time': None,
            'action_breakdown': {}
        }
        
        if stats['sent_count'] > 0:
            stats['response_rate'] = (
                stats['acknowledged_count'] / stats['sent_count'] * 100
            )
        
        # میانگین زمان پاسخ
        avg_response = responses.filter(
            response_delay__isnull=False
        ).aggregate(
            avg_delay=Avg('response_delay')
        )
        if avg_response['avg_delay']:
            stats['average_response_time'] = str(avg_response['avg_delay'])
        
        # تفکیک اقدامات
        action_counts = responses.values('action_result').annotate(
            count=Count('id')
        )
        for item in action_counts:
            if item['action_result']:
                stats['action_breakdown'][item['action_result']] = item['count']
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def upcoming_schedules(self, request, pk=None):
        """
        برنامه‌های آینده یادآوری
        """
        reminder = self.get_object()
        
        schedules = ReminderSchedule.objects.filter(
            reminder=reminder,
            scheduled_time__gt=timezone.now(),
            is_sent=False
        ).order_by('scheduled_time')[:10]
        
        serializer = ReminderScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    def _has_patient_access(self, user, patient_id):
        """
        بررسی دسترسی پزشک به بیمار
        """
        if hasattr(user, 'doctor_profile'):
            from gitdm.models import PatientProfile
            patient = PatientProfile.objects.filter(
                id=patient_id,
                primary_doctor=user.doctor_profile
            ).exists()
            return patient
        return False


class ReminderPatternViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده الگوهای رفتاری
    """
    serializer_class = ReminderPatternSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ReminderPattern.objects.all()
        
        if hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(
                patient__primary_doctor=user.doctor_profile
            )
        
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset.select_related('patient')
    
    @action(detail=False, methods=['get'])
    def patient_analysis(self, request):
        """
        تحلیل کامل رفتار بیمار
        """
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی دسترسی
        if not self._has_patient_access(request.user, patient_id):
            return Response(
                {'error': 'شما دسترسی به این بیمار ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        behavior_service = BehaviorAnalysisService()
        analysis = behavior_service.get_patient_preferences(patient_id)
        
        # اضافه کردن بینش‌ها
        learning_service = AdaptiveLearningService()
        insights = learning_service.generate_insights(patient_id)
        
        analysis['insights'] = insights
        
        return Response(analysis)
    
    def _has_patient_access(self, user, patient_id):
        """
        بررسی دسترسی پزشک به بیمار
        """
        if hasattr(user, 'doctor_profile'):
            from gitdm.models import PatientProfile
            patient = PatientProfile.objects.filter(
                id=patient_id,
                primary_doctor=user.doctor_profile
            ).exists()
            return patient
        return False


class ReminderScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت برنامه‌های زمان‌بندی
    """
    serializer_class = ReminderScheduleSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ReminderSchedule.objects.all()
        
        if hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(
                reminder__patient__primary_doctor=user.doctor_profile
            )
        
        # فیلترها
        reminder_id = self.request.query_params.get('reminder_id')
        if reminder_id:
            queryset = queryset.filter(reminder_id=reminder_id)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_time__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_time__lte=date_to)
        
        is_sent = self.request.query_params.get('is_sent')
        if is_sent is not None:
            queryset = queryset.filter(is_sent=is_sent.lower() == 'true')
        
        return queryset.select_related('reminder', 'reminder__patient')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        ثبت پاسخ به یادآوری
        """
        schedule = self.get_object()
        
        data = request.data
        action_taken = data.get('action_taken')
        notes = data.get('notes', '')
        
        schedule.acknowledge(action_taken=action_taken, notes=notes)
        
        # ثبت پاسخ کامل
        if data.get('response_details'):
            delivery_service = ReminderDeliveryService()
            response = delivery_service.handle_reminder_response(
                schedule.id,
                data['response_details']
            )
            
            return Response({
                'schedule': ReminderScheduleSerializer(schedule).data,
                'response': ReminderResponseSerializer(response).data
            })
        
        return Response(ReminderScheduleSerializer(schedule).data)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """
        تغییر زمان یادآوری
        """
        schedule = self.get_object()
        
        if schedule.is_sent:
            return Response(
                {'error': 'نمی‌توان یادآوری ارسال شده را تغییر داد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_time = request.data.get('new_time')
        if not new_time:
            return Response(
                {'error': 'new_time is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            schedule.scheduled_time = datetime.fromisoformat(new_time)
            schedule.save()
            
            return Response(ReminderScheduleSerializer(schedule).data)
        except ValueError:
            return Response(
                {'error': 'Invalid datetime format'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ReminderResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای ثبت و مشاهده پاسخ‌های یادآوری
    """
    serializer_class = ReminderResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ReminderResponse.objects.all()
        
        # دسترسی بر اساس نقش
        if hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(
                schedule__reminder__patient__primary_doctor=user.doctor_profile
            )
        elif hasattr(user, 'patient_profile'):
            queryset = queryset.filter(
                schedule__reminder__patient=user.patient_profile
            )
        
        # فیلترها
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        
        response_type = self.request.query_params.get('response_type')
        if response_type:
            queryset = queryset.filter(response_type=response_type)
        
        return queryset.select_related(
            'schedule', 
            'schedule__reminder',
            'schedule__reminder__patient'
        )
    
    def create(self, request):
        """
        ثبت پاسخ جدید به یادآوری
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # محاسبه تاخیر
        schedule = serializer.validated_data['schedule']
        response_time = timezone.now()
        
        if schedule.sent_at:
            response_delay = response_time - schedule.sent_at
        else:
            response_delay = None
        
        # تعیین نوع پاسخ
        if response_delay and response_delay < timedelta(minutes=5):
            response_type = 'IMMEDIATE'
        elif response_delay and response_delay < timedelta(hours=1):
            response_type = 'DELAYED'
        else:
            response_type = 'NO_RESPONSE'
        
        # ذخیره پاسخ
        response = serializer.save(
            response_time=response_time,
            response_delay=response_delay,
            response_type=response_type
        )
        
        # بروزرسانی schedule
        schedule.acknowledge(
            action_taken=response.action_result,
            notes=response.patient_feedback
        )
        
        return Response(
            ReminderResponseSerializer(response).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def satisfaction_summary(self, request):
        """
        خلاصه رضایت از یادآورها
        """
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        responses = self.get_queryset().filter(
            schedule__reminder__patient_id=patient_id,
            satisfaction_score__isnull=False
        )
        
        summary = responses.aggregate(
            average_satisfaction=Avg('satisfaction_score'),
            total_responses=Count('id')
        )
        
        # تفکیک بر اساس نوع یادآوری
        by_type = responses.values(
            'schedule__reminder__reminder_type'
        ).annotate(
            avg_satisfaction=Avg('satisfaction_score'),
            count=Count('id')
        )
        
        summary['by_reminder_type'] = list(by_type)
        
        return Response(summary)


# API endpoints برای خدمات پس‌زمینه
class SmartReminderServiceViewSet(viewsets.ViewSet):
    """
    ViewSet برای عملیات سرویس یادآوری
    """
    permission_classes = [IsAuthenticated, IsDoctor]
    
    @action(detail=False, methods=['post'])
    def process_reminders(self, request):
        """
        پردازش یادآورهای در انتظار (برای cron job)
        """
        delivery_service = ReminderDeliveryService()
        sent_count = delivery_service.process_pending_reminders()
        
        return Response({
            'sent_count': sent_count,
            'processed_at': timezone.now()
        })
    
    @action(detail=False, methods=['post'])
    def optimize_timing(self, request):
        """
        بهینه‌سازی زمان‌بندی برای یک بیمار
        """
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        learning_service = AdaptiveLearningService()
        learning_service.optimize_reminder_timing(patient_id)
        
        return Response({
            'status': 'optimized',
            'patient_id': patient_id
        })
    
    @action(detail=False, methods=['get'])
    def predict_best_time(self, request):
        """
        پیش‌بینی بهترین زمان برای یادآوری
        """
        patient_id = request.query_params.get('patient_id')
        reminder_type = request.query_params.get('reminder_type')
        date_str = request.query_params.get('date')
        
        if not all([patient_id, reminder_type, date_str]):
            return Response(
                {'error': 'patient_id, reminder_type and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        learning_service = AdaptiveLearningService()
        predictions = learning_service.predict_best_time(
            patient_id, 
            reminder_type,
            date
        )
        
        return Response({
            'predictions': [
                {
                    'hour': hour,
                    'probability': prob,
                    'time': f"{hour:02d}:00"
                }
                for hour, prob in predictions
            ]
        })