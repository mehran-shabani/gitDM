import json
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError

from <APP_NAME>.models import Service


class Command(BaseCommand):
    help = "Seed initial Service objects from a JSON file"

    def add_arguments(self, parser):  # type: ignore[override]
        parser.add_argument("--file", type=str, default=None, help="Path to services.json")

    def handle(self, *args, **options):  # type: ignore[override]
        import os

        file_path = options.get("file") or os.getenv("SERVICES_JSON") or "services.json"
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"File not found: {file_path}")
        with path.open("r", encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)
        created = 0
        for item in data:
            svc, was_created = Service.objects.update_or_create(
                name=item["name"],
                defaults={
                    "base_url": item["base_url"],
                    "health_path": item.get("health_path", "/health"),
                    "method": item.get("method", "GET"),
                    "headers": item.get("headers", {}),
                    "timeout_s": item.get("timeout_s", 5),
                    "enabled": item.get("enabled", True),
                },
            )
            created += 1 if was_created else 0
        self.stdout.write(self.style.SUCCESS(f"Seed completed. Created: {created}, total: {Service.objects.count()}"))

