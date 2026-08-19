"""Shared helpers for the end-to-end CLI tests.

Every test drives the CLI as a subprocess over a fixture adopter tree built in
a temporary directory. Nothing here imports the package's internals.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def run_cli():
    """Return a callable that invokes the CLI as a subprocess."""

    def _run(*args, cwd):
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        return subprocess.run(
            [sys.executable, "-m", "validated_memory", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            check=False,
        )

    return _run


@pytest.fixture
def adopter_dir(tmp_path):
    """Minimal adopter fixture: an empty project directory."""
    return tmp_path


@pytest.fixture
def write_document(adopter_dir):
    """Return a callable that writes a frontmatter document into the fixture tree."""

    def _write(relative_path, frontmatter, body="Document body.\n"):
        path = adopter_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + frontmatter + "---\n\n" + body, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def write_unit(write_document):
    """Return a callable that writes a curated-knowledge unit under `knowledge/`."""

    def _write(name, frontmatter, body="Unit body.\n"):
        return write_document(f"knowledge/{name}", frontmatter, body)

    return _write


@pytest.fixture
def write_memory(write_document):
    """Return a callable that writes an agent-memory file under `memory/`."""

    def _write(name, frontmatter, body="Memory body.\n"):
        return write_document(f"memory/{name}", frontmatter, body)

    return _write


@pytest.fixture
def write_probe(adopter_dir):
    """Return a callable that writes a fake probe script and its command.

    The script is plain Python, invoked through the interpreter
    (`sys.executable script.py`) -- so no shebang or `chmod +x` is needed.
    The returned command is exactly what a `probes:` entry in
    `validated-memory.md` would register: split with `shlex.split` and run
    without a shell.
    """

    def _write(relative_path, source):
        path = adopter_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return f"{sys.executable} {path.as_posix()}"

    return _write


@pytest.fixture
def write_index(adopter_dir):
    """Return a callable that writes the agent-memory index at `memory/MEMORY.md`."""

    def _write(text):
        path = adopter_dir / "memory" / "MEMORY.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return _write
