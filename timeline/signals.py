from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from encounters.models import Encounter
from laboratory.models import LabResult
from .models import MedicalTimeline
from .services import TimelineService, ReminderService


@receiver(post_save, sender=Encounter)
def create_timeline_event_from_encounter(sender, instance, created, **kwargs):
    """
    ایجاد خودکار رویداد تایم‌لاین هنگام ثبت مواجهه جدید
    """
    if created:
        TimelineService.create_timeline_event_from_encounter(instance)


@receiver(post_save, sender=LabResult)
def create_timeline_event_from_lab_result(sender, instance, created, **kwargs):
    """
    ایجاد خودکار رویداد تایم‌لاین هنگام ثبت نتیجه آزمایش جدید
    """
    if created:
        # ایجاد رویداد تایم‌لاین
        TimelineService.create_timeline_event_from_lab_result(instance)
        
        # به‌روزرسانی یادآوری مربوطه (در صورت وجود)
        ReminderService.update_reminder_from_lab_result(instance)


@receiver(post_delete, sender=Encounter)
def hide_timeline_event_on_encounter_delete(sender, instance, **kwargs):
    """
    مخفی کردن رویداد تایم‌لاین هنگام حذف مواجهه
    """
    try:
        timeline_event = MedicalTimeline.objects.get(
            content_type__model='encounter',
            object_id=instance.id
        )
        timeline_event.is_visible = False
        timeline_event.save(update_fields=['is_visible'])
    except MedicalTimeline.DoesNotExist:
        pass


@receiver(post_delete, sender=LabResult)
def hide_timeline_event_on_lab_result_delete(sender, instance, **kwargs):
    """
    مخفی کردن رویداد تایم‌لاین هنگام حذف نتیجه آزمایش
    """
    try:
        timeline_event = MedicalTimeline.objects.get(
            content_type__model='labresult',
            object_id=instance.id
        )
        timeline_event.is_visible = False
        timeline_event.save(update_fields=['is_visible'])
    except MedicalTimeline.DoesNotExist:
        pass