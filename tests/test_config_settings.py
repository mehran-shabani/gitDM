# noqa: E501, PD006
import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
import types
import pytest

# Testing library and framework:
# Using pytest (with built-in monkeypatch fixture).
# Tests are pure unit tests and do not require pytest-django.

SETTINGS_IMPORT_PATH = os.environ.get("TEST_SETTINGS_IMPORT_PATH", "config.settings")

@contextmanager
def fresh_import_with_env(env: dict) -> None:
    """
    روند واردسازی تازهٔ ماژول تنظیمات با محیط موقت را فراهم می‌کند و پس از خروج محیط 
    و کش ماژول را بازیابی می‌کند.

    این کانتکست‌منیجر:
    - به‌صورت موقت os.environ را با دیکشنری env جایگزین می‌کند تا ماژول تنظیمات با 
      آن متغیرهای محیطی ارزیابی شود.
    - هر نمونهٔ قبلی از ماژول مشخص‌شده (SETTINGS_IMPORT_PATH) را از sys.modules حذف 
      می‌کند تا واردسازی جدید اطمیناناً دوباره ارزیابی شود.
    - ماژول واردشده را به فراخوان بازمی‌گرداند (yield) تا تست‌ها یا کد فراخوان بتوانند 
      به محتوای ماژول دسترسی داشته باشند.
    - در خروج (حتی در صورت بروز استثناء) محیط اصلی را دقیقاً بازمی‌گرداند و هر ماژول 
      نیمه‌مقداری که ممکن است باقی مانده باشد را حذف می‌کند تا از اثرات جانبی بر سایر 
      تست‌ها جلوگیری شود.

    پارامترها:
        env (dict): نگاشت نام متغیرهای محیطی به مقادیرشان که در طول مدت کانتکست باید 
        اعمال شود.

    مقدار بازگشتی:
        ماژول واردشده (module): ماژول تنظیمات تازه واردشده که داخل بلوک کانتکست قابل 
        استفاده است.

    رفتارهای مهم:
    - هر استثنایی که در زمان واردسازی ماژول رخ دهد از این کانتکست برمی‌گردد 
      (propagates) و مسئول رسیدگی به آن فراخوان است.
    - این تابع تضمین می‌کند که پس از خروج هیچ‌یک از تغییرات محیط یا ماژول‌های 
      موقتی در فضای نام باقی نماند.
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
    # With DJANGO_DEBUG false and missing secret => 'ImproperlyConfigured'
    """
    تأیید می‌کند که وقتی DJANGO_DEBUG برابر False است و کلید مخفی (SECRET_KEY) 
    وجود ندارد، وارد کردن ماژول تنظیمات باعث بالا آمدن استثنائی مرتبط با تنظیمات 
    (مثل 'ImproperlyConfigured') می‌شود.

    شرح:
    - محیط آزمایشی با DJANGO_DEBUG="False" و یک مقدار برای DJANGO_ALLOWED_HOSTS 
      تنظیم می‌شود تا خطای ناشی از نبود SECRET_KEY به طور ویژه بررسی شود.
    - از fresh_import_with_env برای وارد کردن تازهٔ ماژول تنظیمات و از pytest.raises 
      برای انتظار ظهور استثنا استفاده می‌شود.
    - آزمون موفق است اگر هنگام وارد کردن تنظیمات استثناء پرتاب شود و پیام 
      استثناء شامل رشته "SECRET_KEY" باشد.
    """
    env = {
        "DJANGO_DEBUG": "False",
        # Ensure ALLOWED_HOSTS provided so we isolate SECRET_KEY failure
        "DJANGO_ALLOWED_HOSTS": "example.com",
    }
    with pytest.raises(Exception) as excinfo:
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
        assert s.ALLOWED_HOSTS == ['localhost', '127.0.0.1', '[::1]']


def test_allowed_hosts_required_in_production_raises_when_missing_secret_is_ok() -> None:  # noqa: E501
    # Provide SECRET_KEY to isolate ALLOWED_HOSTS error; omit DJANGO_ALLOWED_HOSTS
    """
    تست می‌کند که وقتی برنامه در حالت production (DJANGO_DEBUG=False) است و متغیر 
    محیطی DJANGO_ALLOWED_HOSTS تنظیم نشده، وارد کردن ماژول تنظیمات استثنا 
    برمی‌انگیزد.

    جزئیات:
    - برای ایزوله کردن علت خطا، یک SECRET_KEY معتبر در محیط قرار داده می‌شود؛ 
      بنابراین هر استثنایی که رخ دهد باید مربوط به نبود ALLOWED_HOSTS باشد.
    - انتظار می‌رود که هنگام import تنظیمات یک Exception پرتاب شود و پیام آن 
      شامل رشته "ALLOWED_HOSTS" باشد.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod-secret",
    }
    with pytest.raises(Exception) as excinfo:
        with fresh_import_with_env(env):
            pass
    assert "ALLOWED_HOSTS" in str(excinfo.value)


