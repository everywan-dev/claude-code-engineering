"""Sanity checks for the Claude Code plugin manifest and the version."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _manifest():
    manifest_path = REPO_ROOT / ".claude-plugin" / "plugin.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def test_plugin_manifest_is_valid_json_with_identity():
    manifest = _manifest()
    assert manifest["name"] == "validated-memory"
    assert manifest["version"]
    assert manifest["description"]


def test_the_version_agrees_across_the_three_places_it_is_written():
    # Read as text rather than imported: these tests never import the
    # package's internals (see CLAUDE.md).
    package = (REPO_ROOT / "validated_memory" / "__init__.py").read_text(
        encoding="utf-8"
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    package_version = re.search(
        r'^__version__ = "([^"]+)"', package, re.MULTILINE
    ).group(1)
    pyproject_version = re.search(
        r'^version = "([^"]+)"', pyproject, re.MULTILINE
    ).group(1)

    assert package_version == pyproject_version == _manifest()["version"]
