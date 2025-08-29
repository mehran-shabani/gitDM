"""
Tests for project URL configuration and API schema/docs endpoints.

Framework: pytest + pytest-django with DRF's APIClient when available.
"""

import importlib
import pytest
from django.urls import resolve


try:
    from rest_framework.test import APIClient
    HAS_DRF = True
except Exception:
    HAS_DRF = False


@pytest.mark.django_db
class TestProjectUrls:
    def test_schema_url_resolves(self, settings: object) -> None:
        match = resolve("/api/schema/")
        assert match.func is not None
        # SpectacularAPIView.as_view() sets view_class name
        assert "SpectacularAPIView" in getattr(
            getattr(match.func, "view_class", object),
            "__name__", ""
        )

    def test_swagger_url_resolves(self) -> None:
        match = resolve("/api/docs/")
        assert match.func is not None
        assert "SpectacularSwaggerView" in getattr(
            getattr(match.func, "view_class", object),
            "__name__", ""
        )

    @pytest.mark.skipif(not HAS_DRF, reason="DRF not installed in test environment")
    def test_schema_endpoint_returns_200(self, db: object) -> None:
        client = APIClient()
        resp = client.get("/api/schema/")
        assert resp.status_code == 200
        ctype = resp.headers.get("Content-Type", "")
        assert "json" in ctype

    @pytest.mark.skipif(not HAS_DRF, reason="DRF not installed in test environment")
    def test_swagger_ui_served(self, db: object) -> None:
        client = APIClient()
        resp = client.get("/api/docs/")
        assert resp.status_code in (200, 302)
        if resp.status_code == 200:
            text = resp.text.lower()
            assert "swagger" in text or "rapidoc" in text or "redoc" in text

    def test_api_routers_included(self) -> None:
        module = importlib.import_module("api.routers")
        assert module is not None

    def test_root_includes_api_routers(self, settings: object) -> None:
        from django.conf import settings as dj_settings
        from importlib import import_module

        urls_mod = import_module(dj_settings.ROOT_URLCONF)
        patterns = getattr(urls_mod, "urlpatterns", [])
        included = [
            p
            for p in patterns
            if getattr(p, "pattern", None) and str(p.pattern) == ""
        ]
        assert any(
            "api.routers" in repr(getattr(p, "urlconf_module", ""))
            for p in included
        ), "api.routers not included at root ''"


@pytest.mark.django_db
class TestApiVersionPaths:
    @pytest.mark.skipif(not HAS_DRF, reason="DRF not installed in test environment")
    @pytest.mark.parametrize("path", [
        "/api/v1/",
        "/api/v2/",
    ])
    def test_version_index_paths_exist_or_404_clean(self, path: str, db: object) -> None:
        """
        Bias for action: check common version roots.
        If not present, ensure a clean 404 without server error.
        """
        client = APIClient()
        resp = client.get(path)
        assert resp.status_code in (200, 301, 302, 404)
        assert resp.status_code < 500

    def test_rest_framework_versioning_config(self, settings: object) -> None:
        rf = getattr(settings, "REST_FRAMEWORK", {})
        for key in (
            "DEFAULT_VERSIONING_CLASS",
            "DEFAULT_SCHEMA_CLASS",
            "DEFAULT_VERSION",
            "ALLOWED_VERSIONS",
            "VERSION_PARAM",
        ):
            if key in rf:
                assert rf[key] is not None


@pytest.mark.django_db
@pytest.mark.skipif(not HAS_DRF, reason="DRF not installed in test environment")
class TestVersionEndpoints:
    def test_versions_list_empty_ok(self) -> None:
        from uuid import uuid4
        client = APIClient()
        resp = client.get(f"/api/versions/Patient/{uuid4()}/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data == []

    def test_versions_revert_missing_target_version_400(self) -> None:
        from uuid import uuid4
        client = APIClient()
        resp = client.post(
            f"/api/versions/Patient/{uuid4()}/revert/", 
            data={}, 
            format="json"
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data
        assert "target_version" in data["error"].lower()