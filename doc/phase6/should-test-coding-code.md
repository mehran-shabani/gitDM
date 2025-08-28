# تست‌های الزامی – Clinical References

## tests/test_refs.py
import pytest
from clinical_refs.models import ClinicalReference
from django.core.management import call_command

@pytest.mark.django_db
def test_seeding_refs():
    call_command('seed_refs_diabetes')
    assert ClinicalReference.objects.filter(source='ADA', year=2025).count() >= 2

## tests/test_ai_links_refs.py
import pytest
from ai_summarizer.services import link_references
from clinical_refs.models import ClinicalReference

@pytest.mark.django_db
def test_link_references_basic():
    ClinicalReference.objects.create(title='ADA 2025 – Glycemic', source='ADA', year=2025, url='u', topic='diabetes', section='glycemic')
    s = 'بیمار با HbA1c بالا، درمان با متفورمین'
    linked = link_references(s, 'diabetes')
    assert len(linked) >= 1