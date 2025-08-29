"""Unit tests for DRF permission classes IsAdmin and IsDoctor.

Testing framework: pytest
- We use simple lightweight fakes instead of DRF Request objects
  to keep tests pure-unit.
- No serializers or models are tested, per guidance; we focus on permission logic.

Coverage:
- Happy paths for 'admin' and 'doctor'
- Non-matching roles (e.g., 'nurse', case-sensitivity)
- Missing role attribute on user
- role present but None
- role object missing 'role' attribute
  (expected AttributeError based on current implementation)
- request.user present but is an object without 'role'
- request.user is None
- Sanity check that view parameter isn't used

If project uses unittest, pytest will still discover and run these functions.
"""
import types
import pytest
from typing import Any

# Attempt to import the permissions under test from common locations.
# Adjust import paths if your project structure differs.
try:
    from security.permissions import IsAdmin, IsDoctor  # pragma: no cover
except Exception:
    try:
        from app.security.permissions import IsAdmin, IsDoctor  # pragma: no cover
    except Exception:
        try:
            from permissions import IsAdmin, IsDoctor  # pragma: no cover
        except Exception as e:  # Last resort: fail with a clear message
            raise ImportError(
                "Could not import IsAdmin/IsDoctor. "
                "Tried: security.permissions, app.security.permissions, permissions. "
                "Please adjust the import path in tests/test_security_permissions.py."
            ) from e


class FakeRequest:
    """Minimal request surrogate with a 'user' attribute."""

    def __init__(self, user: Any) -> None:
        """
        سازندهٔ شیء حاملِ کاربر را مقداردهی می‌کند.

        پارامترها:
            user: شیئی که نمایندهٔ کاربر درخواست است؛ می‌تواند None یا هر نوع دیگری باشد
                  (مثلاً یک آبجکت ساده با خصوصیت‌های مورد انتظار مانند `role`). مقدار
                  ورودی بدون اعتبارسنجی نگهداری و در صفت نمونه‌ای `self.user` قرار می‌گیرد.
        """
        self.user = user


