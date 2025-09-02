from django.db.models.signals import post_save
from django.dispatch import receiver
from laboratory.models import LabResult
from .services import NotificationService


@receiver(post_save, sender=LabResult)
def check_critical_lab_values(sender, instance, created, **kwargs):
    """
    Check for critical lab values when a new lab result is created.
    """
    if created:
        # Check and notify for critical values
        NotificationService.notify_critical_lab_result(instance)