from django.db.models.signals import post_save
from django.dispatch import receiver
from laboratory.models import LabResult
from encounters.models import Encounter
from .tasks import run_anomaly_detection_for_new_lab, run_pattern_analysis_for_patient
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=LabResult)
def trigger_anomaly_detection_on_new_lab(sender, instance, created, **kwargs):
    """
    تشخیص ناهنجاری خودکار هنگام ثبت نتیجه آزمایش جدید
    """
    if created:
        try:
            # تشخیص ناهنجاری برای نتیجه آزمایش جدید
            run_anomaly_detection_for_new_lab.delay(instance.id)
            logger.info(f"Anomaly detection scheduled for new lab result {instance.id}")
        except Exception as e:
            logger.error(f"Failed to schedule anomaly detection for lab {instance.id}: {e}")


@receiver(post_save, sender=Encounter)
def trigger_pattern_analysis_on_encounter(sender, instance, created, **kwargs):
    """
    تحلیل الگو هنگام ثبت مواجهه جدید
    """
    if created:
        try:
            # تحلیل الگوهای رفتاری پس از مواجهه جدید
            run_pattern_analysis_for_patient.delay(
                patient_id=instance.patient.id,
                pattern_types=['MEDICATION_ADHERENCE', 'VISIT_FREQ'],
                months_back=3
            )
            logger.info(f"Pattern analysis scheduled for patient {instance.patient.id} after new encounter")
        except Exception as e:
            logger.error(f"Failed to schedule pattern analysis for encounter {instance.id}: {e}")