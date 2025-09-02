from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference

User = get_user_model()


class NotificationService:
    """
    Service for creating and managing notifications.
    """
    
    @staticmethod
    def create_notification(
        user: User,
        notification_type: str,
        title: str,
        message: str,
        priority: str = 'MEDIUM',
        related_object_type: str = '',
        related_object_id: str = ''
    ) -> Notification:
        """
        Create a new notification for a user.
        """
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            related_object_type=related_object_type,
            related_object_id=related_object_id
        )
        
        # TODO: Send notification through configured channels (email, SMS, push)
        # This would integrate with email service, SMS provider, etc.
        
        return notification
    
    @staticmethod
    def check_lab_result_critical(lab_result) -> Optional[Dict[str, Any]]:
        """
        Check if a lab result has critical values and return notification data.
        """
        critical_notifications = []
        
        # Define critical thresholds
        critical_thresholds = {
            'glucose': {'min': 70, 'max': 250, 'unit': 'mg/dL'},
            'hba1c': {'max': 9.0, 'unit': '%'},
            'cholesterol': {'max': 240, 'unit': 'mg/dL'},
            'ldl': {'max': 160, 'unit': 'mg/dL'},
            'blood_pressure_systolic': {'max': 180, 'unit': 'mmHg'},
            'blood_pressure_diastolic': {'max': 120, 'unit': 'mmHg'},
        }
        
        # Check if any values are critical
        for test_name, thresholds in critical_thresholds.items():
            value = getattr(lab_result, test_name, None)
            if value is not None:
                is_critical = False
                message_parts = []
                
                if 'min' in thresholds and value < thresholds['min']:
                    is_critical = True
                    message_parts.append(f"critically low ({value} {thresholds['unit']})")
                elif 'max' in thresholds and value > thresholds['max']:
                    is_critical = True
                    message_parts.append(f"critically high ({value} {thresholds['unit']})")
                
                if is_critical:
                    critical_notifications.append({
                        'test_name': test_name.replace('_', ' ').title(),
                        'value': value,
                        'unit': thresholds['unit'],
                        'message': ' '.join(message_parts)
                    })
        
        return critical_notifications if critical_notifications else None
    
    @staticmethod
    def notify_critical_lab_result(lab_result):
        """
        Send notification for critical lab results.
        """
        critical_values = NotificationService.check_lab_result_critical(lab_result)
        
        if not critical_values:
            return None
        
        # Get the doctor (primary_doctor of the patient)
        doctor = lab_result.patient.primary_doctor
        if not doctor:
            return None
        
        # Check notification preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=doctor)
        if not prefs.critical_lab_alerts:
            return None
        
        # Create notification
        critical_tests = ', '.join([cv['test_name'] for cv in critical_values])
        title = f"Critical Lab Results for {lab_result.patient.full_name}"
        
        message_lines = [
            f"Patient: {lab_result.patient.full_name}",
            f"Lab taken on: {lab_result.taken_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "Critical values:"
        ]
        
        for cv in critical_values:
            message_lines.append(
                f"- {cv['test_name']}: {cv['value']} {cv['unit']} ({cv['message']})"
            )
        
        message = '\n'.join(message_lines)
        
        notification = NotificationService.create_notification(
            user=doctor,
            notification_type=Notification.NotificationType.CRITICAL_LAB_RESULT,
            title=title,
            message=message,
            priority=Notification.Priority.CRITICAL,
            related_object_type='laboratory.LabResult',
            related_object_id=str(lab_result.id)
        )
        
        return notification
    
    @staticmethod
    def notify_blood_sugar_alert(patient, glucose_value: float, is_high: bool = True):
        """
        Send notification for abnormal blood sugar levels.
        """
        doctor = patient.primary_doctor
        if not doctor:
            return None
        
        # Check preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=doctor)
        if not prefs.blood_sugar_alerts:
            return None
        
        # Check thresholds
        if is_high and glucose_value < prefs.high_blood_sugar_threshold:
            return None
        elif not is_high and glucose_value > prefs.low_blood_sugar_threshold:
            return None
        
        # Create notification
        alert_type = "High" if is_high else "Low"
        notification_type = (
            Notification.NotificationType.HIGH_BLOOD_SUGAR if is_high 
            else Notification.NotificationType.LOW_BLOOD_SUGAR
        )
        
        title = f"{alert_type} Blood Sugar Alert - {patient.full_name}"
        message = (
            f"Patient {patient.full_name} has recorded a {alert_type.lower()} "
            f"blood sugar level of {glucose_value} mg/dL. "
            f"Please review and take appropriate action."
        )
        
        notification = NotificationService.create_notification(
            user=doctor,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=Notification.Priority.HIGH,
            related_object_type='gitdm.PatientProfile',
            related_object_id=str(patient.id)
        )
        
        return notification