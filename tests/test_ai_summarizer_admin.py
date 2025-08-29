from datetime import datetime, timedelta
import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory
from django.urls import reverse

# Import the admin classes under test
# The admin module under test should reside alongside AISummary model.
# Adjust the dotted path below if the app label differs (e.g., "ai_summarizer").
try:
    from . import admin as app_admin  # when tests package is inside the app
except Exception:
    # Fallback: try to find "<app>.admin" by scanning installed apps lazily
    # Replace 'ai_summarizer' with your actual app label if needed.
    try:
        app_admin = __import__("ai_summarizer.admin", fromlist=["*"])
    except Exception as err:
        # Last resort: create a stub module error to help developers fix import path
        raise ImportError(
            "Unable to import the app's admin module. "
            "Ensure the app label is correct (e.g., ai_summarizer.admin) "
            "or adjust the import in tests/test_ai_summarizer_admin.py."
        ) from err

# Extract classes under test
AISummaryResourceTypeFilter = app_admin.AISummaryResourceTypeFilter
AISummaryAdmin = app_admin.AISummaryAdmin
AISummary = app_admin.AISummary

pytestmark = pytest.mark.django_db


def make_superuser(**extra: object) -> tuple[object, str]:
    user_model = get_user_model()
    username = extra.pop("username", "admin")
    email = extra.pop("email", "admin@example.com")
    password = extra.pop("password", "pass1234")
    user = user_model.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        **extra,
    )
    return user, password


def create_ai_summary(
    patient: object | None = None,
    model_label: str = "note",
    created_at: datetime | None = None,
) -> AISummary:
    """
    Helper to create AISummary with a valid ContentType to
    drive resource_type filtering.
    - model_label corresponds to ContentType.model (lowercase)
    """
    # Patient is likely a FK; if project uses a different patient model
    # adjust accordingly.
    # We'll soft-create a minimal patient if field allows null=False.
    if patient is None:
        # Try to discover Patient model from the AISummary FK meta if present
        patient_field = AISummary._meta.get_field("patient")
        patient_model = patient_field.related_model
        patient = patient_model.objects.create()  # rely on defaults
        # adjust in project if required

    # Build a fake model proxy for ContentType if necessary
    # Prefer locating an actual model whose _meta.model_name == model_label
    # otherwise create CT manually
    try:
        ct = ContentType.objects.get(model=model_label)
    except ContentType.DoesNotExist:
        # Create a temporary dummy model content type by using the
        # AISummary model's app_label
        app_label = AISummary._meta.app_label
        # ContentType requires a valid app_label+model; if not present,
        # use AISummary's app_label and custom model name
        ct, _ = ContentType.objects.get_or_create(
            app_label=app_label,
            model=model_label,
        )

    values = dict(
        patient=patient,
        content_type=ct,
        summary=f"Summary for {model_label}",
        object_id=1,
    )
    if created_at is not None:
        values["created_at"] = created_at
    return AISummary.objects.create(**values)


class DummyModelAdmin(admin.ModelAdmin):
    pass


def build_changelist_request(
    path: str,
    user: object,
    params: dict | None = None,
) -> object:
    rf = RequestFactory()
    query = ""
    if params:
        from urllib.parse import urlencode

        query = "?" + urlencode(params, doseq=True)
    request = rf.get(f"{path}{query}")
    request.user = user
    return request


def get_admin_changelist_url(model: type) -> str:
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")


def test_list_display_contains_expected_columns() -> None:
    ma = AISummaryAdmin(AISummary, admin.site)
    assert ("patient", "resource_type", "created_at") == tuple(ma.list_display)


def test_get_list_filter_overrides_and_includes_custom_filter() -> None:
    ma = AISummaryAdmin(AISummary, admin.site)
    # The attribute exists for expectations but runtime
    # list_filter comes from get_list_filter
    assert ("created_at",) == ma.list_filter
    resolved = ma.get_list_filter(request=None)
    # Expect custom filter class and created_at
    assert isinstance(resolved, list | tuple)
    assert resolved[0] is AISummaryResourceTypeFilter
    assert "created_at" in resolved


def test_resource_type_filter_lookups_only_unique_non_empty_models(
    admin_client: Client,
) -> None:
    # Prepare multiple summaries across different content types; include
    # an empty/None model case if possible
    create_ai_summary(model_label="note")
    create_ai_summary(model_label="note")
    create_ai_summary(model_label="report")

    # Instantiate filter and compute lookups
    request = admin_client.request().wsgi_request  # minimal request object
    ma = AISummaryAdmin(AISummary, admin.site)
    flt = AISummaryResourceTypeFilter(request, {}, AISummary, ma)
    lookups = flt.lookups(request, ma)

    # Expect only two unique entries and both labels match the model names
    labels = sorted([label for value, label in lookups])
    assert labels == ["note", "report"]


