# Tests for API URL configuration and the health view
# Test framework: pytest with pytest-django (preferred in this repo if
# available).
# These tests focus on:
#  - URL names and reversibility for router endpoints and JWT token
#    endpoints
#  - Health view behavior (require_safe + never_cache):
#    allowed/blocked methods and caching headers

import json
import importlib
import re
from collections.abc import Callable, Iterable

import pytest
from django.test import RequestFactory

# Attempt to locate the API urls module by common patterns.
# If your module path differs, set API_URLS_MODULE via env or adjust below.
API_URLS_CANDIDATES = [
    "api.urls",
    "apps.api.urls",
    "core.api.urls",
    "project.api.urls",
    "backend.api.urls",
]


def _import_first(modules: Iterable[str]) -> object:
    last_exc = None
    for m in modules:
        try:
            return importlib.import_module(m)
        except Exception as e:  # pragma: no cover - import fallback path
            last_exc = e
            continue
    raise last_exc if last_exc else ImportError(
        "Could not import any API urls module"
    )


api_urls = _import_first(API_URLS_CANDIDATES)


@pytest.fixture(scope="module")
def urlpatterns() -> list:
    assert hasattr(api_urls, "urlpatterns"), "urlpatterns not found in api urls module"
    return api_urls.urlpatterns


@pytest.fixture(scope="module")
def health_view() -> Callable:
    assert hasattr(api_urls, "health"), "health view not found in api urls module"
    return api_urls.health


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


class TestUrlNamesAndReverses:
    def test_named_patterns_exist(self, urlpatterns: list) -> None:
        names = {getattr(p, "name", None) for p in urlpatterns if hasattr(p, "name")}
        # Core names from the diff
        expected = {
            "api-root",
            "api-health",
            "token_obtain_pair",
            "token_refresh",
            "token_obtain_pair_api",
            "token_refresh_api",
            "export_patient",
        }
        missing = expected - names
        assert not missing, f"Missing expected named urls: {missing}"

    def test_router_viewset_routes_present(self, urlpatterns: list) -> None:
        # Verify DRF SimpleRouter registered patterns exist by checking
        # route regexes for list/detail.
        # We avoid reverse() to not require ROOT_URLCONF; we inspect
        # pattern strings instead.
        pattern_strs = []
        for p in urlpatterns:
            # Include resolver from router
            if hasattr(p, "url_patterns"):
                for sub in getattr(p, "url_patterns", []):
                    pattern_strs.append(str(getattr(sub, "pattern", "")))
        text = "\n".join(pattern_strs)

        for base in ["patients", "encounters", "labs", "meds", "refs"]:
            list_pat = rf"/?{base}/?$"
            assert re.search(list_pat, text, re.M), f"List route missing for {base}"

            detail_pat1 = rf"/?{base}/\(\?P\<[^>]+>[^)]+\)/?$"
            detail_pat2 = rf"/?{base}/(?P<[^>]+>[^/]+)/?$"
            detail_pat3 = rf"/?{base}/<[^>]+>/?$"
            assert (
                re.search(detail_pat1, text)
                or re.search(detail_pat2, text)
                or re.search(detail_pat3, text)
            ), f"Detail route missing for {base}"

    def test_export_patient_reverse_shape(self, urlpatterns: list) -> None:
        # Find export pattern and ensure it contains a uuid converter
        export_patterns = [
            p for p in urlpatterns if getattr(p, "name", None) == "export_patient"
        ]
        assert export_patterns, "export_patient URL not found"
        patt = str(export_patterns[0].pattern)
        assert "export/patient" in patt

        has_uuid_converter = "<uuid:pk>" in patt
        has_uuid_text = "uuid" in patt.lower()
        assert has_uuid_converter or has_uuid_text, (
            f"Expected UUID converter in pattern, got: {patt}"
        )


class TestHealthViewBehavior:
    def test_health_get_ok_json_and_never_cache_headers(
        self, rf: RequestFactory, health_view: Callable
    ) -> None:
        req = rf.get("/health/")
        res = health_view(req)
        assert res.status_code == 200

        # JSON body
        payload = json.loads(res.content.decode() or "{}")
        assert payload == {"status": "ok"}

        # never_cache should set strong cache-prevention headers
        cc = res.headers.get("Cache-Control") or res.get("Cache-Control")
        assert cc and "no-cache" in cc and "no-store" in cc and "max-age=0" in cc
        assert (res.headers.get("Pragma") or res.get("Pragma")) == "no-cache"

        has_headers = hasattr(res, "headers")
        keys = res.headers.keys() if has_headers else res
        assert "Expires" in keys, "Expires header should be set"

    def test_health_head_allowed(self, rf: RequestFactory, health_view: Callable) -> None:
        req = rf.head("/health/")
        res = health_view(req)
        # require_safe allows GET and HEAD
        assert res.status_code == 200

    @pytest.mark.parametrize(
        "method", ["post", "put", "patch", "delete", "options", "trace"]
    )
    def test_health_unsafe_methods_disallowed(
        self, rf: RequestFactory, health_view: Callable, method: str
    ) -> None:
        # require_safe should disallow unsafe methods by returning 405
        req = getattr(rf, method)("/health/")
        res = health_view(req)
        assert res.status_code == 405, (
            f"{method.upper()} should be disallowed on health"
        )