def test_allowed_hosts_parsing_and_trimming() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod-secret",
        "DJANGO_ALLOWED_HOSTS": "  api.example.com , www.example.com,localhost  ",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is False
        assert s.ALLOWED_HOSTS == ["api.example.com", "www.example.com", "localhost"]


def test_use_sqlite_defaults_true_when_debug_true_and_sqlite_config() -> None:
    """
    اطمینان می‌دهد که وقتی متغیر محیطی DJANGO_DEBUG برابر با True و 
    DJANGO_SECRET_KEY مقداردهی شده است، تنظیمات پروژه به‌صورت پیش‌فرض از SQLite 
    استفاده می‌کنند.

    این تست با قرار دادن محیط لازم و وارد کردن تازهٔ ماژول تنظیمات 
    (از طریق fresh_import_with_env) بررسی می‌کند که:
    - s.USE_SQLITE برابر True باشد،
    - ENGINE کانکشن پیش‌فرض دیتابیس برابر "django.db.backends.sqlite3" باشد،
    - و مقدار NAME دیتابیس برابر با مسیر BASE_DIR / 'db.sqlite3' باشد.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is True
        assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        # Name should be BASE_DIR / 'db.sqlite3'
        expected = s.BASE_DIR / 'db.sqlite3'
        assert Path(s.DATABASES["default"]["NAME"]) == expected


def test_use_sqlite_defaults_false_when_debug_false_and_postgres_config() -> None:
    """
    تأیید می‌کند که وقتی حالت DEBUG غیرفعال است و متغیر محیطی USE_SQLITE 
    تنظیم نشده است، پیکربندی پایگاه‌داده به‌صورت پیش‌فرض روی PostgreSQL قرار 
    می‌گیرد.

    شرح:
    - با قرار دادن محیطی شامل DJANGO_DEBUG=False، DJANGO_SECRET_KEY و 
      DJANGO_ALLOWED_HOSTS، ماژول تنظیمات تازه وارد شده بررسی می‌شود.
    - انتظار می‌رود s.USE_SQLITE برابر False باشد.
    - s.DATABASES['default'] باید از موتور "django.db.backends.postgresql" استفاده 
      کند و مقادیر پیش‌فرض اتصال (NAME, USER, PASSWORD, HOST, PORT) برابر با 
      مقادیر مورد انتظار ("diabetes", "diabetes", "diabetes", "127.0.0.1", "5432") 
      باشد.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is False
        db = s.DATABASES["default"]
        assert db["ENGINE"] == "django.db.backends.postgresql"
        assert db["NAME"] == "diabetes"
        assert db["USER"] == "diabetes"
        assert db["PASSWORD"] == "diabetes"
        assert db["HOST"] == "127.0.0.1"
        assert db["PORT"] == "5432"


