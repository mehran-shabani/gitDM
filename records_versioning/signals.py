from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .services import save_with_version, _thread_state

User = get_user_model()


def _create_version_on_save(instance: object) -> None:
    """
    Helper function to create a new version for a model instance when it is saved.
    It attempts to determine the user responsible for the change from various fields
    (created_by_id, updated_by_id, primary_doctor_id) or falls back to a system user.
    """
    # Check if we're already in a versioning operation
    if getattr(_thread_state, 'in_version', False):
        return
    
    # Try to get the user from various sources (optimized to avoid DB hits)
    user = None
    
    # Check for user IDs first to avoid unnecessary DB queries
    user_id = (
        getattr(instance, 'created_by_id', None) or
        getattr(instance, 'updated_by_id', None) or
        getattr(instance, 'primary_doctor_id', None)
    )
    
    if user_id:
        user = User.objects.filter(id=user_id).first()
    
    # No system user needed - versioning will work with user=None
    
    save_with_version(instance, user, reason='auto-signal')


# Patient signal
@receiver(post_save, sender='patients_core.Patient')
def patient_saved(sender: object, instance: object, created: bool, **kwargs: object) -> None:
    """Signal receiver for post_save on Patient model to create a version."""
    _create_version_on_save(instance)


# Encounter signal
@receiver(post_save, sender='diab_encounters.Encounter')
def encounter_saved(sender: object, instance: object, created: bool, **kwargs: object) -> None:
    """Signal receiver for post_save on Encounter model to create a version."""
    _create_version_on_save(instance)


# LabResult signal
@receiver(post_save, sender='diab_labs.LabResult')
def lab_result_saved(sender: object, instance: object, created: bool, **kwargs: object) -> None:
    """Signal receiver for post_save on LabResult model to create a version."""
    _create_version_on_save(instance)


# MedicationOrder signal
@receiver(post_save, sender='diab_medications.MedicationOrder')
def medication_order_saved(sender: object, instance: object, created: bool, **kwargs: object) -> None:
    """Signal receiver for post_save on MedicationOrder model to create a version."""
    _create_version_on_save(instance)