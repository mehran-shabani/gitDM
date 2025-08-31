from django.apps import AppConfig
import os

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    # Provide path for tests that instantiate AppConfig without registry
    path = os.path.dirname(os.path.abspath(__file__))