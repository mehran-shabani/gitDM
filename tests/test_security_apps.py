"""Tests for security.apps.SecurityConfig.

Testing library/framework:
- pytest (preferred)
- If pytest-django is configured in the project,
  these tests will still run without relying on database markers.

Scope:
- Focused on AppConfig public interface per the diff.
- Views/serializers/models/services are intentionally out-of-scope for this file.

Conventions:
- Pure unit tests that do not require the Django app registry to be populated.
"""
import importlib
import types
import pytest
from pathlib import Path

# Import the class under test
try:
    from security.apps import SecurityConfig
except Exception as exc:  # pragma: no cover
    # import error should be explicit in failure
    pytest.fail(f"Failed to import SecurityConfig from security.apps: {exc}")


def test_security_config_class_is_subclass_of_appconfig() -> None:
    from django.apps import AppConfig
    assert issubclass(SecurityConfig, AppConfig), (
        "SecurityConfig must subclass "
        "django.apps.AppConfig"
    )


def test_security_config_name_constant() -> None:
    # Validate the configured Django app name is exact
    assert getattr(SecurityConfig, "name", None) == "security"


def test_security_config_default_auto_field_is_bigautofield() -> None:
    expected = "django.db.models.BigAutoField"
    actual = getattr(SecurityConfig, "default_auto_field", None)
    assert actual == expected, (
        f"default_auto_field should be {expected}, got {actual!r}"
    )


def test_security_config_instance_has_expected_label_and_name_without_registry() \
    -> None:
    """
    AppConfig.label defaults to the last component of 'name' if not explicitly set.
    We instantiate with a minimal module to avoid touching Django's app registry.
    """
    # Simulate a minimal module object for the app.
    # AppConfig expects a module object, not a string.
    mod = types.ModuleType("security")
    cfg = SecurityConfig("security", mod)
    assert cfg.name == "security"
    assert cfg.label == "security"
    # 'path' is derived from module.__file__ if present.
    # Ensure absence doesn't break attribute access.
    assert hasattr(cfg, "path")


@pytest.mark.parametrize(
    "bad_name",
    [None, "", 123, object()],
)
def test_security_config_rejects_invalid_name_types(bad_name: object) -> None:
    """
    Defensive test: constructing with invalid 'app_name'
    should raise TypeError/ValueError per Django AppConfig contract.
    """
    mod = types.ModuleType("security")
    with pytest.raises((TypeError, ValueError)):
        SecurityConfig(bad_name, mod)


def test_security_config_module_must_be_module_object() -> None:
    """
    Defensive test: AppConfig expects a module object.
    Passing a string or None should raise.
    """
    with pytest.raises(TypeError):
        SecurityConfig("security", "security")
    with pytest.raises(TypeError):
        SecurityConfig("security", None)


def test_security_config_importable_and_module_reloads_cleanly() -> None:
    """
    Ensure module import idempotence: reloading should not alter class attributes.
    """
    before_default = getattr(SecurityConfig, "default_auto_field", None)
    before_name = getattr(SecurityConfig, "name", None)
    mod = importlib.import_module("security.apps")
    importlib.reload(mod)
    reloaded = getattr(mod, "SecurityConfig", None)
    assert reloaded is SecurityConfig or reloaded.__name__ == "SecurityConfig"
    assert getattr(reloaded, "default_auto_field", None) == before_default
    assert getattr(reloaded, "name", None) == before_name


def test_security_config_module_and_class_attributes_are_present_and_types_valid() \
    -> None:
    # Basic sanity checks on class-level attributes
    assert hasattr(SecurityConfig, "name"), "SecurityConfig.name must exist"
    assert isinstance(SecurityConfig.name, str), "SecurityConfig.name must be a string"
    # default_auto_field should be explicitly set to BigAutoField path
    assert (
        getattr(SecurityConfig, "default_auto_field", None)
        == "django.db.models.BigAutoField"
    )


def test_security_config_path_derives_from_module_dunder_file_when_present(
    tmp_path: Path,
) -> None:
    """
    When app module has __file__, AppConfig.path should be the directory of that file.
    This is a pure unit test without touching Django's app registry.
    """
    pkg_dir = tmp_path / "security"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    fake_init = pkg_dir / "__init__.py"
    fake_init.write_text("# fake app package")
    mod = types.ModuleType("security")
    mod.__file__ = str(fake_init)
    cfg = SecurityConfig("security", mod)
    # Path may be absolute, normalize and compare suffix to avoid platform differences
    assert Path(cfg.path).resolve() == pkg_dir.resolve()


@pytest.mark.parametrize(
    "file_value, expect_has_path",
    [
        # Django still assigns a path (current working directory)
        # even if __file__ missing
        (None, True),
        # Falsy string should still lead to a path attribute being present
        ("", True),
    ],
)
def test_security_config_has_path_even_when_module_file_missing_or_empty(
    file_value: object,
    expect_has_path: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = types.ModuleType("security")
    if file_value is not None:
        mod.__file__ = file_value  # simulate odd module states
    cfg = SecurityConfig("security", mod)
    assert hasattr(cfg, "path") is expect_has_path
    # Ensure it's at least a readable string
    assert isinstance(getattr(cfg, "path", ""), str)


def test_security_config_label_defaults_to_last_component_of_name() -> None:
    mod = types.ModuleType("security")
    cfg = SecurityConfig("security", mod)
    assert cfg.label == "security"


def test_security_config_custom_label_when_overridden_via_subclass() -> None:
    class CustomLabelConfig(SecurityConfig):
        label = "sec"

    mod = types.ModuleType("security")
    cfg = CustomLabelConfig("security", mod)
    assert cfg.label == "sec"


def test_security_config_ready_method_is_callable_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    If SecurityConfig overrides ready(), calling it twice should not crash.
    This test doesn't validate side-effects; only that it's safe and callable.
    """
    mod = types.ModuleType("security")
    cfg = SecurityConfig("security", mod)

    # If ready is not overridden by SecurityConfig, it falls back to
    # AppConfig.ready which is a no-op.
    assert callable(cfg.ready)
    # Call twice to ensure idempotence/no exception
    cfg.ready()
    cfg.ready()


def test_security_config_import_module_reload_keeps_critical_attributes() -> None:
    before_default = getattr(SecurityConfig, "default_auto_field", None)
    before_name = getattr(SecurityConfig, "name", None)
    mod = importlib.import_module("security.apps")
    importlib.reload(mod)
    reloaded = getattr(mod, "SecurityConfig", None)
    assert (
        reloaded is SecurityConfig
        or getattr(reloaded, "__name__", "") == "SecurityConfig"
    )
    assert getattr(reloaded, "default_auto_field", None) == before_default
    assert getattr(reloaded, "name", None) == before_name


def test_security_config_rejects_non_module_app_module() -> None:
    with pytest.raises(TypeError):
        SecurityConfig("security", "security")
    with pytest.raises(TypeError):
        SecurityConfig("security", None)


def test_security_config_name_is_exact_security() -> None:
    assert getattr(SecurityConfig, "name", None) == "security"