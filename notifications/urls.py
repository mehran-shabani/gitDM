"""
URL Configuration برای notifications app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, ClinicalAlertViewSet
from .smart_reminder_views import (
    SmartReminderViewSet,
    ReminderPatternViewSet,
    ReminderScheduleViewSet,
    ReminderResponseViewSet,
    SmartReminderServiceViewSet
)

router = DefaultRouter()

# اطلاع‌رسانی‌ها و هشدارها
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'alerts', ClinicalAlertViewSet, basename='clinicalalert')

# یادآورهای هوشمند
router.register(r'smart-reminders', SmartReminderViewSet, basename='smartreminder')
router.register(r'reminder-patterns', ReminderPatternViewSet, basename='reminderpattern')
router.register(r'reminder-schedules', ReminderScheduleViewSet, basename='reminderschedule')
router.register(r'reminder-responses', ReminderResponseViewSet, basename='reminderresponse')
router.register(r'reminder-services', SmartReminderServiceViewSet, basename='reminderservice')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
]