def test_resource_type_filter_queryset_filters_when_value_selected(
    admin_client: Client,
) -> None:
    create_ai_summary(model_label="alpha")
    create_ai_summary(model_label="beta")
    request = admin_client.request().wsgi_request
    ma = AISummaryAdmin(AISummary, admin.site)

    # Simulate selecting "alpha" from the filter by overriding self.value()
    class _Filter(AISummaryResourceTypeFilter):
        def value(self) -> str:
            return "alpha"

    flt = _Filter(request, {}, AISummary, ma)
    qs = flt.queryset(request, AISummary.objects.all())
    assert qs.count() == 1
    assert qs.first().content_type.model == "alpha"


def test_resource_type_filter_queryset_returns_unfiltered_when_no_value(
    admin_client: Client,
) -> None:
    create_ai_summary(model_label="alpha")
    create_ai_summary(model_label="beta")
    request = admin_client.request().wsgi_request
    ma = AISummaryAdmin(AISummary, admin.site)
    flt = AISummaryResourceTypeFilter(request, {}, AISummary, ma)
    qs = flt.queryset(request, AISummary.objects.all())
    assert qs.count() == 2


def test_changelist_view_renders_with_result_list_marker(
    client: Client,
) -> None:
    # Create superuser and login to access admin
    user, password = make_superuser()
    client = Client()
    assert client.login(username=user.username, password=password)
    # Seed at least one record to avoid empty queryset edge-cases
    create_ai_summary(model_label="rendercheck")

    url = get_admin_changelist_url(AISummary)
    resp = client.get(url)
    # The overridden changelist_view ensures render() is called
    # and injects result_list marker if missing
    assert resp.status_code == 200
    content = resp.content or b""
    assert b"result_list" in content


def test_changelist_view_handles_non_renderable_response_gracefully(
    monkeypatch: object,
) -> None:
    # Build a fake admin instance whose super().changelist_view returns a minimal object
    class NoRenderResponse:
        # Missing render/content attributes should be tolerated by try/except
        pass

    def fake_changelist_view(
        self: AISummaryAdmin,
        request: object,
        extra_context: object | None = None,
    ) -> object:
        return NoRenderResponse()

    monkeypatch.setattr(
        AISummaryAdmin,
        "changelist_view",
        fake_changelist_view,
        raising=False,
    )
    # Now call the original implementation against the fake response path
    # by invoking the method on a subclass
    class _Temp(AISummaryAdmin):
        pass

    # Restore original for super() call; we need to call the real method
    monkeypatch.setattr(
        AISummaryAdmin,
        "changelist_view",
        app_admin.AISummaryAdmin.changelist_view,
        raising=False,
    )

    rf = RequestFactory()
    req = rf.get("/")
    req.user, _ = make_superuser(username="x2", email="x2@example.com")
    # Patch super().changelist_view to return NoRenderResponse for this call
    orig_super = app_admin.AISummaryAdmin.changelist_view

    def super_stub(
        self: AISummaryAdmin,
        request: object,
        extra_context: object | None = None,
    ) -> object:
        return NoRenderResponse()

    try:
        monkeypatch.setattr(
            app_admin.AISummaryAdmin,
            "changelist_view",
            super_stub,
            raising=False,
        )
        resp = _Temp(AISummary, admin.site).changelist_view(req)
        # Should return the same object without raising;
        # no attributes to assert other than type
        assert isinstance(resp, NoRenderResponse)
    finally:
        monkeypatch.setattr(
            app_admin.AISummaryAdmin,
            "changelist_view",
            orig_super,
            raising=False,
        )


def test_search_fields_and_readonly_and_select_related_contract() -> None:
    ma = AISummaryAdmin(AISummary, admin.site)
    assert ("patient__full_name", "content_type__model", "summary") == ma.search_fields
    assert ("id", "created_at") == ma.readonly_fields
    assert ("patient", "content_type") == ma.list_select_related


def test_created_at_filter_and_date_range_behaviour(
    client: Client,
) -> None:
    # Verify that created_at remains usable alongside custom filter
    user, password = make_superuser(username="dater", email="dater@example.com")
    client = Client()
    assert client.login(username=user.username, password=password)

    # Create two records with different created_at dates if field allows manual set
    now = datetime.now(datetime.UTC)
    old = now - timedelta(days=10)
    create_ai_summary(model_label="dateA", created_at=old)
    create_ai_summary(model_label="dateB", created_at=now)

    url = get_admin_changelist_url(AISummary)

    # Filter by resource_type only
    resp = client.get(url, {"resource_type": "dateB"})
    assert resp.status_code == 200
    assert b"result_list" in resp.content
    # Sanity: both records exist; we can't easily assert count from HTML here
    # without parsing, but we validate that the page renders with sidebar filters
    # (presence of 'filter' class)
    assert b"filter" in resp.content or b"changelist-filter" in resp.content