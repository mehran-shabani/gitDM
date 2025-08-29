from django.core.management.base import BaseCommand
from django.db import transaction
from typing import Any
from clinical_refs.models import ClinicalReference

ADA = [
    {
        "title": "ADA Standards of Care 2025 - Glycemic Targets",
        "source": "ADA",
        "year": 2025,
        "url": "https://diabetesjournals.org/care/article/48/Supplement_1/S1/153797/Standards-of-Care-in-Diabetes-2025",
        "topic": "diabetes",
        "section": "glycemic-targets",
        "lang": "en",
        "tags": ["hba1c","targets","type2"],
    },
    {
        "title": "ADA Standards of Care 2025 - Pharmacologic Therapy",
        "source": "ADA",
        "year": 2025,
        "url": "https://diabetesjournals.org/care/article/48/Supplement_1/S1/153797/Standards-of-Care-in-Diabetes-2025",
        "topic": "diabetes",
        "section": "therapy",
        "lang": "en",
        "tags": ["metformin","sglt2","glp1"],
    },
]

class Command(BaseCommand):
    help = "Seed ADA 2025 clinical references for diabetes"

    def handle(self, *args: Any, **options: dict[str, Any]) -> None:
        created = 0
        updated = 0
        with transaction.atomic():
            for r in ADA:
                obj, is_created = ClinicalReference.objects.update_or_create(
                    title=r["title"],
                    source=r["source"],
                    year=r["year"],
                    defaults={
                        "url": r["url"],
                        "topic": r["topic"],
                    },
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Seeded ADA refs — created={created}, updated={updated}")
        )