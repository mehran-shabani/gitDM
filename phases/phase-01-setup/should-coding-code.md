# کدهای الزامی (Setup)

## requirements.txt
Django>=5.0
djangorestframework>=3.15
psycopg2-binary>=2.9
python-dotenv>=1.0
djangorestframework-simplejwt>=5.3
celery>=5.4
redis>=5.0
minio>=7.2
boto3>=1.34
django-storages>=1.14
drf-spectacular>=0.27
uvicorn>=0.30

## docker-compose.yml
version: '3.9'
services:
  web:
    build: .
    command: uvicorn config.asgi:application --host 0.0.0.0 --port 8000
    env_file: .env
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
      - minio
  worker:
    build: .
    command: celery -A config.celery_app worker -l info
    env_file: .env
    volumes:
      - ./:/app
    depends_on:
      - db
      - redis
  beat:
    build: .
    command: celery -A config.celery_app beat -l info
    env_file: .env
    volumes:
      - ./:/app
    depends_on:
      - db
      - redis
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: diabetes
      POSTGRES_USER: diabetes
      POSTGRES_PASSWORD: diabetes
    ports:
      - "5432:5432"
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: admin12345
    ports:
      - "9000:9000"
      - "9001:9001"

## Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

## .env نمونه
DJANGO_SECRET_KEY=change_me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
POSTGRES_DB=diabetes
POSTGRES_USER=diabetes
POSTGRES_PASSWORD=diabetes
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
MINIO_BUCKET=diabetes-media
OPENAI_API_KEY=sk-xxxxx

## config/settings.py (گزیده)
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','drf_spectacular',
    'patients_core','diab_encounters','diab_labs','diab_medications','records_versioning','ai_summarizer','clinical_refs',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [],'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']},
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

REDIS_URL = os.getenv('REDIS_URL')

# MinIO (django-storages)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = os.getenv('MINIO_ENDPOINT')
AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('MINIO_BUCKET')
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_SIGNATURE_VERSION = 's3v4'

## config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
celery_app = Celery('config')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

## api/routers.py (حداقل مسیر سلامت)
from django.urls import path
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status":"ok"})

urlpatterns = [path('health/', health)]