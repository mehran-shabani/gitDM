import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db

def _get_ai_summary_model_and_admin() -> tuple[type, type]:
    # Find the registered model named 'AISummary' from admin site registry
    for model, model_admin in admin.site._registry.items():
        if model.__name__ == "AISummary":
            return model, model_admin.__class__
    raise LookupError(
        "AISummary model is not registered with the Django admin site."
    )

def test_ai_summary_admin_is_registered() -> None:
    model, model_admin_cls = _get_ai_summary_model_and_admin()
    assert model is not None, "AISummary model should be discoverable."
    assert issubclass(
        model_admin_cls, admin.ModelAdmin
    ), "AISummary admin must subclass ModelAdmin."

def test_ai_summary_admin_configuration_matches_spec() -> None:
    model, model_admin_cls = _get_ai_summary_model_and_admin()
    # Instantiate a ModelAdmin tied to the model
    # Request is not needed for these attributes
    model_admin = model_admin_cls(model, admin.site)

    # From the PR diff: ensure exact configuration for critical attributes
    assert tuple(model_admin.list_display) == (
        "patient",
        "resource_type",
        "created_at",
    )
    assert tuple(model_admin.list_filter) == ("resource_type", "created_at")
    assert tuple(
        model_admin.search_fields
    ) == (
        "patient__full_name",
        "resource_type",
        "summary",
    )
    # `readonly_fields` can be tuple or list
    # Compare as sets for flexibility in ordering
    assert set(model_admin.readonly_fields) == {"id", "created_at"}

def test_ai_summary_admin_readonly_fields_includes_id_and_created_at() -> None:
    model, model_admin_cls = _get_ai_summary_model_and_admin()
    model_admin = model_admin_cls(model, admin.site)

    # get_readonly_fields allows overriding; call without request/obj
    ro = model_admin.get_readonly_fields(request=None, obj=None)
    assert "id" in ro
    assert "created_at" in ro

def test_ai_summary_admin_changelist_accessible_to_superuser(
    client: object, django_user_model: object
) -> None:
    # Create superuser and login
    user = django_user_model
    su = user.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="pass",
    )
    client.force_login(su)

    model, _ = _get_ai_summary_model_and_admin()
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    url = reverse(f"admin:{app_label}_{model_name}_changelist")

    resp = client.get(url)
    assert resp.status_code == 200
    # Verify key UI elements exist (header and filter sidebar container)
    assert b"changelist-form" in resp.content
    assert b"action-select" in resp.content or b"result_list" in resp.content

def test_ai_summary_admin_requires_authentication(client: object) -> None:
    model, _ = _get_ai_summary_model_and_admin()
    url = reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
    )
    resp = client.get(url, follow=False)
    # Unauthenticated requests are redirected to admin login
    assert resp.status_code in (302, 301)
    assert "/admin/login" in resp.headers.get("Location", "")

# If pytest-django's admin_client fixture is available, also validate with it.
# This test will be skipped automatically if fixture is not present.
@pytest.mark.tryfirst
def test_ai_summary_admin_with_admin_client(admin_client: object) -> None:
    model, _ = _get_ai_summary_model_and_admin()
    url = reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
    )
    resp = admin_client.get(url)
    assert resp.status_code == 200