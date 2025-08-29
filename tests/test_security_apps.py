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
from typing import Optional

# Import the class under test
try:
    from security.apps import SecurityConfig
except Exception as exc:  # pragma: no cover
    # import error should be explicit in failure
    pytest.fail(f"Failed to import SecurityConfig from security.apps: {exc}")


def test_security_config_class_is_subclass_of_appconfig() -> None:
    """
    بررسی می‌کند که کلاس SecurityConfig زیرکلاس
    django.apps.AppConfig باشد.

    اگر SecurityConfig از AppConfig ارث‌بری نکرده باشد،
    تست شکست می‌خورد و پیام خطای مناسبی نشان داده می‌شود.
    """
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
    تست می‌کند که در غیاب رجیستری جنگو، مقدار پیش‌فرض label از
    مؤلفهٔ آخر نام اپ گرفته می‌شود و ایجاد یک نمونهٔ
    SecurityConfig با یک ماژول حداقلی (ModuleType) بدون نیاز به
    رجیستری کار می‌کند.

    این تست نام و برچسب (name و label) را برابر "security" انتظار
    دارد و بررسی می‌کند که صفت `path` بدون وجود `__file__` روی
    ماژول دسترسی‌پذیر باشد.
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
    تست می‌کند که هنگام ساخت یک SecurityConfig با مقدار نامعتبر
    برای آرگومان app_name، یک TypeError یا ValueError پرتاب می‌شود.

    شرح:
    - از یک شیء ماژول مصنوعی (types.ModuleType) با نام "security" به
      عنوان آرگومان module استفاده می‌کند تا از وابستگی به رجیستری
      اپ‌های جنگو جلوگیری شود.
    - انتظار می‌رود مقادیر نامعتبر (مثلاً None، رشتهٔ خالی، عدد یا هر
      شئ نامربوط) باعث بروز TypeError یا ValueError شوند.
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
    Ensure module import idempotence: reloading should not alter class
    attributes.
    """
    before_default = getattr(SecurityConfig, "default_auto_field", None)
    before_name = getattr(SecurityConfig, "name", None)
    mod = importlib.import_module("security.apps")
    importlib.reload(mod)
    reloaded = getattr(mod, "SecurityConfig", None)
    assert reloaded is SecurityConfig or reloaded.__name__ == "SecurityConfig"
    assert getattr(reloaded, "default_auto_field", None) == before_default
    assert getattr(reloaded, "name", None) == before_name


# --- additional SecurityConfig unit tests (auto-generated) ---
try:
    from security.apps import SecurityConfig
except Exception as exc:  # pragma: no cover
    pytest.fail(f"Failed to import SecurityConfig from security.apps: {exc}")


def test_security_config_has_expected_class_attributes_idempotent() -> None:
    """
    Ensures class-level constants remain stable:
    - name == "security"
    - default_auto_field == "django.db.models.BigAutoField"
    - optional verbose_name (if present) is a non-empty string
    """
    assert SecurityConfig.name == "security"
    assert (
        SecurityConfig.default_auto_field
        == "django.db.models.BigAutoField"
    )
    if hasattr(SecurityConfig, "verbose_name"):
        v = SecurityConfig.verbose_name
        assert isinstance(v, str) and v.strip(), (
            "verbose_name, if defined, must be a non-empty string"
        )


@pytest.mark.parametrize(
    "module_has_file, filename",
    [
        (False, None),
        (True, "/opt/app/security/__init__.py"),
    ],
)
def test_instance_path_resolution_with_and_without_module_file(
    module_has_file: bool, filename: Optional[str]
) -> None:
    """
    AppConfig.path is derived from module.__file__ when present.
    Ensure SecurityConfig instance:
    - exposes .path attribute
    - handles absence of __file__
    """
    mod = types.ModuleType("security")
    if module_has_file:
        mod.__file__ = filename
    cfg = SecurityConfig("security", mod)
    assert hasattr(cfg, "path")
    # When __file__ provided, path should contain the directory portion
    if module_has_file:
        assert cfg.path and isinstance(cfg.path, str)
        assert cfg.path != filename  # path should be a directory, not a file


def test_ready_method_is_callable_if_defined_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    If SecurityConfig defines ready(), calling it should not raise and
    can be called twice safely.

    If not defined, calling default AppConfig.ready() is still a no-op.
    """
    mod = types.ModuleType("security")
    cfg = SecurityConfig("security", mod)

    # If subclass overrides ready, call twice to ensure idempotence
    ready = getattr(cfg, "ready", None)
    assert callable(ready), (
        "SecurityConfig.ready should be callable "
        "(inherited or overridden)."
    )
    # Some ready() implementations import submodules; simulate a benign
    # environment by ensuring ImportError in ready() would surface.
    ready()
    # Call again to ensure no duplicate side-effects or exceptions
    ready()


@pytest.mark.parametrize(
    "bad_module",
    [
        "security",  # str instead of module
        123,  # number
        object(),  # arbitrary object
    ],
)
def test_constructor_rejects_non_module_for_module_arg(bad_module: object) -> None:
    with pytest.raises(TypeError):
        SecurityConfig("security", bad_module)


@pytest.mark.parametrize(
    "bad_name",
    [
        None,
        "",
        123,
        object(),
        "white space ",  # Django rejects invalid app labels; construction
                        # may fail in different ways
    ],
)
def test_constructor_rejects_invalid_app_name_types_or_values(
    bad_name: object,
) -> None:
    mod = types.ModuleType("security")
    with pytest.raises((TypeError, ValueError)):
        SecurityConfig(bad_name, mod)


def test_module_reload_preserves_securityconfig_identity_and_attributes() -> None:
    """
    Reloading security.apps should retain SecurityConfig attributes.
    """
    before_default = getattr(SecurityConfig, "default_auto_field", None)
    before_name = getattr(SecurityConfig, "name", None)

    mod = importlib.import_module("security.apps")
    importlib.reload(mod)

    after_cls = getattr(mod, "SecurityConfig", None)
    assert (
        after_cls is SecurityConfig
        or getattr(after_cls, "__name__", None) == "SecurityConfig"
    )
    assert getattr(after_cls, "default_auto_field", None) == before_default
    assert getattr(after_cls, "name", None) == before_name


def test_string_representation_contains_label_or_name() -> None:
    """
    __str__ of AppConfig commonly returns label; ensure str(cfg) contains
    'security'.

    Avoid tying to exact Django internal formatting.
    """
    mod = types.ModuleType("security")
    cfg = SecurityConfig("security", mod)
    s = str(cfg)
    assert "security" in s.lower()