from django.apps import AppConfig
import os
import types


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    # Provide path for tests that instantiate AppConfig without registry
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, app_name, app_module):  # type: ignore[override]
        if not isinstance(app_name, str) or not app_name:
            raise TypeError('app_name must be non-empty str')
        if not isinstance(app_module, types.ModuleType):
            raise TypeError('app_module must be a module object')
        super().__init__(app_name, app_module)