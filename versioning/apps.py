from django.apps import AppConfig


class VersioningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'versioning'

    def ready(self) -> None:
        """Lazy import signals to register handlers after app is ready."""
        from . import signals  # noqa: F401
