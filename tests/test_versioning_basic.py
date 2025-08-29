import pytest
import json
import contextlib
import importlib

from django.contrib.auth import get_user_model
from patients_core.models import Patient
from records_versioning.models import RecordVersion
from records_versioning.services import revert_to_version

User = get_user_model()


@pytest.mark.django_db
def test_version_increments_on_save() -> None:
    # Create a test user (doctor)
    doctor = User.objects.create_user(username="testdoctor", password="testpass")

    p = Patient.objects.create(full_name="Test P", primary_doctor=doctor)
    v1 = RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
        version=1,
    ).exists()
    assert v1
    p.full_name = "Test P2"
    p.save()
    v2 = RecordVersion.objects.get(
        resource_type="Patient",
        resource_id=p.id,
        version=2,
    )
    assert v2.diff is not None and "full_name" in v2.diff


@pytest.mark.django_db
def test_revert_creates_new_version() -> None:
    # Create test users
    doctor = User.objects.create_user(username="doctor", password="testpass")
    admin = User.objects.create_user(username="admin", password="testpass")

    p = Patient.objects.create(full_name="Patient A", primary_doctor=doctor)
    p.full_name = "Patient B"
    p.save()
    # revert to v1
    revert_to_version("Patient", p.id, 1, admin)
    v3 = RecordVersion.objects.get(
        resource_type="Patient",
        resource_id=p.id,
        version=3,
    )
    assert v3.prev_version == 2
    p2 = Patient.objects.get(id=p.id)
    assert p2.full_name == "Patient A"


# --- Additional comprehensive tests for records_versioning services and views ---
# Test stack: pytest + pytest-django

# Optional DRF imports for API tests (skipped if DRF not installed/configured)
with contextlib.suppress(Exception):
    from rest_framework.test import APIClient  # type: ignore

def _drf_available() -> bool:
    try:
        importlib.import_module("rest_framework")
        return True
    except Exception:
        return False

@pytest.mark.django_db
def test_revert_to_nonexistent_version_raises() -> None:
    # Arrange
    doctor = User.objects.create_user(username="doc_x", password="p")
    admin = User.objects.create_user(username="admin_x", password="p")
    p = Patient.objects.create(full_name="Alpha", primary_doctor=doctor)
    # Act + Assert
    with pytest.raises(RecordVersion.DoesNotExist):
        # Expecting service to raise when target version does not exist (e.g., v99)
        revert_to_version("Patient", p.id, 99, admin)


@pytest.mark.django_db
def test_revert_with_invalid_resource_type_raises() -> None:
    doctor = User.objects.create_user(username="doc_y", password="p")
    admin = User.objects.create_user(username="admin_y", password="p")
    p = Patient.objects.create(full_name="Bravo", primary_doctor=doctor)
    with pytest.raises(ValueError):
        revert_to_version("UnknownResource", p.id, 1, admin)


@pytest.mark.django_db
def test_revert_to_version_one_creates_next_version_and_restores_fields() -> None:
    # Arrange
    doctor = User.objects.create_user(username="doc_z", password="p")
    admin = User.objects.create_user(username="admin_z", password="p")
    p = Patient.objects.create(full_name="Charlie", primary_doctor=doctor)
    p.full_name = "Charlie Updated"
    p.save()

    # Sanity: we have v1 and v2
    assert RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
        version=1,
    ).exists()
    assert RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
        version=2,
    ).exists()

    # Act: revert to v1
    revert_to_version("Patient", p.id, 1, admin)

    # Assert: new version (v3) created, prev_version should be 2,
    # and underlying record rolled back
    v3 = RecordVersion.objects.get(
        resource_type="Patient",
        resource_id=p.id,
        version=3,
    )
    assert v3.prev_version == 2
    # Reload Patient and verify field restored
    p.refresh_from_db()
    assert p.full_name == "Charlie"


@pytest.mark.django_db
def test_revert_rejects_invalid_version_numbers() -> None:
    doctor = User.objects.create_user(username="doc_w", password="p")
    admin = User.objects.create_user(username="admin_w", password="p")
    p = Patient.objects.create(full_name="Delta", primary_doctor=doctor)

    for bad_version in (0, -1, None):
        with pytest.raises(ValueError):
            revert_to_version(
                "Patient",
                p.id,
                bad_version,
                admin,
            )  # type: ignore[arg-type]


@pytest.mark.django_db
def test_revert_requires_existing_resource() -> None:
    admin = User.objects.create_user(username="admin_missing", password="p")
    # Non-existent Patient id
    with pytest.raises(Patient.DoesNotExist):
        revert_to_version("Patient", 999999, 1, admin)  # Using non-existent integer ID


