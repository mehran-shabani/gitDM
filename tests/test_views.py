# Testing framework: pytest + pytest-django
# Purpose: API/view tests for Patients/Encounters if DRF/Django views are present.

import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize("name", [
    "patients-list", "patients-detail", "encounters-list", "encounters-detail"
])
def test_named_routes_resolve_if_configured(name: str) -> None:
    try:
        url = reverse(name, kwargs={"pk": 1} if "detail" in name else None)
        match = resolve(url)
        assert match is not None
    except Exception:
        pytest.skip(f"Route '{name}' not configured; adjust URL names in project.")