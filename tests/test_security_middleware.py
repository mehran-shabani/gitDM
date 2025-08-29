"""
Tests for AuditMiddleware.

Framework:
- Primary: pytest
- If available: pytest-django (for RequestFactory).
  Tests auto-fallback to mocks if Django isn't present.

Focus:
- Behavior defined in PR diff for AuditMiddleware.__call__: creating AuditLog
  with correct fields, UUID derivation for authenticated users, and handling
  unauthenticated users.
- Captures meta['remote_addr'] and swallows exceptions during logging without
  affecting response.

We do NOT test serializers/models per request; AuditLog ORM calls are mocked.
"""
import types
import uuid
from unittest.mock import Mock, patch

import pytest
from typing import Optional, Any
from collections.abc import Callable

# Try to import Django test utilities if available.
# Tests will skip Django-specific cases when not present.
try:
    from django.test import RequestFactory
    HAVE_DJANGO = True
except Exception:  # pragma: no cover - environment without django
    HAVE_DJANGO = False

# Resolve middleware import path dynamically.
# Search typical module names at runtime.
MIDDLEWARE_CANDIDATES = [
    # common app paths
    "security.middleware",
    "core.middleware",
    "apps.security.middleware",
    "app.middleware",
    "middleware",
]

AuditMiddleware = None
_import_error = None

for mod in MIDDLEWARE_CANDIDATES:
    try:
        m = __import__(mod, fromlist=["AuditMiddleware"])
        if hasattr(m, "AuditMiddleware"):
            AuditMiddleware = m.AuditMiddleware
            break
    except Exception as e:  # pragma: no cover - best-effort resolution
        _import_error = e

if AuditMiddleware is None:
    # As a last resort, attempt relative import.
    # Assumes tests are inside project root and module is alongside.
    try:
        from audit_middleware import AuditMiddleware  # type: ignore
    except Exception:  # pragma: no cover
        pass

pytestmark = pytest.mark.skipif(
    AuditMiddleware is None,
    reason=f"AuditMiddleware not importable: {_import_error!r}",
)

def _make_request(
    path: str = "/api/x",
    method: str = "GET",
    user: Optional["_User"] = None,
    remote_addr: str = "127.0.0.1",
) -> types.SimpleNamespace:
    """Create minimal request-like object for AuditMiddleware."""
    req = types.SimpleNamespace()
    req.path = path
    req.method = method
    req.META = {"REMOTE_ADDR": remote_addr}
    if user is not None:
        req.user = user
    return req

class _User:
    def __init__(self, uid: int, is_authenticated: bool = True) -> None:
        self.id = uid
        self.is_authenticated = is_authenticated

def _response(status: int = 200) -> types.SimpleNamespace:
    return types.SimpleNamespace(status_code=status)

def _next(
    response_status: int = 200,
) -> Callable[
    [types.SimpleNamespace], types.SimpleNamespace
]:
    def _call(req: types.SimpleNamespace) -> types.SimpleNamespace:
        return _response(response_status)
    return _call

@patch("security.middleware.AuditLog")
def test_logs_authenticated_user_uuid_deterministic(mock_auditlog: Mock) -> None:
    # Arrange
    try:
        # Rebind patch target dynamically to the module where AuditMiddleware is defined
        import importlib

        mod = importlib.import_module(AuditMiddleware.__module__)
        with patch(f"{mod.__name__}.AuditLog") as audit_log:
            user = _User(uid=42, is_authenticated=True)
            req = _make_request(user=user)
            get_response = _next(201)
            mw = AuditMiddleware(get_response)

            # Act
            resp = mw(req)

            # Assert
            assert resp.status_code == 201
            assert audit_log.objects.create.called
            kwargs = audit_log.objects.create.call_args.kwargs
            assert kwargs["path"] == req.path
            assert kwargs["method"] == req.method
            assert kwargs["status_code"] == 201
            assert kwargs["meta"] == {"remote_addr": "127.0.0.1"}
            # Deterministic UUID using uuid5 + NAMESPACE_DNS and 'user-<id>'
            expected_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "user-42")
            assert kwargs["user_id"] == expected_uuid
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@patch("security.middleware.AuditLog")
def test_logs_unauthenticated_user_sets_none(mock_auditlog: Mock) -> None:
    try:
        import importlib

        mod = importlib.import_module(AuditMiddleware.__module__)
        with patch(f"{mod.__name__}.AuditLog") as audit_log:
            user = _User(uid=7, is_authenticated=False)
            req = _make_request(user=user, method="POST", remote_addr="10.0.0.5")
            mw = AuditMiddleware(_next(200))

            resp = mw(req)

            assert resp.status_code == 200
            args, kwargs = audit_log.objects.create.call_args
            assert kwargs["user_id"] is None
            assert kwargs["meta"] == {"remote_addr": "10.0.0.5"}
            assert kwargs["method"] == "POST"
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@patch("security.middleware.AuditLog")
def test_logs_when_no_user_attribute(mock_auditlog: Mock) -> None:
    try:
        import importlib

        mod = importlib.import_module(AuditMiddleware.__module__)
        with patch(f"{mod.__name__}.AuditLog") as audit_log:
            req = _make_request()
            # ensure no user attribute
            if hasattr(req, "user"):
                delattr(req, "user")
            mw = AuditMiddleware(_next(204))

            resp = mw(req)

            assert resp.status_code == 204
            kwargs = audit_log.objects.create.call_args.kwargs
            assert kwargs["user_id"] is None
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@patch("security.middleware.AuditLog")
def test_logging_failure_does_not_affect_response(mock_auditlog: Mock) -> None:
    try:
        import importlib

        mod = importlib.import_module(AuditMiddleware.__module__)
        with patch(f"{mod.__name__}.AuditLog") as audit_log:
            # Force create() to raise to validate exception swallowing
            audit_log.objects.create.side_effect = RuntimeError("DB down")
            req = _make_request()
            mw = AuditMiddleware(_next(502))

            resp = mw(req)

            # Even though logging failed, response should pass through unchanged
            assert resp.status_code == 502
            assert audit_log.objects.create.called
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@patch("security.middleware.AuditLog")
def test_preserves_next_layer_response_object_identity(mock_auditlog: Mock) -> None:
    try:
        import importlib

        mod = importlib.import_module(AuditMiddleware.__module__)
        with patch(f"{mod.__name__}.AuditLog") as audit_log:
            req = _make_request()
            expected_resp = _response(200)

            def next_layer(r: types.SimpleNamespace) -> types.SimpleNamespace:
                return expected_resp

            mw = AuditMiddleware(next_layer)

            resp = mw(req)
            assert resp is expected_resp
            assert audit_log.objects.create.called
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@pytest.mark.skipif(not HAVE_DJANGO, reason="Django RequestFactory not available")
def test_with_django_requestfactory_smoke(monkeypatch: Any) -> None:
    # This smoke test ensures integration with a real HttpRequest shape.
    # AuditLog persistence is still mocked.
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log_mock = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log_mock, raising=True)

    rf = RequestFactory()
    request = rf.get("/healthz")
    # Simulate anonymous user (Django's AnonymousUser acts as is_authenticated=False)
    request.user = types.SimpleNamespace(is_authenticated=False, id=None)

    mw = AuditMiddleware(lambda req: types.SimpleNamespace(status_code=200))
    resp = mw(request)

    assert resp.status_code == 200
    assert audit_log_mock.objects.create.called
    kwargs = audit_log_mock.objects.create.call_args.kwargs
    assert kwargs["user_id"] is None
    assert kwargs["path"] == "/healthz"
    assert kwargs["method"] == "GET"
    assert isinstance(kwargs["meta"], dict)
