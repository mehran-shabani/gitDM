from django.apps import AppConfig

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class DiabMedicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diab_medications'
    verbose_name = _('Diabetes Medications')