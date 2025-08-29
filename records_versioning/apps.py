from django.apps import AppConfig

class RecordsVersioningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'records_versioning'

    def ready(self) -> None:
        """Lazy import signals to register handlers after app is ready."""
        from . import signals  # noqa: F401