import logging
from typing import List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification, ClinicalAlert

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    سرویس مدیریت اطلاع‌رسانی
    """
    
    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.INFO,
        priority: str = Notification.Priority.MEDIUM,
        patient_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        expires_at: Optional[timezone.datetime] = None
    ) -> Notification:
        """
        ایجاد اطلاع‌رسانی جدید
        """
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expires_at=expires_at
        )
    
    @staticmethod
    def notify_patient_created(patient, doctor):
        """
        اطلاع‌رسانی ایجاد بیمار جدید
        """
        return NotificationService.create_notification(
            recipient=doctor,
            title="بیمار جدید ثبت شد",
            message=f"بیمار {patient.full_name} با موفقیت در سیستم ثبت شد.",
            notification_type=Notification.NotificationType.INFO,
            patient_id=str(patient.id),
            resource_type='patient',
            resource_id=str(patient.id)
        )
    
    @staticmethod
    def notify_abnormal_lab_result(lab_result, doctor):
        """
        اطلاع‌رسانی نتیجه آزمایش غیرطبیعی
        """
        return NotificationService.create_notification(
            recipient=doctor,
            title="نتیجه آزمایش غیرطبیعی",
            message=f"نتیجه آزمایش {lab_result.loinc} برای بیمار {lab_result.patient.full_name} خارج از محدوده طبیعی است: {lab_result.value} {lab_result.unit}",
            notification_type=Notification.NotificationType.WARNING,
            priority=Notification.Priority.HIGH,
            patient_id=str(lab_result.patient.id),
            resource_type='lab_result',
            resource_id=str(lab_result.id)
        )
    
    @staticmethod
    def notify_ai_summary_ready(ai_summary, doctor):
        """
        اطلاع‌رسانی آماده شدن خلاصه AI
        """
        return NotificationService.create_notification(
            recipient=doctor,
            title="خلاصه هوشمند آماده شد",
            message=f"خلاصه هوشمند برای بیمار {ai_summary.patient.full_name} تولید شد.",
            notification_type=Notification.NotificationType.AI_SUMMARY,
            patient_id=str(ai_summary.patient.id),
            resource_type='ai_summary',
            resource_id=str(ai_summary.id)
        )


class ClinicalAlertService:
    """
    سرویس مدیریت هشدارهای بالینی
    """
    
    @staticmethod
    def check_hba1c_alert(lab_result):
        """
        بررسی نیاز به هشدار برای HbA1c
        """
        if lab_result.loinc not in ['4548-4', '17856-6']:
            return None
        
        hba1c_value = float(lab_result.value)
        
        # HbA1c > 9% = بحرانی
        if hba1c_value > 9.0:
            severity = 'CRITICAL'
            message = f"HbA1c بسیار بالا: {hba1c_value}% - نیاز به مداخله فوری"
        # HbA1c > 7% = بالا
        elif hba1c_value > 7.0:
            severity = 'HIGH'
            message = f"HbA1c بالا: {hba1c_value}% - نیاز به بازنگری درمان"
        else:
            return None
        
        return ClinicalAlert.objects.create(
            patient=lab_result.patient,
            alert_type=ClinicalAlert.AlertType.HIGH_HBA1C,
            severity=severity,
            trigger_value=hba1c_value,
            threshold_value=7.0,
            message=message
        )
    
    @staticmethod
    def check_glucose_alerts(lab_result):
        """
        بررسی نیاز به هشدار برای قند خون
        """
        if lab_result.loinc not in ['2345-7', '2339-0', '1558-6']:
            return None
        
        glucose_value = float(lab_result.value)
        alerts = []
        
        # قند خون پایین
        if glucose_value < 70:
            severity = 'CRITICAL' if glucose_value < 50 else 'HIGH'
            alert = ClinicalAlert.objects.create(
                patient=lab_result.patient,
                alert_type=ClinicalAlert.AlertType.LOW_GLUCOSE,
                severity=severity,
                trigger_value=glucose_value,
                threshold_value=70.0,
                message=f"قند خون پایین: {glucose_value} mg/dL - خطر هیپوگلیسمی"
            )
            alerts.append(alert)
        
        # قند خون بالا
        elif glucose_value > 200:
            severity = 'CRITICAL' if glucose_value > 400 else 'HIGH'
            alert = ClinicalAlert.objects.create(
                patient=lab_result.patient,
                alert_type=ClinicalAlert.AlertType.HIGH_GLUCOSE,
                severity=severity,
                trigger_value=glucose_value,
                threshold_value=200.0,
                message=f"قند خون بالا: {glucose_value} mg/dL - نیاز به کنترل"
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def check_drug_interactions(medication_order):
        """
        بررسی تداخل دارویی (پیاده‌سازی ساده)
        """
        # دریافت سایر داروهای فعال بیمار
        active_meds = medication_order.patient.medication_orders.filter(
            end_date__isnull=True
        ).exclude(id=medication_order.id)
        
        # لیست تداخل‌های شناخته شده (نمونه)
        known_interactions = {
            'A10BA02': ['C03CA01'],  # Metformin + Furosemide
            'A10AB01': ['C07AB02'],  # Insulin + Metoprolol
        }
        
        new_atc = medication_order.atc
        if new_atc in known_interactions:
            for med in active_meds:
                if med.atc in known_interactions[new_atc]:
                    return ClinicalAlert.objects.create(
                        patient=medication_order.patient,
                        alert_type=ClinicalAlert.AlertType.DRUG_INTERACTION,
                        severity='HIGH',
                        message=f"تداخل دارویی احتمالی بین {medication_order.name} و {med.name}"
                    )
        
        return None
    
    @staticmethod
    def create_test_reminder_notification(test_reminder):
        """
        ایجاد اطلاع‌رسانی برای یادآوری آزمایش
        """
        days_until_due = test_reminder.days_until_due()
        
        if days_until_due < 0:
            # عقب‌افتاده
            title = f"یادآوری عقب‌افتاده: {test_reminder.get_test_type_display()}"
            message = f"آزمایش {test_reminder.get_test_type_display()} برای بیمار {test_reminder.patient.full_name} {abs(days_until_due)} روز عقب‌افتاده است."
            notification_type = Notification.NotificationType.CRITICAL
            priority = Notification.Priority.URGENT
        elif days_until_due <= test_reminder.reminder_days_before:
            # نزدیک به سررسید
            title = f"یادآوری آزمایش: {test_reminder.get_test_type_display()}"
            message = f"آزمایش {test_reminder.get_test_type_display()} برای بیمار {test_reminder.patient.full_name} در {days_until_due} روز آینده سررسید دارد."
            notification_type = Notification.NotificationType.REMINDER
            priority = Notification.Priority.MEDIUM
        else:
            return None
        
        # ایجاد notification برای پزشک معالج
        if test_reminder.patient.primary_doctor:
            return Notification.objects.create(
                recipient=test_reminder.patient.primary_doctor,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                patient_id=str(test_reminder.patient.id),
                resource_type='test_reminder',
                resource_id=str(test_reminder.id)
            )
        
        return None
    
    @staticmethod
    def create_test_completion_notification(test_reminder, performed_date):
        """
        ایجاد اطلاع‌رسانی برای تکمیل آزمایش
        """
        title = f"آزمایش انجام شد: {test_reminder.get_test_type_display()}"
        message = f"آزمایش {test_reminder.get_test_type_display()} برای بیمار {test_reminder.patient.full_name} در تاریخ {performed_date.strftime('%Y/%m/%d')} انجام شد. تاریخ سررسید بعدی: {test_reminder.next_due.strftime('%Y/%m/%d')}"
        
        # ایجاد notification برای پزشک معالج
        if test_reminder.patient.primary_doctor:
            return Notification.objects.create(
                recipient=test_reminder.patient.primary_doctor,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.INFO,
                priority=Notification.Priority.LOW,
                patient_id=str(test_reminder.patient.id),
                resource_type='test_completion',
                resource_id=str(test_reminder.id)
            )
        
        return None