import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes'):
        # Only use a default key in DEBUG mode for development
        SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production'
    else:
        raise ImproperlyConfigured(
            "The SECRET_KEY setting must not be empty in production."
        )
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# ALLOWED_HOSTS configuration
ALLOWED_HOSTS_ENV = os.getenv('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',')]
else:
    if DEBUG:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
    else:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be set in production."
        )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    # 'minio_storage',  # removed to simplify; not required for core functionality
    'security',
    'api',
    'patients_core',
    'diab_encounters',
    'diab_labs',
    'diab_medications',
    'records_versioning',
    'ai_summarizer',
    'clinical_refs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'security.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

USE_SQLITE = os.getenv('USE_SQLITE', 'True' if DEBUG else 'False').lower() in ('true','1','yes')
if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'diabetes'),
            'USER': os.getenv('POSTGRES_USER', 'diabetes'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'diabetes'),
            'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API schema settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Diabetes Pilot API',
    'DESCRIPTION': 'API for Diabetes Management System. Authentication required for all endpoints. '
                   'Users are created exclusively through Django admin panel - no public registration available.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
}

# No system user fallback; enforce authenticated actions
SYSTEM_USER_ID = None

# Optional Redis; default to local memory cache when not provided
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Use default Django file storage

# Omit Celery by default; enable via env in deployments if needed

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'