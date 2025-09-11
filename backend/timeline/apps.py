from django.apps import AppConfig


class TimelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timeline'
    verbose_name = 'Medical Timeline'
    
    def ready(self):
        import timeline.signals