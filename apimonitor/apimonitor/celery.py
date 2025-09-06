import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apimonitor.settings')

app = Celery('apimonitor')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Hardening / QoL
app.conf.broker_connection_retry_on_startup = True
app.conf.worker_hijack_root_logger = False
app.conf.timezone = getattr(settings, 'TIME_ZONE', 'UTC')
