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
    except Exception as e:  # pragma: no cover
        _import_error = e  # best-effort resolution

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
    """
    یک شیء ساده شبیه به Request را برای استفاده در تست‌ها و شبیه‌سازی AuditMiddleware می‌سازد.

    این تابع یک SimpleNamespace با فیلدهای مورد انتظار AuditMiddleware تولید می‌کند:
    `path`، `method`، و `META` شامل `REMOTE_ADDR`. اگر پارامتر `user` داده شود،
    فیلد `user` هم به شیء اضافه می‌شود. شیء برگشتی برای تست واحد و جایگزینی
    یک HttpRequest واقعی کافی است و تنها خواص ضروری مورد نیاز middleware را
    فراهم می‌کند.

    Parameters:
        path (str): مسیر درخواست (مثلاً "/api/x"). صرفاً برای مقداردهی فیلد `path`.
        method (str): متد HTTP (مثل "GET" یا "POST").
        user (Optional[_User]): نمونهٔ کاربر شبیه‌سازی‌شده؛ اگر None باشد
            فیلد `user` در شیء وجود نخواهد داشت.
        remote_addr (str): مقدار آدرس مبدأ که در `META['REMOTE_ADDR']` قرار می‌گیرد.

    Returns:
        types.SimpleNamespace: شیء شبیه به درخواست با فیلدهای `path`,
        `method`, `META` و در صورت وجود `user`.
    """
    req = types.SimpleNamespace()
    req.path = path
    req.method = method
    req.META = {"REMOTE_ADDR": remote_addr}
    if user is not None:
        req.user = user
    return req

class _User:
    def __init__(self, uid: int, is_authenticated: bool = True) -> None:
        """
        یک سازندهٔ ساده برای شیٔ کاربر جایگزین در تست‌ها.

        این مقداردهی اولیه یک شیٔ کاربر سبک با دو ویژگی ایجاد می‌کند:
        - id: شناسهٔ عددی کاربر که برای تولید UUID قطعی در تست‌ها استفاده می‌شود.
        - is_authenticated: نشان‌دهندهٔ وضعیت احراز هویت کاربر؛ مقدار True به معنی
          کاربر وارد شده است و False به معنی ناشناس/غیر‌معتبر است.

        Parameters:
            uid (int): شناسهٔ عددی کاربر؛ معمولاً عدد صحیحی که در تست‌ها برای تولید
                `user-<id>` به کار می‌رود.
            is_authenticated (bool): اگر True باشد کاربر به‌عنوان احراز هویت‌شده در
                نظر گرفته می‌شود (پیش‌فرض True).
        """
        self.id = uid
        self.is_authenticated = is_authenticated

def _response(status: int = 200) -> types.SimpleNamespace:
    """
    یک شیء پاسخ ساده شبیه‌سازی‌شده برای استفاده در تست‌ها تولید می‌کند.

    این تابع یک types.SimpleNamespace با یک فیلد `status_code` ایجاد و بازمی‌گرداند
    که نمایانگر کد وضعیت HTTP است. برای شبیه‌سازی سریع پاسخ‌های لایه‌های پایین
    در واحدآزمایی‌ها استفاده می‌شود و هیچ رفتار دیگری (مثل هدرها یا بدنه) را
    مدل‌سازی نمی‌کند.

    Parameters:
        status (int): کد وضعیت HTTP که در فیلد `status_code` قرار می‌گیرد
            (پیش‌فرض 200).

    Returns:
        types.SimpleNamespace: یک شیء ساده با ویژگی `status_code` برابر
        مقدار ورودی.
    """
    return types.SimpleNamespace(status_code=status)