def test_use_sqlite_can_be_forced_true_in_production() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        "USE_SQLITE": "yes",
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is True
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
        assert sp['SCHEMA_PATH_PREFIX'] == '/api'
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
        assert jwt['ACCESS_TOKEN_LIFETIME'] == timedelta(minutes=60)
        assert jwt['REFRESH_TOKEN_LIFETIME'] == timedelta(days=1)
        assert jwt['ROTATE_REFRESH_TOKENS'] is True


def test_system_user_is_none_and_static_root_path() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.SYSTEM_USER_ID is None
        assert s.STATIC_URL == '/static/'
        assert s.STATIC_ROOT == s.BASE_DIR / 'staticfiles'
        assert s.DEFAULT_AUTO_FIELD == 'django.db.models.BigAutoField'


def test_caches_locmem_when_no_redis_url() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES['default']
        assert caches['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'


def test_caches_redis_when_url_provided() -> None:
    """
    آزمون می‌کند که وقتی متغیر محیطی `REDIS_URL` تنظیم شده باشد، تنظیمات کش 
    به‌درستی برای استفاده از Redis پیکربندی می‌شوند.

    جزئیات: با قرار دادن `DJANGO_DEBUG=True` و یک `DJANGO_SECRET_KEY` و مقدار 
    `REDIS_URL`، ماژول تنظیمات به‌صورت تازه وارد می‌شود و سپس بررسی می‌شود که 
    CACHES['default']:
    - از بک‌اند `django_redis.cache.RedisCache` استفاده کند،
    - مقدار `LOCATION` برابر با مقدار `REDIS_URL` باشد،
    - و در `OPTIONS`، `CLIENT_CLASS` برابر با `django_redis.client.DefaultClient` باشد.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "REDIS_URL": "redis://localhost:6379/1",
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES['default']
        assert caches['BACKEND'] == 'django_redis.cache.RedisCache'
        assert caches['LOCATION'] == "redis://localhost:6379/1"
        assert caches['OPTIONS']['CLIENT_CLASS'] == 'django_redis.client.DefaultClient'


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
    آزمونی پارامترایز شده که صحت پارس شدن مقدار محیطی DJANGO_DEBUG به بولین 
    را بررسی می‌کند.

    این تست برای هر جفت (value, expected) یک محیط مینیمال می‌سازد که شامل:
    - DJANGO_DEBUG برابر value (رشته‌های مختلف معادل true/false نظیر "TRUE", 
      "false", "1", "0" و غیره)
    - DJANGO_SECRET_KEY: در حالت توسعه (expected=True) مقدار کوتاه "x" و در 
      حالت تولید مقدار "prod-secret"
    - در حالت تولید (expected=False) مقدار DJANGO_ALLOWED_HOSTS نیز اضافه می‌شود 
      تا از خطاهای غیرمرتبط هنگام وارد کردن ماژول جلوگیری شود
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
        assert s.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "[::1]"]


def test_postgres_env_overrides_when_use_sqlite_false() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        "POSTGRES_DB": "mydb",
        "POSTGRES_USER": "myuser",
        "POSTGRES_PASSWORD": "mypass",
        "POSTGRES_HOST": "db.internal",
        "POSTGRES_PORT": "6543",
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is False
        db = s.DATABASES["default"]
        assert db["ENGINE"] == "django.db.backends.postgresql"
        assert db["NAME"] == "mydb"
        assert db["USER"] == "myuser"
        assert db["PASSWORD"] == "mypass"
        assert db["HOST"] == "db.internal"
        assert db["PORT"] == "6543"


# Additional tests appended by automation:
# Testing library/framework: pytest

def test_allowed_hosts_whitespace_only_in_production_raises() -> None:
    """
    When DJANGO_DEBUG=False and DJANGO_ALLOWED_HOSTS is provided
    as whitespace-only (which trims to empty), importing settings should raise.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "   ,   ,   ",
    }
    with pytest.raises(Exception) as excinfo:
        with fresh_import_with_env(env):
            pass
    assert "ALLOWED_HOSTS" in str(excinfo.value)


