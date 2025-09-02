from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from gitdm.models import PatientProfile
from laboratory.models import LabResult
from pharmacy.models import MedicationOrder
from intelligence.models import AISummary
from .services import NotificationService, ClinicalAlertService

User = get_user_model()


@receiver(post_save, sender=PatientProfile)
def patient_created_notification(sender, instance, created, **kwargs):
    """
    ارسال اطلاع‌رسانی هنگام ایجاد بیمار جدید
    """
    if created and instance.primary_doctor:
        NotificationService.notify_patient_created(instance, instance.primary_doctor)


@receiver(post_save, sender=LabResult)
def lab_result_alerts(sender, instance, created, **kwargs):
    """
    بررسی و ایجاد هشدارهای بالینی برای نتایج آزمایش
    """
    if created:
        # بررسی HbA1c
        hba1c_alert = ClinicalAlertService.check_hba1c_alert(instance)
        
        # بررسی قند خون
        glucose_alerts = ClinicalAlertService.check_glucose_alerts(instance)
        
        # ارسال notification به پزشک در صورت وجود هشدار
        if hba1c_alert or glucose_alerts:
            if instance.patient.primary_doctor:
                NotificationService.notify_abnormal_lab_result(
                    instance, 
                    instance.patient.primary_doctor
                )


@receiver(post_save, sender=MedicationOrder)
def medication_interaction_check(sender, instance, created, **kwargs):
    """
    بررسی تداخل دارویی هنگام تجویز دارو
    """
    if created:
        interaction_alert = ClinicalAlertService.check_drug_interactions(instance)
        
        if interaction_alert and instance.patient.primary_doctor:
            NotificationService.create_notification(
                recipient=instance.patient.primary_doctor,
                title="هشدار تداخل دارویی",
                message=interaction_alert.message,
                notification_type=NotificationService.Notification.NotificationType.WARNING,
                priority=NotificationService.Notification.Priority.HIGH,
                patient_id=str(instance.patient.id)
            )


@receiver(post_save, sender=AISummary)
def ai_summary_notification(sender, instance, created, **kwargs):
    """
    اطلاع‌رسانی آماده شدن خلاصه AI
    """
    if created and instance.patient.primary_doctor:
        NotificationService.notify_ai_summary_ready(instance, instance.patient.primary_doctor)