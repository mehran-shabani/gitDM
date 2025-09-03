from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification, ClinicalAlert
from .serializers import NotificationSerializer, ClinicalAlertSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده اطلاع‌رسانی‌ها
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        فقط اطلاع‌رسانی‌های کاربر جاری
        """
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        علامت‌گذاری به عنوان خوانده شده
        """
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        علامت‌گذاری همه به عنوان خوانده شده
        """
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'marked_count': count})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        تعداد اطلاع‌رسانی‌های خوانده نشده
        """
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class ClinicalAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده هشدارهای بالینی
    """
    serializer_class = ClinicalAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        فقط هشدارهای بیماران مربوط به پزشک جاری
        """
        user = self.request.user
        if getattr(user, 'is_superuser', False):
            return ClinicalAlert.objects.all()
        
        # فقط بیماران این پزشک
        return ClinicalAlert.objects.filter(patient__primary_doctor=user)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        تایید هشدار توسط پزشک
        """
        alert = self.get_object()
        alert.acknowledge(request.user)
        return Response({'status': 'acknowledged'})
    
    @action(detail=False, methods=['get'])
    def active_count(self, request):
        """
        تعداد هشدارهای فعال
        """
        count = self.get_queryset().filter(is_active=True).count()
        return Response({'active_alerts_count': count})