from django.apps import AppConfig

class DiabLabsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diab_labs'
    verbose_name = 'Diabetes Labs'
    # فقط وقتی diab_labs/signals.py داری:
    # def ready(self):
    #     import diab_labs.signals  # noqa: F401