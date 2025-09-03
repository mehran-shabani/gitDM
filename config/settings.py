import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from celery.schedules import crontab

# Load environment variables
load_dotenv()

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
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',')] if ALLOWED_HOSTS_ENV else ['localhost', '127.0.0.1', 'testserver']  # noqa: E501

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
    'django_filters',

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
    'reminders',
    'gateway',
    'monitor',

    'analytics',

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
# Celery Configuration
# ------------------------

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Beat Schedule for periodic tasks

CELERY_BEAT_SCHEDULE = {
    'run-health-checks': {
        'task': 'monitor.tasks.run_health_checks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'analyze-logs': {
        'task': 'monitor.tasks.analyze_logs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'kwargs': {'period_hours': 24}
    },
}

# ------------------------
# Logging Configuration
# ------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'health_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'health.log',
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'json',
            'encoding': 'utf-8',
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'monitor.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'monitor': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'monitor.health': {
            'handlers': ['console', 'health_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'monitor.tasks': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Ensure logs directory exists
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ------------------------
# Health Monitoring Settings
# ------------------------
HEALTH_INTERVAL_CRON = os.getenv('HEALTH_INTERVAL_CRON', '*/5 * * * *')
SERVICES_JSON = os.getenv('SERVICES_JSON', './services.json')

# ------------------------
# REST Framework
# ------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
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
