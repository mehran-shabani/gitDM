from __future__ import annotations

# Initialize Celery app when Django starts
from .celery import app as celery_app  # noqa: F401

__all__ = ["celery_app"]

