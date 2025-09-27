"""Unit tests for OwnedByCurrentDoctorQuerysetMixin."""

from types import SimpleNamespace

import pytest
from rest_framework.exceptions import PermissionDenied

from security.mixins import OwnedByCurrentDoctorQuerysetMixin


class DummyQuerySet:
    """Minimal stand-in for a Django QuerySet used by the mixin."""

    def __init__(self) -> None:
        self.none_called = False
        self.filter_kwargs: dict | None = None
        self.none_return = object()
        self.filter_return = object()

    def none(self):
        self.none_called = True
        return self.none_return

    def filter(self, **kwargs):
        self.filter_kwargs = kwargs
        return self.filter_return


class _BaseView:
    def __init__(self, queryset: DummyQuerySet) -> None:
        self._base_qs = queryset

    def get_queryset(self):  # pragma: no cover - invoked via super()
        return self._base_qs


class ViewUnderTest(OwnedByCurrentDoctorQuerysetMixin, _BaseView):
    """Concrete class combining the mixin with a stub base view."""

    pass


@pytest.fixture()
def mixin_view():
    qs = DummyQuerySet()
    view = ViewUnderTest(qs)
    return view, qs


class DummyUser:
    """Lightweight user object with identity-based equality."""

    def __init__(
        self,
        *,
        is_authenticated: bool = True,
        is_superuser: bool = False,
        identifier: object | None = None,
    ) -> None:
        self.is_authenticated = is_authenticated
        self.is_superuser = is_superuser
        # identifier helps us distinguish different users in assertions
        self.identifier = identifier if identifier is not None else object()


def _make_user(*, is_authenticated=True, is_superuser=False, identifier=None):
    return DummyUser(
        is_authenticated=is_authenticated,
        is_superuser=is_superuser,
        identifier=identifier,
    )


class DummySerializer:
    def __init__(self, patient):
        self.validated_data = {"patient": patient}


def test_get_queryset_returns_empty_for_anonymous_user(mixin_view):
    view, qs = mixin_view
    view.request = SimpleNamespace(user=_make_user(is_authenticated=False))

    result = view.get_queryset()

    assert result is qs.none_return
    assert qs.none_called is True
    assert qs.filter_kwargs is None


def test_get_queryset_returns_base_for_superuser(mixin_view):
    view, qs = mixin_view
    view.request = SimpleNamespace(user=_make_user(is_superuser=True))

    result = view.get_queryset()

    assert result is qs
    assert qs.none_called is False
    assert qs.filter_kwargs is None


def test_get_queryset_filters_by_primary_doctor(mixin_view):
    view, qs = mixin_view
    doctor = _make_user()
    view.request = SimpleNamespace(user=doctor)

    result = view.get_queryset()

    assert result is qs.filter_return
    assert qs.filter_kwargs == {"patient__primary_doctor": doctor}
    assert qs.none_called is False


def test_enforce_patient_ownership_allows_matching_doctor(mixin_view):
    view, _ = mixin_view
    doctor = _make_user()
    patient = SimpleNamespace(primary_doctor=doctor)
    view.request = SimpleNamespace(user=doctor)
    serializer = DummySerializer(patient=patient)

    view.enforce_patient_ownership(serializer)


def test_enforce_patient_ownership_raises_for_other_doctor(mixin_view):
    view, _ = mixin_view
    current_doctor = _make_user(identifier="current")
    other_doctor = _make_user(identifier="other")
    patient = SimpleNamespace(primary_doctor=other_doctor)
    view.request = SimpleNamespace(user=current_doctor)
    serializer = DummySerializer(patient=patient)

    with pytest.raises(PermissionDenied):
        view.enforce_patient_ownership(serializer)


def test_enforce_patient_ownership_ignores_missing_patient(mixin_view):
    view, _ = mixin_view
    doctor = _make_user()
    view.request = SimpleNamespace(user=doctor)
    serializer = DummySerializer(patient=None)

    view.enforce_patient_ownership(serializer)
