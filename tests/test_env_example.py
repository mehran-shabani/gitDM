"""
Tests for the environment example configuration.

Testing library/framework:
- Prefer pytest if present (tests use plain asserts and are pytest-friendly).
- Tests also remain compatible with Python's builtin unittest (no pytest-only features used).

Focus:
- Validate required keys exist.
- Validate value shapes/types (booleans, integers, URLs, host lists).
- Validate acceptable placeholders and sane defaults.
- Validate port ranges and endpoint formats.

Note:
- These tests primarily target the .env example content included in the PR diff.
- If a real .env.example file exists in the repo, we validate it too.
"""

import re
from pathlib import Path

# Source content from the PR diff (kept in-sync with the provided snippet)
PR_DIFF_ENV_CONTENT = """
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL settings (external database)
POSTGRES_DB=diabetes
POSTGRES_USER=diabetes
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432

# Redis settings (external Redis)
REDIS_URL=redis://your-redis-host:6379/0

# MinIO settings (external MinIO)
MINIO_ENDPOINT=your-minio-host:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_USE_HTTPS=False
MINIO_MEDIA_BUCKET=media
MINIO_STATIC_BUCKET=static
""".strip() + "\n"

REQUIRED_KEYS = [
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "REDIS_URL",
    "MINIO_ENDPOINT",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "MINIO_USE_HTTPS",
    "MINIO_MEDIA_BUCKET",
    "MINIO_STATIC_BUCKET",
]

BOOL_KEYS = {"DJANGO_DEBUG", "MINIO_USE_HTTPS"}

def parse_env_lines(text: str) -> dict[str, str]:
    """
    Parse KEY=VALUE lines, ignoring comments and blank lines.
    Does not perform shell expansion; minimal, safe parser for validation.
    """
    env: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            # Skip malformed (we assert later that none are malformed)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        # Strip optional surrounding quotes
        if (len(value) >= 2) and ((value[0] == value[-1]) and value[0] in ("'", '"')):
            value = value[1:-1]
        env[key] = value
    return env

def is_bool_str(val: str) -> bool:
    return val in ("True", "False", "true", "false", "1", "0")

def to_bool(val: str) -> bool:
    return val in ("True", "true", "1")

def is_valid_port(val: str) -> bool:
    if not val.isdigit():
        return False
    n = int(val)
    return 1 <= n <= 65535

def split_hosts(val: str) -> list[str]:
    return [x.strip() for x in val.split(",") if x.strip()]

def is_hostname_or_ip(host: str) -> bool:
    # Very lightweight check: hostname labels or IPv4 dotted quad or 'localhost'
    if host == "localhost":
        return True
    ipv4 = re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)
    if ipv4:
        return all(0 <= int(part) <= 255 for part in host.split("."))
    # Hostname pattern per RFC 1123 (simplified)
    return bool(re.match(r"^(?=.{1,253}$)([a-zA-Z0-9-]{1,63}\.)*[a-zA-Z0-9-]{1,63}$", host))

def parse_endpoint_host_port(endpoint: str) -> tuple[str, int]:
    """
    Expect format 'host:port'
    """
    if ":" not in endpoint:
        raise ValueError("Endpoint must contain host:port")  # noqa
    host, port = endpoint.rsplit(":", 1)
    host = host.strip()
    port = port.strip()
    if not host or not is_valid_port(port):
        raise ValueError("Invalid host or port")  # noqa
    return host, int(port)

def is_redis_url(url: str) -> bool:
    return bool(re.match(r"^redis(s)?://[^/\s:]+(:\d+)?(/\d+)?$", url))

def _load_repo_env_example_candidates() -> list[Path]:
    """
    Find potential env example files in the repository.
    """
    candidates = []
    for name in (
        ".env.example",
        ".env.sample",
        ".env.dev.example",
        "env.example",
        "config/.env.example",
    ):
        p = Path(name)
        if p.exists() and p.is_file():
            candidates.append(p)
    # Also scan top-level files for env-like names
    for p in Path(".").glob(".env*"):
        if p.is_file():
            candidates.append(p)
    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for p in candidates:
        if p.resolve() not in seen:
            uniq.append(p)
            seen.add(p.resolve())
    return uniq