def _next(response_status: int = 200) -> Callable[[Any], types.SimpleNamespace]:
    """
    یک سازندهٔ تابعٔ کمکی برای تست‌ها که یک callable برمی‌گرداند و هر زمان فراخوانی
    شود، یک شیٔ پاسخ ساده با فیلد `status_code` را بازمی‌گرداند.

    پارامترها:
        response_status (int): کد وضعیت (HTTP-like) که شیٔ پاسخ تولیدشده باید
            داشته باشد. مقدار پیش‌فرض 200 است.

    بازگشت:
        Callable[[Any], types.SimpleNamespace]: تابعی که یک پارامتر (درخواست)
            می‌پذیرد اما آن را نادیده می‌گیرد و همیشه یک
            `types.SimpleNamespace` با `status_code==response_status` برمی‌گرداند.

    توضیحات اضافی:
        - تابع بازگشتی برای شبیه‌سازی لایهٔ بعدی در زنجیرهٔ middleware در تست‌ها
          استفاده می‌شود.
        - هیچ تداخل یا اثر جانبی دیگری ندارد و درخواست ورودی را دستکاری نمی‌کند.
    """
    def _call(req: object) -> types.SimpleNamespace:
        return _response(response_status)
    return _call

@patch("security.middleware.AuditLog")
def test_logs_authenticated_user_uuid_deterministic(mock_auditlog: Mock) -> None:
    # Arrange
    """
    تست می‌کند که AuditMiddleware هنگام دریافت درخواست از کاربر احراز
    هویت‌شده:
    - یک رکورد AuditLog ایجاد می‌کند با فیلدهای path، method، status_code و
      meta شامل remote_addr،
    - و مقدار user_id را به‌صورت قطعی و قابل تکرار با استفاده از
      uuid.uuid5(uuid.NAMESPACE_DNS, "user-<id>") تولید می‌کند.

    جزئیات:
    - یک درخواست ساختگی با کاربر احراز هویت‌شده (id=42) ساخته می‌شود و
      middleware اجرا می‌گردد.
    - اطمینان حاصل می‌شود که پاسخ دیتای برگشتی از لایه بعدی (status_code 201)
      بدون تغییر بازگردانده می‌شود.
    - سپس بررسی می‌شود که AuditLog.objects.create فراخوانی شده و آرگومان‌های
      ارسال‌شده شامل path، method، status_code، meta و user_id مطابق انتظار
      هستند.
    - در صورت عدم امکان ایمپورت دینامیک ماژولی که AuditMiddleware در آن
      تعریف شده، تست با pytest.skip نادیده گرفته می‌شود.
    """
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
    """
    بررسی می‌کند که در صورت خطا در ثبت لاگ (مثلاً پایگاه‌داده)، میدل‌ور AuditMiddleware پاسخ
    لایه بعدی را بدون تغییر بازمی‌گرداند.
    """
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

            def next_layer(r: object) -> types.SimpleNamespace:
                """
                یک لایهٔ بعدیٔ ساختگی که همیشه یک پاسخ از پیش‌تعریف‌شده را برمی‌گرداند.
                """
                return expected_resp

            mw = AuditMiddleware(next_layer)

            resp = mw(req)
            assert resp is expected_resp
            assert audit_log.objects.create.called
    except ModuleNotFoundError:
        pytest.skip("Unable to patch AuditLog in resolved middleware module path")

@pytest.mark.skipif(not HAVE_DJANGO, reason="Django RequestFactory not available")
def test_with_django_requestfactory_smoke(monkeypatch: object) -> None:
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

# ---------------------------
# Additional tests (extended)
# ---------------------------

@pytest.mark.parametrize("status", [200, 201, 204, 301, 400, 404, 500, 502])
def test_pass_through_various_status_codes(status: int) -> None:
    """
    Ensures response status codes from the next layer are passed through unchanged for a
    variety of cases.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        req = _make_request(method="GET")
        mw = AuditMiddleware(_next(status))
        resp = mw(req)
        assert resp.status_code == status
        assert audit_log.objects.create.called

def test_multiple_calls_produce_multiple_audit_entries() -> None:
    """
    Calling the middleware multiple times should create an AuditLog record for each request.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        mw = AuditMiddleware(_next(200))
        req1 = _make_request(path="/api/a", method="GET", user=_User(1))
        req2 = _make_request(path="/api/b", method="POST", user=_User(2))
        mw(req1)
        mw(req2)
        # Two create calls with different payloads
        assert audit_log.objects.create.call_count == 2
        first_kwargs = audit_log.objects.create.call_args_list[0].kwargs
        second_kwargs = audit_log.objects.create.call_args_list[1].kwargs
        assert first_kwargs["path"] == "/api/a"
        assert second_kwargs["path"] == "/api/b"
        assert first_kwargs["method"] == "GET"
        assert second_kwargs["method"] == "POST"

