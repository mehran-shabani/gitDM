# کدهای الزامی – Clinical References

## clinical_refs/models.py (به‌روزرسانی)
from django.db import models
import uuid

class ClinicalReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=120)  # ADA, WHO, IDF, ESC, ...
    year = models.PositiveIntegerField()
    url = models.URLField(blank=True)
    topic = models.CharField(max_length=80)    # diabetes, hba1c, therapy, renal
    section = models.CharField(max_length=160, blank=True)  # e.g., "Glycemic Targets"
    lang = models.CharField(max_length=8, default='en')
    tags = models.JSONField(default=list, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["topic","year","source"]),
        ]

## ai_summarizer/models.py (به‌روزرسانی)
from django.db import models
import uuid

class AISummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients_core.Patient', on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    references = models.ManyToManyField('clinical_refs.ClinicalReference', blank=True)

## clinical_refs/admin.py (جدید)
from django.contrib import admin
from .models import ClinicalReference

@admin.register(ClinicalReference)
class ClinicalReferenceAdmin(admin.ModelAdmin):
    list_display = ("title","source","year","topic","section","lang")
    list_filter = ("source","year","topic","lang")
    search_fields = ("title","topic","section")

## clinical_refs/management/commands/seed_refs_diabetes.py (جدید)
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

## api/views.py (به‌روزرسانی – فیلتر برای refs)
from rest_framework import filters

class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','topic','section','source']

    def get_queryset(self):
        qs = super().get_queryset()
        topic = self.request.query_params.get('topic')
        year = self.request.query_params.get('year')
        source = self.request.query_params.get('source')
        q = self.request.query_params.get('q')
        if topic:
            qs = qs.filter(topic__icontains=topic)
        if year:
            qs = qs.filter(year=year)
        if source:
            qs = qs.filter(source__icontains=source)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

## ai_summarizer/services.py (جدید – لینک خودکار به رفرنس)
from clinical_refs.models import ClinicalReference

TOPIC_KEYWORDS = {
    'diabetes': ['diabetes','hba1c','metformin','insulin','sglt2','glp-1'],
}

def link_references(summary_text, topic_hint='diabetes'):
    qs = ClinicalReference.objects.filter(topic__icontains=topic_hint)
    selected = []
    text_lower = summary_text.lower()
    for ref in qs[:20]:
        score = 0
        for kw in TOPIC_KEYWORDS.get(topic_hint, []):
            if kw in text_lower:
                score += 1
        if score:
            selected.append(ref)
    return selected[:3]

## ai_summarizer/tasks.py (به‌روزرسانی – افزودن لینک refs)
from ai_summarizer.services import link_references
# ... در انتهای summarize_record پس از ایجاد AISummary ...
        refs = link_references(text, topic_hint='diabetes')
        for r in refs:
            summary.references.add(r)
        return summary.id