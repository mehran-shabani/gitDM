"""
Tests for security.apps.SecurityConfig.

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

def test_security_config_instance_has_expected_label_and_name_without_registry() -> None:
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
    import types
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