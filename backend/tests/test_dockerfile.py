# Test framework: pytest
# Purpose: Validate Dockerfile instructions introduced in the PR diff.
# Focus areas: base image, WORKDIR, dependency install, COPY order, ENV flags.

import re
from pathlib import Path
import pytest
import logging
from typing import Callable, Optional


@pytest.fixture(scope="module")
def dockerfile_text() -> str:
    """
    Prefer the root Dockerfile; if not present, find a Dockerfile that matches the PR base image.
    """
    root = Path("Dockerfile")
    if root.exists():
        try:
            return root.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            pytest.skip(f"Could not read root Dockerfile: {e}")

    for p in Path(".").rglob("Dockerfile"):
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            logging.getLogger(__name__).warning("Could not read Dockerfile %s: %s", p, e)
            continue
        if re.search(r"^\s*FROM\s+python:3\.11-slim\b", text, re.M):
            return text

    pytest.skip("No Dockerfile found containing 'FROM python:3.11-slim'.")


def _instructions(text: str) -> list[tuple[str, str]]:
    """
    Parse a simple Dockerfile into (INSTR, ARG) pairs, ignoring comments/blank lines.
    This is intentionally minimal to match the PR diff's simple file.
    """
    out: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z]+)\s+(.*)$", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def test_base_image_is_python_3_11_slim(dockerfile_text: str) -> None:
    assert re.search(r"^\s*FROM\s+python:3\.11-slim\b", dockerfile_text, re.M), \
        "Base image should be python:3.11-slim"


def test_workdir_set_to_app(dockerfile_text: str) -> None:
    assert re.search(r"^\s*WORKDIR\s+/app\s*$", dockerfile_text, re.M), \
        "WORKDIR should be /app"


def test_single_workdir_line(dockerfile_text: str) -> None:
    count = len(re.findall(r"^\s*WORKDIR\b", dockerfile_text, re.M))
    assert count == 1, "Expect exactly one WORKDIR instruction"


def test_copy_requirements_then_pip_install_then_copy_source(dockerfile_text: str) -> None:
    insns = _instructions(dockerfile_text)

    def find_index(predicate: Callable[[str, str], bool]) -> Optional[int]:
        for i, (ins, args) in enumerate(insns):
            if predicate(ins, args):
                return i
        return None

    idx_copy_reqs = find_index(lambda ins, args: ins == "COPY" and re.search(r"\brequirements\.txt\b", args))
    assert idx_copy_reqs is not None, "Expected 'COPY requirements.txt .' (or './') step"

    idx_run_pip = find_index(lambda ins, args: ins == "RUN" and re.search(r"\bpip\s+install\b", args))
    assert idx_run_pip is not None, "Expected 'RUN pip install ...' step"

    idx_copy_dot = find_index(lambda ins, args: ins == "COPY" and re.search(r"^\.\s+\.", args))
    assert idx_copy_dot is not None, "Expected 'COPY . .' step"

    assert idx_copy_reqs < idx_run_pip < idx_copy_dot, \
        "Order must be: COPY requirements.txt -> RUN pip install -> COPY . ."


def test_workdir_precedes_copy_and_run(dockerfile_text: str) -> None:
    insns = _instructions(dockerfile_text)

    idx_workdir = next((i for i, (ins, _) in enumerate(insns) if ins == "WORKDIR"), None)
    assert idx_workdir is not None, "WORKDIR instruction missing"

    first_copy = next((i for i, (ins, _) in enumerate(insns) if ins == "COPY"), None)
    first_run = next((i for i, (ins, _) in enumerate(insns) if ins == "RUN"), None)

    if first_copy is not None:
        assert idx_workdir < first_copy, "WORKDIR should come before COPY steps"
    if first_run is not None:
        assert idx_workdir < first_run, "WORKDIR should come before RUN steps"


def test_pip_install_uses_no_cache_dir_and_requirements(dockerfile_text: str) -> None:
    m = re.search(r"^\s*RUN\s+pip\s+install\s+([^\n]+)$", dockerfile_text, re.M)
    assert m, "Could not find 'RUN pip install' line"

    args = m.group(1)
    assert "--no-cache-dir" in args, "pip install should include --no-cache-dir"
    assert re.search(r"-r\s+requirements\.txt\b", args), "pip install should use '-r requirements.txt'"


def test_copy_requirements_destination_is_current_directory(dockerfile_text: str) -> None:
    assert re.search(r"^\s*COPY\s+requirements\.txt\s+\.(?:/)?\s*$", dockerfile_text, re.M), \
        "requirements.txt should be copied into current directory ('.' or './')"


def test_copy_source_uses_dot_to_dot(dockerfile_text: str) -> None:
    assert re.search(r"^\s*COPY\s+\.\s+\.\s*$", dockerfile_text, re.M), \
        "Source copy should be 'COPY . .'"


def test_env_sets_python_flags_and_is_single_line(dockerfile_text: str) -> None:
    # Expect one ENV with both variables set to 1
    env_lines = re.findall(r"^\s*ENV\s+(.+)$", dockerfile_text, re.M)
    assert env_lines, "Expected at least one ENV line"
    assert len(env_lines) == 1, "Expected exactly one ENV line"

    kvs = dict(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)", env_lines[0]))
    assert kvs.get("PYTHONDONTWRITEBYTECODE") == "1", "PYTHONDONTWRITEBYTECODE should be 1"
    assert kvs.get("PYTHONUNBUFFERED") == "1", "PYTHONUNBUFFERED should be 1"


def test_env_is_last_instruction(dockerfile_text: str) -> None:
    insns = _instructions(dockerfile_text)
    assert insns, "Dockerfile appears empty after parsing"
    last_instr, _ = insns[-1]
    assert last_instr == "ENV", "ENV should be the last instruction (as per PR diff)"


def test_no_add_instruction_is_used(dockerfile_text: str) -> None:
    assert not re.search(r"^\s*ADD\b", dockerfile_text, re.M), \
        "Prefer COPY over ADD for these use cases"