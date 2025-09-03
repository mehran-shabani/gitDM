from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apimonitor.settings")

app = Celery("apimonitor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


def _get_health_cron() -> str:
    from environs import Env

    env = Env()
    env.read_env()
    return env.str("HEALTH_INTERVAL_CRON", "*/5 * * * *")


# Configure beat schedule
minute, hour, day_of_month, month_of_year, day_of_week = _get_health_cron().split()

app.conf.beat_schedule = {
    "run-health-checks": {
        "task": "<APP_NAME>.tasks.run_health_checks",
        "schedule": crontab(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
        ),
    },
    "daily-analyze-logs": {
        "task": "<APP_NAME>.tasks.analyze_logs",
        "schedule": crontab(minute=0, hour=2),
        "args": (24,),
    },
}

