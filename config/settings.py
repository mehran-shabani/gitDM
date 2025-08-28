import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'minio_storage',
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

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Diabetes Pilot API',
}

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# MinIO configuration (django-minio-storage)
DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
STATICFILES_STORAGE = 'minio_storage.storage.MinioStaticStorage'

if DEBUG:
    # Development: use getenv with defaults
    MINIO_STORAGE_ENDPOINT = os.getenv('MINIO_STORAGE_ENDPOINT', 'localhost:9000')
    MINIO_STORAGE_ACCESS_KEY = os.getenv('MINIO_STORAGE_ACCESS_KEY', 'minioadmin')
    MINIO_STORAGE_SECRET_KEY = os.getenv('MINIO_STORAGE_SECRET_KEY', 'minioadmin')
    MINIO_STORAGE_MEDIA_BUCKET_NAME = os.getenv('MINIO_STORAGE_MEDIA_BUCKET', 'media')
    MINIO_STORAGE_STATIC_BUCKET_NAME = os.getenv('MINIO_STORAGE_STATIC_BUCKET', 'static')
else:
    # Production: require environment variables
    MINIO_STORAGE_ENDPOINT = os.environ['MINIO_STORAGE_ENDPOINT']
    MINIO_STORAGE_ACCESS_KEY = os.environ['MINIO_STORAGE_ACCESS_KEY']
    MINIO_STORAGE_SECRET_KEY = os.environ['MINIO_STORAGE_SECRET_KEY']
    MINIO_STORAGE_MEDIA_BUCKET_NAME = os.environ['MINIO_STORAGE_MEDIA_BUCKET']
    MINIO_STORAGE_STATIC_BUCKET_NAME = os.environ['MINIO_STORAGE_STATIC_BUCKET']

MINIO_STORAGE_USE_HTTPS = os.getenv('MINIO_STORAGE_USE_HTTPS', 'False').lower() in ('true', '1', 'yes')
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = False
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = False

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

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