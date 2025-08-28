from django.apps import AppConfig

# File: diab_encounters/apps.py

from django.apps import AppConfig

class DiabEncountersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diab_encounters'
    verbose_name = 'Diabetes Encounters'
    # def ready(self):
    #     import diab_encounters.signals  # noqa: F401