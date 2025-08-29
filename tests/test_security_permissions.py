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
    def __init__(self, user: object) -> None:
        self.user = user


class Obj:  # simple dynamic object for attribute bags
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def view_unused() -> object:
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
    view_unused: object,
) -> None:
    user = Obj(role=Obj(role=user_role))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is expected_admin
    assert IsDoctor().has_permission(req, view_unused) is expected_doctor


def test_permissions_when_user_has_no_role_attribute(view_unused: object) -> None:
    user = Obj()  # no 'role'
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_when_user_is_none(view_unused: object) -> None:
    req = FakeRequest(user=None)
    # hasattr(None, 'role') -> False; should not raise
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_when_role_is_none(view_unused: object) -> None:
    user = Obj(role=None)
    req = FakeRequest(user=user)
    # hasattr(None, 'role') -> False; should not raise
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_raise_when_role_object_missing_inner_role(view_unused: object) -> None:
    user = Obj(role=Obj())  # role exists, but missing 'role' attr
    req = FakeRequest(user=user)
    # Current implementation accesses request.user.role.role unguarded.
    # Expect AttributeError. This test documents current behavior.
    with pytest.raises(AttributeError):
        IsAdmin().has_permission(req, view_unused)
    with pytest.raises(AttributeError):
        IsDoctor().has_permission(req, view_unused)


def test_permissions_with_extra_unrelated_user_attrs(view_unused: object) -> None:
    # Ensure unrelated attrs don't affect logic
    user = Obj(username="alice", id=123, role=Obj(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is True
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_view_parameter_is_ignored(view_unused: object) -> None:
    user = Obj(role=Obj(role="doctor"))
    req = FakeRequest(user=user)
    class DummyView:  # any object should do
        sentinel = True
    view = DummyView()
    assert IsDoctor().has_permission(req, view) is True
    assert IsAdmin().has_permission(req, view) is False


def test_permissions_user_object_without_dunder_dict(view_unused: object) -> None:
    # Use types.SimpleNamespace (has __dict__) and a custom object without dict
    # to ensure attribute access works
    user = types.SimpleNamespace(role=types.SimpleNamespace(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is True
    assert IsDoctor().has_permission(req, view_unused) is False


# ---------------------------------------------------------------------------
# Additional unit tests (pytest) for IsAdmin and IsDoctor permission classes.
# Framework: pytest
# These tests extend coverage to slotted objects, property-based roles,
# missing request.user attribute, dict-like users, non-string role values,
# and leading whitespace in role strings.
# ---------------------------------------------------------------------------


class RequestWithoutUser:
    """Request surrogate lacking a 'user' attribute (documents current behavior)."""
    pass


class UserWithProperty:
    """User whose 'role' property returns an object with a 'role' attribute."""
    def __init__(self, role_value: str) -> None:
        self._role_value = role_value

    @property
    def role(self) -> "Obj":
        return Obj(role=self._role_value)


class SlottedRole:
    __slots__ = ("role",)
    def __init__(self, role: str) -> None:
        self.role = role


class SlottedUser:
    __slots__ = ("role",)
    def __init__(self, role_obj: SlottedRole) -> None:
        self.role = role_obj


def test_permissions_request_missing_user_attribute(view_unused: object) -> None:
    # Current implementation accesses request.user.role.role unguarded.
    # We document that absence of 'user' leads to AttributeError.
    req = RequestWithoutUser()
    with pytest.raises(AttributeError):
        IsAdmin().has_permission(req, view_unused)
    with pytest.raises(AttributeError):
        IsDoctor().has_permission(req, view_unused)


@pytest.mark.parametrize(
    "role_value, expected_admin, expected_doctor",
    [
        ("admin", True, False),
        ("doctor", False, True),
    ],
)
def test_permissions_with_role_as_property(
    role_value: str,
    expected_admin: bool,
    expected_doctor: bool,
    view_unused: object,
) -> None:
    user = UserWithProperty(role_value)
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is expected_admin
    assert IsDoctor().has_permission(req, view_unused) is expected_doctor


def test_permissions_with_slotted_user_and_role(view_unused: object) -> None:
    user = SlottedUser(role_obj=SlottedRole("doctor"))
    req = FakeRequest(user=user)
    assert IsDoctor().has_permission(req, view_unused) is True
    assert IsAdmin().has_permission(req, view_unused) is False


@pytest.mark.parametrize(
    "val",
    [123, 0, 1, True, False, b"admin", b"doctor", [], {}, object()],
)
def test_permissions_with_non_string_role_values(val: object, view_unused: object) -> None:
    # Non-string values should not match exact string checks
    user = Obj(role=Obj(role=val))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_with_leading_whitespace_role(view_unused: object) -> None:
    user = Obj(role=Obj(role=" admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, view_unused) is False
    assert IsDoctor().has_permission(req, view_unused) is False


def test_permissions_dict_like_user_raises_attribute_error(view_unused: object) -> None:
    # Dicts don't provide attribute access; document current AttributeError behavior
    user = {"role": {"role": "admin"}}
    req = FakeRequest(user=user)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        IsAdmin().has_permission(req, view_unused)
    with pytest.raises(AttributeError):
        IsDoctor().has_permission(req, view_unused)


def test_permissions_when_view_is_none() -> None:
    # Sanity: view parameter should be unused by these permissions
    user = Obj(role=Obj(role="admin"))
    req = FakeRequest(user=user)
    assert IsAdmin().has_permission(req, None) is True
    assert IsDoctor().has_permission(req, None) is False