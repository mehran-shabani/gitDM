from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .services import save_with_version

User = get_user_model()

def _create_version_on_save(instance):
    """Helper function to create a version when a model instance is saved."""
    # Try to get the user from various sources
    user = None
    
    # Check if instance has created_by or updated_by that are User instances
    if hasattr(instance, 'created_by') and isinstance(instance.created_by, User):
        user = instance.created_by
    elif hasattr(instance, 'updated_by') and isinstance(instance.updated_by, User):
        user = instance.updated_by
    elif hasattr(instance, 'primary_doctor') and isinstance(instance.primary_doctor, User):
        user = instance.primary_doctor
    
    # If no user found, use system user if configured
    if user is None and hasattr(settings, 'SYSTEM_USER_ID'):
        try:
            user = User.objects.get(id=settings.SYSTEM_USER_ID)
        except User.DoesNotExist:
            pass
    
    save_with_version(instance, user, reason='auto-signal')

# Patient signal
@receiver(post_save, sender='patients_core.Patient')
def patient_saved(sender, instance, created, **kwargs):
    _create_version_on_save(instance)

# Encounter signal
@receiver(post_save, sender='diab_encounters.Encounter')
def encounter_saved(sender, instance, created, **kwargs):
    _create_version_on_save(instance)

# LabResult signal
@receiver(post_save, sender='diab_labs.LabResult')
def lab_result_saved(sender, instance, created, **kwargs):
    _create_version_on_save(instance)

# MedicationOrder signal
@receiver(post_save, sender='diab_medications.MedicationOrder')
def medication_order_saved(sender, instance, created, **kwargs):
    _create_version_on_save(instance)