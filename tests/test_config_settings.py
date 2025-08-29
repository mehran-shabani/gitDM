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
    Temporarily patch environment and import the settings module fresh,
    forcing module-level code to re-evaluate.
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
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        # No USE_SQLITE provided -> expect Postgres
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is False
        db = s.DATABASES["default"]
        assert db["ENGINE"] == "django.db.backends.postgresql"
        # Defaults from env when not supplied
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
        # REDIS_URL omitted
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES['default']
        assert caches['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'


def test_caches_redis_when_url_provided() -> None:
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
    env = {
        "DJANGO_DEBUG": value,
        "DJANGO_SECRET_KEY": "x" if expected else "prod-secret",
        # If expected is False (production), ensure allowed hosts present to avoid unrelated failure  # noqa: E501
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
# ---------------------------------------------------------------------------
# Additional tests (pytest) focusing on env parsing, edge-cases and overrides.
# These extend coverage of the settings module without touching serializers/models.
# ---------------------------------------------------------------------------

def test_secret_key_pass_through_in_production() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "myprodsecret",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is False
        assert s.SECRET_KEY == "myprodsecret"

def test_allowed_hosts_ignores_empty_and_deduplicates() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": " api.example.com, , api.example.com , localhost, ,  ",
    }
    with fresh_import_with_env(env) as s:
        assert s.ALLOWED_HOSTS == ["api.example.com", "localhost"]

def test_allowed_hosts_empty_string_in_production_raises() -> None:
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "",
    }
    with pytest.raises(Exception) as excinfo:
        with fresh_import_with_env(env):
            pass
    assert "ALLOWED_HOSTS" in str(excinfo.value)

@pytest.mark.parametrize(
    "value, expected",
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
def test_use_sqlite_env_parsing_variants(value: str, expected: bool) -> None:
    # Run in production to avoid DEBUG-based defaults masking explicit USE_SQLITE
    env = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": "prod",
        "DJANGO_ALLOWED_HOSTS": "api.example.com",
        "USE_SQLITE": value,
    }
    with fresh_import_with_env(env) as s:
        assert s.USE_SQLITE is expected
        if expected:
            assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        else:
            assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

def test_use_sqlite_false_overrides_debug_true() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "USE_SQLITE": "False",
    }
    with fresh_import_with_env(env) as s:
        assert s.DEBUG is True
        assert s.USE_SQLITE is False
        assert s.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

@pytest.mark.parametrize("redis_url", ["", "   \t   "])
def test_caches_locmem_when_redis_url_blank_or_whitespace(redis_url: str) -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "REDIS_URL": redis_url,
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES["default"]
        assert caches["BACKEND"] == "django.core.cache.backends.locmem.LocMemCache"

def test_caches_redis_with_query_params() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "REDIS_URL": "redis://localhost:6379/1?ssl=false&timeout=1",
    }
    with fresh_import_with_env(env) as s:
        caches = s.CACHES["default"]
        assert caches["BACKEND"] == "django_redis.cache.RedisCache"
        assert caches["LOCATION"].startswith("redis://localhost:6379/1")
        assert "CLIENT_CLASS" in caches["OPTIONS"]

def test_system_user_id_parses_int_when_provided() -> None:
    env = {
        "DJANGO_DEBUG": "True",
        "DJANGO_SECRET_KEY": "dev",
        "SYSTEM_USER_ID": "42",
    }
    with fresh_import_with_env(env) as s:
        assert s.SYSTEM_USER_ID == 42