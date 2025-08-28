from django.apps import AppConfig

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AiSummarizerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_summarizer'
    verbose_name = _('AI Summarizer')
