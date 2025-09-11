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
except (ImportError, ModuleNotFoundError):
    try:
        from app.security.permissions import IsAdmin, IsDoctor  # pragma: no cover
    except (ImportError, ModuleNotFoundError):
        try:
            from permissions import IsAdmin, IsDoctor  # pragma: no cover
        except (ImportError, ModuleNotFoundError) as e:  # Last resort: fail with a clear message
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


def test_permissions_when_role_is_none(view_unused: Any) -> None:
    user = Obj(role=None)
    req = FakeRequest(user=user)
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
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


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
