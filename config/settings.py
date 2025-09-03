import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------
# Security
# ------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes'):
        SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production'
    else:
        raise ImproperlyConfigured("SECRET_KEY is required in production.")

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS_ENV = os.getenv('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',')] if ALLOWED_HOSTS_ENV else ['localhost', '127.0.0.1']  # noqa: E501

# GitHub Codespaces specific settings
if os.getenv('CODESPACES', 'false').lower() == 'true':
    ALLOWED_HOSTS.extend([
        f"{os.getenv('CODESPACE_NAME')}-8000.{os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')}",
        'localhost',
        '127.0.0.1',
        '[::1]',
    ])
    CSRF_TRUSTED_ORIGINS = [
        f"https://{os.getenv('CODESPACE_NAME')}-8000.{os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')}",
    ]
    # Force debug in codespaces for development
    DEBUG = True

# ------------------------
# Installed Apps
# ------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_celery_beat',

    # Your apps
    'gitdm',
    'intelligence',
    'references',
    'encounters',
    'laboratory',
    'pharmacy',
    'versioning',
    'security',
    'notifications',
    'gateway',
    'timeline',

]

# ------------------------
# Middleware
# ------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'security.middleware.SecurityMiddleware',
    'security.middleware.AuditLoggingMiddleware',
]

# ------------------------
# URL/WSGI/ASGI
# ------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ------------------------
# Templates
# ------------------------
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ------------------------
# Database
# ------------------------
# Using SQLite for GitHub Codespaces
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ------------------------
# Cache - Django Default
# ------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ------------------------
# Celery - Disabled for Codespaces
# ------------------------
# Celery is disabled in Codespaces environment
# To enable Celery, you need to set up a message broker

# ------------------------
# REST Framework
# ------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'Description here.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ------------------------
# JWT
# ------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=20),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ------------------------
# Static and Media Files - Django Default
# ------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------------
# AI Summarization
# ------------------------
GAPGPT_API_KEY = os.getenv('GAPGPT_API_KEY')
GAPGPT_BASE_URL = os.getenv('GAPGPT_BASE_URL', 'https://api.gapgpt.app/v1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

AI_SUMMARIZER_SETTINGS = {
    'MODEL': os.getenv('AI_MODEL', 'gpt-4o'),
    'MAX_TOKENS': int(os.getenv('AI_MAX_TOKENS', '1000')),
    'TEMPERATURE': float(os.getenv('AI_TEMPERATURE', '0.3')),
    'USE_GAPGPT': os.getenv('USE_GAPGPT', 'True').lower() in ('true', '1', 'yes'),
    'SYSTEM_PROMPT': """You are a medical AI assistant specialized in creating concise, accurate summaries of patient medical data.
Focus on key clinical information, diagnoses, medications, and important findings.
Keep summaries professional, clear, and relevant for healthcare providers."""  # noqa: E501
}

# ------------------------
# Internationalization
# ------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'gitdm.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # پیش‌فرض
]
