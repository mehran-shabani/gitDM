from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    Model for storing notifications for users about critical events.
    """
    class NotificationType(models.TextChoices):
        CRITICAL_LAB_RESULT = 'CRITICAL_LAB', 'Critical Lab Result'
        HIGH_BLOOD_SUGAR = 'HIGH_SUGAR', 'High Blood Sugar Alert'
        LOW_BLOOD_SUGAR = 'LOW_SUGAR', 'Low Blood Sugar Alert'
        MEDICATION_REMINDER = 'MED_REMINDER', 'Medication Reminder'
        APPOINTMENT_REMINDER = 'APPT_REMINDER', 'Appointment Reminder'
        SYSTEM = 'SYSTEM', 'System Notification'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'
    
    # Core fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related object (generic relation)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=50, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority', 'is_sent']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user}"
    
    def mark_as_read(self):
        """Mark notification as read with timestamp."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self):
        """Mark notification as sent with timestamp."""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """
    User preferences for notifications.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Notification channels
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    
    # Notification types preferences
    critical_lab_alerts = models.BooleanField(default=True)
    blood_sugar_alerts = models.BooleanField(default=True)
    medication_reminders = models.BooleanField(default=True)
    appointment_reminders = models.BooleanField(default=True)
    
    # Thresholds for alerts
    high_blood_sugar_threshold = models.IntegerField(
        default=250,  # mg/dL
        help_text="Blood sugar level above which to send alert"
    )
    low_blood_sugar_threshold = models.IntegerField(
        default=70,   # mg/dL
        help_text="Blood sugar level below which to send alert"
    )
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Notification preferences for {self.user}"