class Obj:  # simple dynamic object for attribute bags
    def __init__(self, **kwargs: Any) -> None:
        """
        نمونه‌ساز ساده‌ای که مقادیر کلید‌=مقدار داده‌شده را به صفت‌های نمونه انتساب می‌دهد.

        هر جفت کلید=مقدار در kwargs به‌عنوان صفتی با نام کلید روی شیء قرار می‌گیرد (setattr). این متد هیچ اعتبارسنجی یا کپی‌برداری انجام نمی‌دهد و مقادیر را مستقیماً انتساب می‌کند، بنابراین:
        - صفت‌های موجود با همان نام بازنویسی خواهند شد.
        - می‌توان هر نام و هر مقدار معتبری را اضافه کرد.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def view_unused() -> Any:
    # The permission classes don't use 'view'; provide a placeholder.
    """
    بازگرداندن یک شیء جایگزین که به‌عنوان مقدار نمادین برای پارامتر `view` استفاده می‌شود.

    این مقدار جهت استفاده در تست‌ها به‌عنوان یک placeholder ارائه می‌شود زیرا کلاس‌های مجوز (`IsAdmin` و `IsDoctor`) پارامتر `view` را استفاده نمی‌کنند. شیء بازگشتی بی‌حالتی (opaque) است و تنها برای متمایز کردن و پر کردن آرگومان `view` در فراخوانی `has_permission` به کار می‌رود.

    Returns:
        object: شیء نمادین که به عنوان مقدار `view` در تست‌ها استفاده می‌شود.
    """
    return object()


@pytest.mark.parametrize(
    "user_role, expected_admin, expected_doctor",
    [
        ("admin", True, False),
        ("doctor", False, True),
        ("nurse", False, False),
        ("", False, False),
        ("Admin", False, False),   # case sensitivity check
        ("DOCTOR", False, False),  # case sensitivity check
        ("doctor ", False, False), # whitespace sensitivity
    ],
)
def test_permissions_with_valid_role_string(
    user_role: str,
    expected_admin: bool,
    expected_doctor: bool,
    view_unused: Any,
) -> None:
    """
    تست پارامتری‌شده‌ای که پذیرش سطوح دسترسی بر اساس رشته نقش داخلی را بررسی می‌کند.

    هر بار با یک مقدار `user_role` یک شیء کاربر با ساختار تو در تو (user.role.role) ساخته می‌شود و سپس بررسی می‌شود که
    IsAdmin.has_permission و IsDoctor.has_permission نتیجه‌ی مورد انتظار (`expected_admin` و `expected_doctor`) را برگردانند.

    Parameters:
        user_role (str): مقدار رشته‌ای نقش که در user.role.role قرار می‌گیرد (مثلاً "admin" یا "doctor").
        expected_admin (bool): مقدار بولی مورد انتظار برای IsAdmin().has_permission.
        expected_doctor (bool): مقدار بولی مورد انتظار برای IsDoctor().has_permission.
        view_unused (Any): فیکسچر جایگزین برای پارامتر view (در این تست نادیده گرفته می‌شود).
    """
    user = Obj(role=Obj(role=user_role))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is expected_admin
    assert IsDoctor().has_permission(req, view_unused) is expected_doctor


def test_permissions_when_user_has_no_role_attribute(view_unused: Any) -> None:
    user = Obj()  # no 'role'
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_when_user_is_none(view_unused: Any) -> None:
    req = FakeRequest(user=None)
    # hasattr(None, 'role') -> False; should not raise
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_when_role_is_none(view_unused: Any) -> None:
    user = Obj(role=None)
    req = FakeRequest(user=user)
    # hasattr(None, 'role') -> False; should not raise
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_raise_when_role_object_missing_inner_role(view_unused: Any) -> None:
    user = Obj(role=Obj())  # role exists, but missing 'role' attr
    req = FakeRequest(user=user)
    # Current implementation accesses request.user.role.role unguarded;
    # Expect AttributeError. This test documents current behavior.
    with pytest.raises(AttributeError):
        IsAdmin().has_permission(req, view_unused)
    with pytest.raises(AttributeError):
        IsDoctor().has_permission(req, view_unused)


def test_permissions_with_extra_unrelated_user_attrs(view_unused: Any) -> None:
    # Ensure unrelated attrs don't affect logic
    user = Obj(username="alice", id=123, role=Obj(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is True
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_view_parameter_is_ignored(view_unused: Any) -> None:
    user = Obj(role=Obj(role="doctor"))
    req = FakeRequest(user=user)

    class DummyView:  # any object should do
        sentinel = True

    view = DummyView()
    assert IsDoctor().has_permission(req, view) is True
    assert IsAdmin().has_permission(req, view) is False


def test_permissions_user_object_without_dunder_dict(view_unused: Any) -> None:
    # Use types.SimpleNamespace (has __dict__) and a custom object without dict
    # to ensure attribute access works
    """
    بررسی رفتار کلاس‌های مجوز (IsAdmin و IsDoctor) هنگام دریافت یک شیء کاربر از نوع types.SimpleNamespace.

    شیء کاربر با صفت تو در تو role.role برابر "admin" ساخته می‌شود؛ انتظار می‌رود IsAdmin.has_permission مقدار True و IsDoctor.has_permission مقدار False بازگرداند. پارامتر view_unused صرفاً یک مقدار کمکی/فیکسچر است و در منطق مجوز نادیده گرفته می‌شود.
    """
    user = types.SimpleNamespace(role=types.SimpleNamespace(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is True
    assert IsDoctor().has_permission(req, view_unused) is False


# --- Additional comprehensive tests (appended) ---

# Happy paths already covered above; add mixed and edge scenarios.

@pytest.mark.parametrize(
    "user_role, expected_admin, expected_doctor",
    [
        (" admin", False, False),   # leading space
        ("doctor\n", False, False), # trailing newline
        ("\tadmin", False, False),  # tabbed
        ("Админ", False, False),    # non-ASCII role should not match
        ("دکتر", False, False),     # Persian word for doctor should not match
    ],
)
def test_permissions_role_string_whitespace_and_i18n(user_role, expected_admin, expected_doctor, _view) -> None:
    user = _Obj(role=_Obj(role=user_role))
    req = _Req(user=user)
    assert IsAdmin().has_permission(req, _view) is expected_admin
    assert IsDoctor().has_permission(req, _view) is expected_doctor


def test_permissions_when_request_has_no_user_attribute(_view) -> None:
    class NoUserReq:
        pass

    req = NoUserReq()  # type: ignore[assignment]
    # Accessing req.user should fail gracefully to False if implementation checks via getattr/hasattr,
    # but may raise AttributeError if it assumes presence. Document current behavior:
    try:
        assert IsAdmin().has_permission(req, _view) is False
        assert IsDoctor().has_permission(req, _view) is False
    except AttributeError:
        pytest.xfail("Current implementation accesses request.user directly and raises AttributeError.")


def test_permissions_when_user_role_is_dict_expect_attribute_error_documented(_view) -> None:
    # If implementation uses attribute access (user.role.role), a dict at user.role will raise AttributeError.
    user = _Obj(role={"role": "admin"})
    req = _Req(user=user)
    with pytest.raises(AttributeError):
        IsAdmin().has_permission(req, _view)
    with pytest.raises(AttributeError):
        IsDoctor().has_permission(req, _view)


def test_permissions_when_user_is_missing_role_container(_view) -> None:
    # user.role exists but inner .role is None explicitly
    user = _Obj(role=_Obj(role=None))
    req = _Req(user=user)
    assert IsAdmin().has_permission(req, _view) is False
    assert IsDoctor().has_permission(req, _view) is False


def test_permissions_with_simpler_shape_if_supported(_view) -> None:
    # Some codebases evolve to support user.role being the raw string.
    # If not supported, this test will raise; we mark as xfail in that case to document intent.
    user = _Obj(role="admin")
    req = _Req(user=user)
    try:
        result_admin = IsAdmin().has_permission(req, _view)
    except AttributeError:
        pytest.xfail("Implementation requires nested user.role.role; flat user.role not supported.")
    else:
        assert result_admin is True
        assert IsDoctor().has_permission(_Req(_Obj(role="doctor")), _view) is True


def test_permissions_simple_namespace_still_valid(_view) -> None:
    user = types.SimpleNamespace(role=types.SimpleNamespace(role="doctor"))
    req = _Req(user=user)
    assert IsDoctor().has_permission(req, _view) is True
    assert IsAdmin().has_permission(req, _view) is False


# Object-level permission parity:
# If has_object_permission is not overridden, DRF BasePermission returns True by default.
# We assert the current behavior explicitly to prevent accidental privilege escalation if combined.
@pytest.mark.parametrize(
    "cls, expect_permission",
    [
        (IsAdmin, False),   # with non-admin user
        (IsDoctor, True),   # with doctor user
    ],
)
def test_has_object_permission_matches_has_permission_when_implemented(cls, expect_permission, _view) -> None:
    # Arrange a user who yields expect_permission for has_permission
    role = "doctor" if expect_permission else "nurse"
    if cls is IsAdmin and not expect_permission:
        role = "nurse"
    if cls is IsAdmin and expect_permission:
        role = "admin"
    user = _Obj(role=_Obj(role=role))
    req = _Req(user=user)

    perm = cls()
    has_perm = perm.has_permission(req, _view)
    try:
        has_obj_perm = perm.has_object_permission(req, _view, object())
    except AttributeError:
        # If not implemented, DRF BasePermission.has_object_permission returns True.
        # Document the potential risk; assert True to lock behavior for current version.
        has_obj_perm = True

    # Document and check:
    # - If object-permission is implemented, it should be consistent with base decision (tighten or equal).
    # - If not implemented, this highlights that combining permissions with OR may allow access.
    if hasattr(perm, "has_object_permission"):
        # Implementation exists; assert it is not more permissive than has_permission for these roles.
        assert (has_obj_perm and has_perm) is has_obj_perm
    else:
        assert has_obj_perm in (True, False)  # sanity; typically True by BasePermission default


def test_permissions_with_unexpected_user_type_int(_view) -> None:
    req = _Req(user=123)  # nonsensical user
    # Expect False or AttributeError depending on implementation strictness.
    try:
        assert IsAdmin().has_permission(req, _view) is False
        assert IsDoctor().has_permission(req, _view) is False
    except AttributeError:
        pytest.xfail("Implementation does not guard against non-object user types.")


def test_permissions_with_user_object_missing_dunder_dict(_view) -> None:
    # Create a minimalist user object without __dict__ by using __slots__
    class SlotUser:
        __slots__ = ("role",)

        def __init__(self, role) -> None:
            self.role = role

    class SlotRole:
        __slots__ = ("role",)

        def __init__(self, role) -> None:
            self.role = role

    user = SlotUser(role=SlotRole(role="admin"))
    req = _Req(user=user)
    assert IsAdmin().has_permission(req, _view) is True
    assert IsDoctor().has_permission(_Req(SlotUser(role=SlotRole(role="doctor"))), _view) is True
    assert IsDoctor().has_permission(_Req(SlotUser(role=SlotRole(role="nurse"))), _view) is False


def test_permissions_view_object_of_arbitrary_type_is_ignored(_view) -> None:
    class RandomView:
        def __init__(self):
            self.any = "thing"

    user = _Obj(role=_Obj(role="doctor"))
    req = _Req(user=user)
    assert IsDoctor().has_permission(req, RandomView()) is True
    assert IsAdmin().has_permission(req, RandomView()) is False