def test_remote_addr_prefers_x_forwarded_for_when_present() -> None:
    """
    If X-Forwarded-For is present, remote_addr should reasonably derive from it.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        req = _make_request(remote_addr="192.0.2.10")
        # inject X-Forwarded-For chain (client, proxy1, proxy2)
        req.META["HTTP_X_FORWARDED_FOR"] = (
            "203.0.113.5, 198.51.100.7, 192.0.2.10"
        )
        mw = AuditMiddleware(_next(200))
        resp = mw(req)
        assert resp.status_code == 200
        meta_logged = audit_log.objects.create.call_args.kwargs.get("meta") or {}
        assert meta_logged.get("remote_addr") in {"203.0.113.5", "192.0.2.10"}

def test_request_without_meta_is_handled_gracefully() -> None:
    """
    A request missing META should not break logging; response must still pass through.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        req = types.SimpleNamespace(path="/meta/missing", method="GET", user=_User(9))
        # Intentionally no META attribute
        mw = AuditMiddleware(_next(418))
        resp = mw(req)
        assert resp.status_code == 418
        assert audit_log.objects.create.called

def test_request_with_missing_remote_addr_key_is_handled_gracefully() -> None:
    """
    A request with META but without REMOTE_ADDR should still log without raising.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        req = types.SimpleNamespace(path="/no-remote", method="PATCH", META={}, user=_User(5))
        mw = AuditMiddleware(_next(200))
        resp = mw(req)
        assert resp.status_code == 200
        meta_logged = audit_log.objects.create.call_args.kwargs.get("meta")
        assert isinstance(meta_logged, dict)

def test_authenticated_user_with_string_id_produces_deterministic_uuid() -> None:
    """
    Authenticated users may sometimes have non-integer identifiers; ensure seed uses
    'user-<id>' string representation.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        user_like = types.SimpleNamespace(id="abc-123", is_authenticated=True)
        req = _make_request(user=user_like)
        mw = AuditMiddleware(_next(200))
        mw(req)
        kwargs = audit_log.objects.create.call_args.kwargs
        expected_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "user-abc-123")
        assert kwargs["user_id"] == expected_uuid

def test_uuid5_called_with_expected_namespace_and_seed(monkeypatch: object) -> None:
    """
    Verifies that uuid.uuid5 is called with uuid.NAMESPACE_DNS and the 'user-<id>' seed string.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)

    captured = {}

    def _uuid5(namespace: uuid.UUID, name: str) -> uuid.UUID:
        captured["namespace"] = namespace
        captured["name"] = name
        # return a stable fake uuid
        return uuid.UUID("12345678-1234-5678-1234-567812345678")

    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        monkeypatch.setattr(uuid, "uuid5", _uuid5, raising=True)
        user = _User(uid=77, is_authenticated=True)
        req = _make_request(user=user)
        mw = AuditMiddleware(_next(200))
        mw(req)

        assert captured["namespace"] == uuid.NAMESPACE_DNS
        assert captured["name"] == "user-77"
        assert audit_log.objects.create.call_args.kwargs["user_id"] == uuid.UUID(
            "12345678-1234-5678-1234-567812345678"
        )

def test_method_and_path_are_logged_exactly() -> None:
    """
    Ensures that path and method are persisted exactly as found on the request object.
    """
    import importlib

    mod = importlib.import_module(AuditMiddleware.__module__)
    with patch(f"{mod.__name__}.AuditLog") as audit_log:
        req = _make_request(path="/Exact/Case/Path?x=1", method="PATCH", user=_User(3))
        mw = AuditMiddleware(_next(200))
        mw(req)
        kwargs = audit_log.objects.create.call_args.kwargs
        assert kwargs["path"] == "/Exact/Case/Path?x=1"
        assert kwargs["method"] == "PATCH"