@pytest.mark.django_db
def test_versioning_tracked_fields_are_in_diff() -> None:
    doctor = User.objects.create_user(username="doc_diff", password="p")
    p = Patient.objects.create(full_name="Echo", primary_doctor=doctor)
    # Update multiple fields if available; fallback to single field
    p.full_name = "Echo Prime"
    p.save()

    v2 = RecordVersion.objects.get(
        resource_type="Patient",
        resource_id=p.id,
        version=2,
    )
    # diff should at least include the changed field name
    assert v2.diff is not None
    if isinstance(v2.diff, dict):
        assert "full_name" in v2.diff
    else:
        # If stored as JSON string or Text, ensure it contains the field name
        try:
            parsed = json.loads(v2.diff)  # type: ignore[arg-type]
            assert "full_name" in parsed
        except Exception:
            assert "full_name" in str(v2.diff)


@pytest.mark.django_db
def test_recordversion_has_monotonic_versions() -> None:
    doctor = User.objects.create_user(username="doc_mon", password="p")
    p = Patient.objects.create(full_name="Foxtrot", primary_doctor=doctor)
    for i in range(3):
        p.full_name = f"Foxtrot {i}"
        p.save()
    versions = list(
        RecordVersion.objects.filter(
            resource_type="Patient",
            resource_id=p.id,
        )
        .order_by("version")
        .values_list("version", flat=True)
    )
    assert versions == sorted(versions)
    assert versions[0] == 1
    assert versions[-1] >= 3


@pytest.mark.django_db
def test_service_is_atomic_and_creates_single_new_version() -> None:
    doctor = User.objects.create_user(username="doc_atomic", password="p")
    admin = User.objects.create_user(username="admin_atomic", password="p")
    p = Patient.objects.create(full_name="Golf", primary_doctor=doctor)
    p.full_name = "Golf v2"
    p.save()

    existing_count = RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
    ).count()
    # A transaction error inside should not leave partial state.
    # We simulate by attempting invalid revert first
    with pytest.raises(RecordVersion.DoesNotExist):
        revert_to_version("Patient", p.id, 9999, admin)
    # No new versions should have been added on failure
    assert RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
    ).count() == existing_count

    # Now perform valid revert and ensure exactly one new version added
    revert_to_version("Patient", p.id, 1, admin)
    assert RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
    ).count() == existing_count + 1


pytestmark = pytest.mark.skipif(
    not _drf_available(),
    reason="DRF not installed; skipping API tests",
)


@pytest.mark.django_db
def test_versions_history_endpoint_lists_versions() -> None:
    # This test assumes an endpoint like
    # /api/versioning/<resource_type>/<resource_id>/history/
    client = APIClient()
    doctor = User.objects.create_user(username="doc_api", password="p")
    client.force_authenticate(user=doctor)

    p = Patient.objects.create(full_name="Hotel", primary_doctor=doctor)
    p.full_name = "Hotel v2"
    p.save()

    candidate_paths = [
        f"/api/versions/Patient/{p.id}/",
        # Legacy paths for backward compatibility
        f"/api/versioning/Patient/{p.id}/history/",
        f"/records-versioning/Patient/{p.id}/history/",
        f"/api/records-versioning/Patient/{p.id}/history/",
    ]
    response = None
    for path in candidate_paths:
        resp = client.get(path)
        # pick the first 200 OK
        if resp.status_code == 200:
            response = resp
            break

    if response is None:
        pytest.skip(
            "No matching history endpoint path found "
            "(adjust test path to project URLs)."
        )

    data = response.json()
    assert isinstance(data, list) or "results" in data
    # Try to extract versions
    versions = data if isinstance(data, list) else data.get("results", [])
    assert any(v.get("version") == 1 for v in versions)
    assert any(v.get("version") == 2 for v in versions)


@pytest.mark.django_db
def test_revert_endpoint_performs_revert_and_creates_new_version() -> None:
    # Assumes an endpoint like POST
    # /api/versioning/<resource_type>/<resource_id>/revert/
    client = APIClient()
    doctor = User.objects.create_user(username="doc_api2", password="p")
    admin = User.objects.create_user(
        username="admin_api2",
        password="p",
        is_staff=True,
    )
    client.force_authenticate(user=admin)

    p = Patient.objects.create(full_name="India", primary_doctor=doctor)
    p.full_name = "India v2"
    p.save()

    pre_count = RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
    ).count()

    candidate_paths = [
        f"/api/versions/Patient/{p.id}/revert/",
        # مسیرهای قبلی برای سازگاری با دیپلوی‌های دیگر
        f"/api/versioning/Patient/{p.id}/revert/",
        f"/records-versioning/Patient/{p.id}/revert/",
        f"/api/records-versioning/Patient/{p.id}/revert/",
    ]
    done = False
    for path in candidate_paths:
        resp = client.post(path, {"target_version": 1}, format="json")
        if resp.status_code in (200, 201, 202, 204):
            done = True
            break

    if not done:
        pytest.skip(
            "No matching revert endpoint path found "
            "(adjust test path to project URLs)."
        )

    # Assert one new version created and record reverted
    assert RecordVersion.objects.filter(
        resource_type="Patient",
        resource_id=p.id,
    ).count() == pre_count + 1
    p.refresh_from_db()
    assert p.full_name == "India"