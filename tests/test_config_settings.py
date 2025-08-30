import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
import types
import pytest
from django.core.exceptions import ImproperlyConfigured

# Testing library and framework:
# Using pytest (with built-in monkeypatch fixture).
# Tests are pure unit tests and do not require pytest-django.

SETTINGS_IMPORT_PATH = os.environ.get("TEST_SETTINGS_IMPORT_PATH", "config.settings")

@contextmanager
def fresh_import_with_env(env: dict) -> None:
    """
    روند واردسازی تازهٔ ماژول تنظیمات با محیط موقت را فراهم می‌کند و پس از خروج محیط و کش ماژول را بازیابی می‌کند.
    
    این کانتکست‌منیجر:
    - به‌صورت موقت os.environ را با دیکشنری env جایگزین می‌کند تا ماژول تنظیمات با آن متغیرهای محیطی ارزیابی شود.
    - هر نمونهٔ قبلی از ماژول مشخص‌شده (SETTINGS_IMPORT_PATH) را از sys.modules حذف می‌کند تا واردسازی جدید اطمیناناً دوباره ارزیابی شود.
    - ماژول واردشده را به فراخوان بازمی‌گرداند (yield) تا تست‌ها یا کد فراخوان بتوانند به محتوای ماژول دسترسی داشته باشند.
    - در خروج (حتی در صورت بروز استثناء) محیط اصلی را دقیقاً بازمی‌گرداند و هر ماژول نیمه‌مقداری که ممکن است باقی مانده باشد را حذف می‌کند تا از اثرات جانبی بر سایر تست‌ها جلوگیری شود.
    
    پارامترها:
        env (dict): نگاشت نام متغیرهای محیطی به مقادیرشان که در طول مدت کانتکست باید اعمال شود.
    
    مقدار بازگشتی:
        ماژول واردشده (module): ماژول تنظیمات تازه واردشده که داخل بلوک کانتکست قابل استفاده است.
    
    رفتارهای مهم:
    - هر استثنایی که در زمان واردسازی ماژول رخ دهد از این کانتکست برمی‌گردد (propagates) و مسئول رسیدگی به آن فراخوان است.
    - این تابع تضمین می‌کند که پس از خروج هیچ‌یک از تغییرات محیط یا ماژول‌های موقتی در فضای نام باقی نماند.
    """
    original_env = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(env)
        # Ensure we don't carry a cached module across tests
        if SETTINGS_IMPORT_PATH in sys.modules:
            del sys.modules[SETTINGS_IMPORT_PATH]
        # Also drop parent package cache to avoid attribute caching issues
        pkg = SETTINGS_IMPORT_PATH.split(".")[0]
        if pkg in sys.modules and isinstance(sys.modules[pkg], types.ModuleType):
            # don't delete the package if other imports rely on it;
            # this is safe generally
            pass
        mod = importlib.import_module(SETTINGS_IMPORT_PATH)
        yield mod
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        # Do not leave a partially-initialized module around
        if SETTINGS_IMPORT_PATH in sys.modules:
            del sys.modules[SETTINGS_IMPORT_PATH]