@pytest.mark.parametrize(
    "value,expected",
    [
        (" True ", True),
        (" False ", False),
        ("\ttrue\n", True),
        ("\tfalse\n", False),
    ],
)
def test_debug_env_parsing_with_whitespace_variants(value: str, expected: bool) -> None:
    """
    Verify DJANGO_DEBUG parsing tolerates surrounding whitespace and newlines.
    """
    env = {
        "DJANGO_DEBUG": value,
        "DJANGO_SECRET_KEY": "x" if expected else "prod",
        **({"DJANGO_ALLOWED_HOSTS": "example.com"} if not expected else {}),
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is expected


def test_cache_redis_with_rediss_scheme_supported_location_passthrough() -> None:
    """
    If REDIS_URL uses TLS (rediss://), ensure LOCATION is passed through and backend is Redis.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "REDIS_URL": "rediss://localhost:6380/2",
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES['default']
        assert caches['BACKEND'] == 'django_redis.cache.RedisCache'
        assert caches['LOCATION'] == "rediss://localhost:6380/2"
        # OPTIONS may or may not include SSL-specific flags; ensure dict is present
        assert isinstance(caches.get('OPTIONS', {}), dict)


def test_databases_sqlite_name_is_base_dir_join_db_sqlite3_when_forced_true_in_prod() -> None:
    """
    Re-assert invariant for sqlite DB name when USE_SQLITE is forced True in production.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        "USE_SQLITE": "true",
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is True
        assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        assert Path(s.DATABASES["default"]["NAME"]) == s.BASE_DIR / 'db.sqlite3'


def test_rest_framework_has_required_core_keys_even_if_extended_elsewhere() -> None:
    """
    Ensure critical DRF settings keys exist to prevent KeyError downstream.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        rf = s.REST_FRAMEWORK
        for key in ("DEFAULT_AUTHENTICATION_CLASSES", "DEFAULT_PERMISSION_CLASSES", "DEFAULT_SCHEMA_CLASS"):
            assert key in rf


def test_static_settings_are_consistent_paths() -> None:
    """
    Sanity check STATIC_URL format and STATIC_ROOT path coherence.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.STATIC_URL.endswith("/")
        # STATIC_ROOT should be an absolute path under BASE_DIR/staticfiles by default
        assert str(s.STATIC_ROOT).endswith("staticfiles")
        assert Path(s.STATIC_ROOT).is_absolute()


def test_csrf_trusted_origins_env_optional_when_debug_true() -> None:
    """
    If settings define CSRF_TRUSTED_ORIGINS, ensure it defaults safely in DEBUG or parses env when present.
    This test tolerates absence of the attribute for portability.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "DJANGO_ALLOWED_HOSTS": "",
    }
    with fresh_import_with_env(env) as s:
        if hasattr(s, "CSRF_TRUSTED_ORIGINS"):
            cto = s.CSRF_TRUSTED_ORIGINS
            # Should be a list (possibly empty)
            assert isinstance(cto, list | tuple)


def test_csrf_trusted_origins_parsing_when_provided() -> None:
    """
    When provided via env, ensure CSV parsing trims items.
    Tolerates settings without CSRF_TRUSTED_ORIGINS by skipping.
    """
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        "DJANGO_CSRF_TRUSTED_ORIGINS": " https://api.example.com ,https://www.example.com ",
    }
    with fresh_import_with_env(env) as s:
        if hasattr(s, "CSRF_TRUSTED_ORIGINS"):
            cto = s.CSRF_TRUSTED_ORIGINS
            assert list(cto) == ["https://api.example.com", "https://www.example.com"]


def test_default_auto_field_consistency_string() -> None:
    """
    Assert DEFAULT_AUTO_FIELD remains the big auto field for consistency.
    """
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEFAULT_AUTO_FIELD.endswith("BigAutoField")