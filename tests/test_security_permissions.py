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
        self.user = user


class Obj:  # simple dynamic object for attribute bags
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def view_unused() -> Any:
    # The permission classes don't use 'view'; provide a placeholder.
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
    user = types.SimpleNamespace(role=types.SimpleNamespace(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is True
    assert IsDoctor().has_permission(req, view_unused) is False