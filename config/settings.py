import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from celery.schedules import crontab

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
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',')] if ALLOWED_HOSTS_ENV else ['localhost', '127.0.0.1']

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

    # Optional
    'storages',

    # Your apps
    'gitdm',
    'intelligence', 
    'references',
    'encounters',
    'laboratory',
    'pharmacy',
    'versioning',
    'security',
    'gateway',
    
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
USE_SQLITE = os.getenv('USE_SQLITE', 'True' if DEBUG else 'False').lower() in ('true', '1', 'yes')

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
            'NAME': os.getenv('POSTGRES_DB', 'appdb'),
            'USER': os.getenv('POSTGRES_USER', 'appuser'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'apppass'),
            'HOST': os.getenv('POSTGRES_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

# ------------------------
# Redis Cache
# ------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB_CACHE = 0

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CACHE}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": REDIS_PASSWORD,
        },
        "KEY_PREFIX": "django",
        "TIMEOUT": 60 * 15,
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ------------------------
# Celery
# ------------------------
REDIS_DB_BROKER = 1
REDIS_DB_RESULT = 2
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BROKER}"
CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_RESULT}"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'

# Celery Beat: Tehran time jobs (UTC +3:30)
CELERY_BEAT_SCHEDULE = {
    'summary_task_22_tehran': {
        'task': 'intelligence.tasks.create_summary_with_references',
        'schedule': crontab(minute=30, hour=18),  # 22:00 Tehran
        'args': [1, "Sample content at 22"]
    },
    'summary_task_2230_tehran': {
        'task': 'intelligence.tasks.create_summary_with_references',
        'schedule': crontab(minute=0, hour=19),  # 22:30 Tehran
        'args': [1, "Sample content at 22:30"]
    },
}

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
# MinIO Storage
# ------------------------
USE_MINIO = os.getenv('USE_MINIO', 'False').lower() in ('true', '1', 'yes')

if USE_MINIO:
    DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
    STATICFILES_STORAGE = 'minio_storage.storage.MinioStaticStorage'

    MINIO_STORAGE_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_STORAGE_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_STORAGE_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    MINIO_STORAGE_MEDIA_BUCKET_NAME = os.getenv('MINIO_MEDIA_BUCKET', 'media')
    MINIO_STORAGE_STATIC_BUCKET_NAME = os.getenv('MINIO_STATIC_BUCKET', 'static')
    MINIO_STORAGE_USE_HTTPS = os.getenv('MINIO_USE_HTTPS', 'False').lower() in ('true', '1', 'yes')
    MINIO_STORAGE_IGNORE_CERT_CHECK = not MINIO_STORAGE_USE_HTTPS
else:
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
Keep summaries professional, clear, and relevant for healthcare providers."""
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