# --- Additional comprehensive tests for AuditMiddleware ---

def test_missing_remote_addr_yields_none_in_meta(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    req = _make_request()
    # Remove REMOTE_ADDR entirely to simulate missing meta
    req.META = {}

    mw = AuditMiddleware(_next(200))
    resp = mw(req)

    assert resp.status_code == 200
    assert audit_log.objects.create.called
    kwargs = audit_log.objects.create.call_args.kwargs
    # Expect explicit None when REMOTE_ADDR absent
    assert kwargs["meta"] == {"remote_addr": None}

def test_ipv6_remote_addr_is_recorded_verbatim(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    req = _make_request(remote_addr=ipv6)
    mw = AuditMiddleware(_next(200))
    _ = mw(req)

    kwargs = audit_log.objects.create.call_args.kwargs
    assert kwargs["meta"] == {"remote_addr": ipv6}

def test_deterministic_uuid_across_multiple_calls(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    user = _User(uid=99, is_authenticated=True)
    req1 = _make_request(user=user)
    req2 = _make_request(user=user)

    mw = AuditMiddleware(_next(200))
    _ = mw(req1)
    _ = mw(req2)

    # two calls -> two create invocations
    assert audit_log.objects.create.call_count == 2
    first_uuid = audit_log.objects.create.call_args_list[0].kwargs["user_id"]
    second_uuid = audit_log.objects.create.call_args_list[1].kwargs["user_id"]
    assert first_uuid == second_uuid == uuid.uuid5(uuid.NAMESPACE_DNS, "user-99")

def test_authenticated_user_without_id_logs_none(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    # Authenticated but id missing/None
    user = types.SimpleNamespace(is_authenticated=True, id=None)
    req = _make_request(user=user)
    mw = AuditMiddleware(_next(200))
    _ = mw(req)

    kwargs = audit_log.objects.create.call_args.kwargs
    assert kwargs["user_id"] is None

def test_invokes_next_layer_once_and_logs_once(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    call_counter = {"n": 0}
    def next_once(r: types.SimpleNamespace) -> types.SimpleNamespace:
        call_counter["n"] += 1
        return _response(207)

    mw = AuditMiddleware(next_once)
    resp = mw(_make_request(method="PATCH"))

    assert resp.status_code == 207
    assert call_counter["n"] == 1
    assert audit_log.objects.create.call_count == 1
    kwargs = audit_log.objects.create.call_args.kwargs
    assert kwargs["method"] == "PATCH"

def test_request_object_not_mutated_by_middleware(monkeypatch: Any) -> None:
    import importlib
    mod = importlib.import_module(AuditMiddleware.__module__)
    audit_log = Mock()
    monkeypatch.setattr(mod, "AuditLog", audit_log, raising=True)

    user = _User(uid=123, is_authenticated=True)
    req = _make_request(path="/alpha", method="PUT", user=user, remote_addr="::1")
    snapshot = (
        req.path,
        req.method,
        getattr(req, "user", None),
        dict(req.META),
    )

    mw = AuditMiddleware(_next(226))
    resp = mw(req)

    assert resp.status_code == 226
    assert (
        req.path,
        req.method,
        getattr(req, "user", None),
        dict(req.META),
    ) == snapshot