def test_secret_key_defaults_in_debug_mode() -> None:
    # DJANGO_DEBUG true -> allow default insecure key when DJANGO_SECRET_KEY missing
    env = {
        "DJANGO_DEBUG": "True",
        # no DJANGO_SECRET_KEY
        # provide minimal env for allowed hosts default
        # (ALLOWED_HOSTS defaults in DEBUG so env not required)
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is True
        assert isinstance(s.SECRET_KEY, str) and s.SECRET_KEY, (
            "SECRET_KEY should default in DEBUG"
        )

def test_secret_key_required_in_production_raises() -> None:
    # With DJANGO_DEBUG false and missing secret => ImproperlyConfigured
    """
    تأیید می‌کند که وقتی DJANGO_DEBUG برابر False است و کلید مخفی (SECRET_KEY) وجود ندارد، وارد کردن ماژول تنظیمات باعث بالا آمدن استثنائی مرتبط با تنظیمات (مثل ImproperlyConfigured) می‌شود.
    
    شرح:
    - محیط آزمایشی با DJANGO_DEBUG="False" و یک مقدار برای DJANGO_ALLOWED_HOSTS تنظیم می‌شود تا خطای ناشی از نبود SECRET_KEY به طور ویژه بررسی شود.
    - از fresh_import_with_env برای وارد کردن تازهٔ ماژول تنظیمات و از pytest.raises برای انتظار ظهور استثنا استفاده می‌شود.
    - آزمون موفق است اگر هنگام وارد کردن تنظیمات استثناء پرتاب شود و پیام استثناء شامل رشته "SECRET_KEY" باشد.
    """
    env = {
        "DJANGO_DEBUG": "False",
        # Ensure ALLOWED_HOSTS provided so we isolate SECRET_KEY failure
        "DJANGO_ALLOWED_HOSTS": "example.com",
    }
    with pytest.raises(ImproperlyConfigured) as excinfo:
        with fresh_import_with_env(env):
            pass
    # Django's exception class is used
    assert "SECRET_KEY" in str(excinfo.value)

def test_allowed_hosts_default_in_debug() -> None:
    env = {
        "DJANGO_DEBUG": "True",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is True
        assert s.ALLOWED_HOSTS == ['localhost', '127.0.0.1']

def test_allowed_hosts_parsing_and_trimming() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod-secret",
        "DJANGO_ALLOWED_HOSTS": "  api.example.com , www.example.com,localhost  ",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is False
        assert s.ALLOWED_HOSTS == ["api.example.com", "www.example.com", "localhost"]

def test_database_always_sqlite() -> None:
    """
    اطمینان می‌دهد که تنظیمات پروژه همیشه از SQLite استفاده می‌کنند.
    
    این تست بررسی می‌کند که:
    - ENGINE کانکشن پیش‌فرض دیتابیس برابر "django.db.backends.sqlite3" باشد،
    - و مقدار NAME دیتابیس برابر با مسیر BASE_DIR / 'db.sqlite3' باشد.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        # Name should be BASE_DIR / 'db.sqlite3'
        expected = s.BASE_DIR / 'db.sqlite3'
        assert Path(s.DATABASES["default"]["NAME"]) == expected

def test_database_sqlite_in_production() -> None:
    """
    تأیید می‌کند که حتی در حالت production نیز از SQLite استفاده می‌شود.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
    }
    with fresh_import_with_env(env) as s:
        assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

def test_rest_framework_defaults() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        rf = s.REST_FRAMEWORK
        assert 'DEFAULT_AUTHENTICATION_CLASSES' in rf
        assert rf['DEFAULT_AUTHENTICATION_CLASSES'] == (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        )
        assert rf['DEFAULT_PERMISSION_CLASSES'] == (
            'rest_framework.permissions.IsAuthenticated',
        )
        assert rf['DEFAULT_SCHEMA_CLASS'] == 'drf_spectacular.openapi.AutoSchema'

def test_spectacular_settings_core_values() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        sp = s.SPECTACULAR_SETTINGS
        assert sp['SERVE_INCLUDE_SCHEMA'] is False
        assert isinstance(sp['TITLE'], str) and sp['TITLE']
        assert isinstance(sp['VERSION'], str) and sp['VERSION']

def test_simple_jwt_timeouts_and_rotation() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        jwt = s.SIMPLE_JWT
        from datetime import timedelta
        assert jwt['ACCESS_TOKEN_LIFETIME'] == timedelta(days=15)
        assert jwt['REFRESH_TOKEN_LIFETIME'] == timedelta(days=20)
        assert jwt['ROTATE_REFRESH_TOKENS'] is True

def test_static_files_configuration() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.STATIC_URL == '/static/'
        assert s.STATIC_ROOT == s.BASE_DIR / 'staticfiles'
        assert s.MEDIA_URL == '/media/'
        assert s.MEDIA_ROOT == s.BASE_DIR / 'media'
        assert s.DEFAULT_AUTO_FIELD == 'django.db.models.BigAutoField'

def test_caches_always_locmem() -> None:
    """
    تأیید می‌کند که کش همیشه از LocMemCache استفاده می‌کند.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES['default']
        assert caches['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'

@pytest.mark.parametrize(
    "value,expected",
    [
        ("TRUE", True),
        ("true", True),
        ("1", True),
        ("yes", True),
        ("False", False),
        ("0", False),
        ("no", False),
    ],
)
def test_debug_env_parsing_variants(value: str, expected: bool) -> None:
    # Provide minimum required env to allow module import
    """
    آزمونی پارامترایز شده که صحت پارس شدن مقدار محیطی DJANGO_DEBUG به بولین را بررسی می‌کند.
    
    این تست برای هر جفت (value, expected) یک محیط مینیمال می‌سازد که شامل:
    - DJANGO_DEBUG برابر value (رشته‌های مختلف معادل true/false نظیر "TRUE", "false", "1", "0" و غیره)
    - DJANGO_SECRET_KEY: در حالت توسعه (expected=True) مقدار کوتاه "x" و در حالت تولید مقدار "prod-secret"
    - در حالت تولید (expected=False) مقدار DJANGO_ALLOWED_HOSTS نیز اضافه می‌شود تا از خطاهای غیرمرتبط هنگام وارد کردن ماژول جلوگیری شود
    
    سپس با وارد کردن تازهٔ ماژول تنظیمات درون context manager مربوطه بررسی می‌کند که s.DEBUG با expected مطابقت دارد.
    
    Parameters:
        value (str): نمایش رشته‌ای مقدار DJANGO_DEBUG که باید پارس شود.
        expected (bool): نتیجهٔ بولینی مورد انتظار پس از پارس شدن value.
    """
    env = {
        "DJANGO_DEBUG": value,
        "DJANGO_SECRET_KEY": "x" if expected else "prod-secret",
        # If expected is False (production), ensure allowed hosts present to avoid unrelated failure
        **(
            {"DJANGO_ALLOWED_HOSTS": "example.com"} if not expected else {}
        ),
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is expected

def test_allowed_hosts_empty_string_in_debug_falls_back_to_defaults() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_ALLOWED_HOSTS": "",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        # Because ALLOWED_HOSTS_ENV is empty and DEBUG True
        assert s.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]

def test_codespaces_configuration() -> None:
    """
    تست تنظیمات GitHub Codespaces
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "CODESPACES": "true",
        "CODESPACE_NAME": "test-codespace",
        "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is True
        assert "test-codespace-8000.app.github.dev" in s.ALLOWED_HOSTS
        assert "https://test-codespace-8000.app.github.dev" in s.CSRF_TRUSTED_ORIGINS