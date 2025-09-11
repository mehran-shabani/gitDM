from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicalTimelineViewSet, TestReminderViewSet, ReminderTemplateViewSet,
    TimelineEventCategoryViewSet, PatientTimelinePreferenceViewSet,
    patient_timeline_view, timeline_dashboard_view
)

router = DefaultRouter()
router.register(r'timeline', MedicalTimelineViewSet, basename='timeline')
router.register(r'reminders', TestReminderViewSet, basename='reminders')
router.register(r'reminder-templates', ReminderTemplateViewSet, basename='reminder-templates')
router.register(r'categories', TimelineEventCategoryViewSet, basename='categories')
router.register(r'preferences', PatientTimelinePreferenceViewSet, basename='preferences')

urlpatterns = [
    path('api/', include(router.urls)),
    path('patient/<int:patient_id>/timeline/', patient_timeline_view, name='patient_timeline'),
    path('dashboard/', timeline_dashboard_view, name='timeline_dashboard'),
]