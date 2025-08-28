from django.core.management.base import BaseCommand
from clinical_refs.models import ClinicalReference

ADA = [
    {
        "title": "ADA Standards of Care 2025 – Glycemic Targets",
        "source": "ADA",
        "year": 2025,
        "url": "https://example.org/ada/2025/glycemic-targets",
        "topic": "diabetes",
        "section": "glycemic-targets",
        "lang": "en",
        "tags": ["hba1c","targets","type2"],
    },
    {
        "title": "ADA Standards of Care 2025 – Pharmacologic Therapy",
        "source": "ADA",
        "year": 2025,
        "url": "https://example.org/ada/2025/pharmacologic-therapy",
        "topic": "diabetes",
        "section": "therapy",
        "lang": "en",
        "tags": ["metformin","sglt2","glp1"],
    },
]

class Command(BaseCommand):
    help = "Seed ADA 2025 clinical references for diabetes"

    def handle(self, *args, **options):
        created = 0
        for r in ADA:
            obj, is_created = ClinicalReference.objects.get_or_create(
                title=r["title"],
                defaults=r,
            )
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} ADA refs."))