def _load_text_from(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""

def _validate_env_map(env: dict[str, str]) -> None:
    # 1) Required keys present
    for key in REQUIRED_KEYS:
        assert key in env, f"Missing required key: {key}"
    # 2) No empty values for critical keys
    for key in REQUIRED_KEYS:
        assert env[key] != "", f"Key {key} must not be empty"
    # 3) Boolean keys well-formed
    for key in BOOL_KEYS:
        assert is_bool_str(env[key]), (
            f"{key} must be a boolean-like string (True/False/1/0), got: {env[key]!r}"
        )
    # 4) Port validation
    assert is_valid_port(env["POSTGRES_PORT"]), (
        f"POSTGRES_PORT must be in 1..65535, got {env['POSTGRES_PORT']}"
    )
    # 5) Allowed hosts
    hosts = split_hosts(env["DJANGO_ALLOWED_HOSTS"])
    assert hosts, "DJANGO_ALLOWED_HOSTS must contain at least one host"
    for h in hosts:
        assert is_hostname_or_ip(h), f"Invalid host in DJANGO_ALLOWED_HOSTS: {h!r}"
    # 6) Redis URL
    assert is_redis_url(env["REDIS_URL"]), (
        f"REDIS_URL must be redis:// or rediss:// URL, got: {env['REDIS_URL']!r}"
    )
    # 7) MinIO endpoint format and buckets non-empty
    host, port = parse_endpoint_host_port(env["MINIO_ENDPOINT"])
    assert is_hostname_or_ip(host), f"MINIO_ENDPOINT host invalid: {host!r}"
    assert 1 <= port <= 65535, "MINIO_ENDPOINT port out of range"
    assert env["MINIO_MEDIA_BUCKET"], "MINIO_MEDIA_BUCKET cannot be empty"
    assert env["MINIO_STATIC_BUCKET"], "MINIO_STATIC_BUCKET cannot be empty"
    # 8) Placeholders sanity (ensure examples look like examples)
    assert "your-secret-key-here" in env["DJANGO_SECRET_KEY"], (
        "Example DJANGO_SECRET_KEY should be a placeholder"
    )
    assert env["POSTGRES_PASSWORD"].startswith("your-"), (
        "Example POSTGRES_PASSWORD should be a placeholder"
    )
    assert env["POSTGRES_HOST"].startswith("your-"), (
        "Example POSTGRES_HOST should be a placeholder"
    )
    assert env["MINIO_ACCESS_KEY"].startswith("your-"), (
        "Example MINIO_ACCESS_KEY should be a placeholder"
    )
    assert env["MINIO_SECRET_KEY"].startswith("your-"), (
        "Example MINIO_SECRET_KEY should be a placeholder"
    )

def test_pr_diff_env_example_is_valid_schema_and_values() -> None:
    """
    Validate the PR diff's env example content.
    """
    env = parse_env_lines(PR_DIFF_ENV_CONTENT)
    # Ensure there are no malformed lines (all non-comment, non-empty lines must have '=')
    for raw in PR_DIFF_ENV_CONTENT.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        assert "=" in s, f"Malformed line (missing '='): {raw!r}"
    _validate_env_map(env)

def test_real_env_example_files_if_present_are_valid() -> None:
    """
    If a real .env example file exists in the repository, validate it too.
    This makes the test suite useful both for the example and actual files.
    """
    candidates = _load_repo_env_example_candidates()
    if not candidates:
        # No env example files present; skip gracefully
        return
    # Validate each candidate independently
    for path in candidates:
        text = _load_text_from(path)
        if not text.strip():
            raise AssertionError(f"Env example file is empty: {path}")  # noqa
        env = parse_env_lines(text)
        # Basic shape: must contain at least the required keys
        missing = [k for k in REQUIRED_KEYS if k not in env]
        assert not missing, f"{path}: missing required keys: {missing}"
        # Validate types/shapes if the keys exist (be lenient with project-specific placeholders)
        _validate_env_map(env)

def test_edge_cases_parser_trims_quotes_and_whitespace() -> None:
    """
    Parser should handle quoted values and whitespace around '='.
    """
    sample = '''
    # comment
    KEY1 = "value with spaces"
    KEY2='single-quoted'
    KEY3=bare
    '''
    env = parse_env_lines(sample)
    assert env["KEY1"] == "value with spaces"
    assert env["KEY2"] == "single-quoted"
    assert env["KEY3"] == "bare"

def test_invalid_values_are_detected() -> None:
    """
    Ensure invalid shapes are caught by validators.
    """
    bad = PR_DIFF_ENV_CONTENT.replace("DJANGO_DEBUG=True", "DJANGO_DEBUG=notabool")
    env = parse_env_lines(bad)
    try:
        _validate_env_map(env)
        raise AssertionError("Expected boolean validation to fail")  # noqa
    except AssertionError as e:
        assert "DJANGO_DEBUG" in str(e)  # noqa

    bad2 = PR_DIFF_ENV_CONTENT.replace("POSTGRES_PORT=5432", "POSTGRES_PORT=99999")
    env2 = parse_env_lines(bad2)
    try:
        _validate_env_map(env2)
        raise AssertionError("Expected port range validation to fail")  # noqa
    except AssertionError as e:
        assert "POSTGRES_PORT" in str(e)  # noqa

    bad3 = PR_DIFF_ENV_CONTENT.replace(
        "REDIS_URL=redis://your-redis-host:6379/0",
        "REDIS_URL=http://example.com",
    )
    env3 = parse_env_lines(bad3)
    try:
        _validate_env_map(env3)
        raise AssertionError("Expected redis URL validation to fail")  # noqa
    except AssertionError as e:
        assert "REDIS_URL" in str(e)  # noqa

    bad4 = PR_DIFF_ENV_CONTENT.replace(
        "MINIO_ENDPOINT=your-minio-host:9000",
        "MINIO_ENDPOINT=bad-endpoint",
    )
    env4 = parse_env_lines(bad4)
    try:
        _validate_env_map(env4)
        raise AssertionError("Expected endpoint format validation to fail")  # noqa
    except ValueError as e:
        assert "MINIO_ENDPOINT" in str(e) or "Endpoint must contain host:port" in str(e)  # noqa

def test_allowed_hosts_parsing_and_validation() -> None:
    env = parse_env_lines(PR_DIFF_ENV_CONTENT)
    hosts = split_hosts(env["DJANGO_ALLOWED_HOSTS"])
    assert hosts == ["localhost", "127.0.0.1"]
    for h in hosts:
        assert is_hostname_or_ip(h)

def test_boolean_parsing_helper_accepts_common_forms() -> None:
    assert is_bool_str("True")
    assert is_bool_str("False")
    assert is_bool_str("true")
    assert is_bool_str("false")
    assert is_bool_str("1")
    assert is_bool_str("0")
    assert to_bool("True") is True
    assert to_bool("1") is True
    assert to_bool("False") is False

def test_port_validation_bounds_and_types() -> None:
    assert is_valid_port("1")
    assert is_valid_port("5432")
    assert is_valid_port("65535")
    assert not is_valid_port("0")
    assert not is_valid_port("65536")
    assert not is_valid_port("abc")

def test_parse_endpoint_host_port_happy_and_error() -> None:
    host, port = parse_endpoint_host_port("minio:9000")
    assert host == "minio"
    assert port == 9000

    try:
        parse_endpoint_host_port("minio")  # missing port
        raise AssertionError("Expected failure for missing port")  # noqa
    except ValueError:
        pass

    try:
        parse_endpoint_host_port("minio:abc")
        raise AssertionError("Expected failure for non-integer port")  # noqa
    except ValueError:
        pass