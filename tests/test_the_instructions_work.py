"""The instructions we give people have to be executable.

Three defects shipped at once, and all three were the same shape: a written
instruction nobody had ever run.

  1. The README told people to run `adopt validated-memory`. That skill had been
     renamed. The instruction pointed at nothing.
  2. Every example wrote `validated-memory <subcommand>` as if it were on the
     PATH. `pyproject.toml` declared no console script, so that command did not
     exist for anyone, by any install route.
  3. Installed as a plugin the CLI lives inside the plugin directory, so it is
     not on the PATH there either, and no page said how to invoke it.

None of these could fail a test, because there was no test. That is the whole
point of the repository, so it is worth being blunt: this file exists because we
did to ourselves exactly what the project is about.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SKILLS_DIR = REPO_ROOT / "skills"
DOCS_DIR = REPO_ROOT / "docs"


def test_the_console_script_is_declared():
    """Without this, `validated-memory` is a command that exists nowhere."""
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "[project.scripts]" in text, (
        "pyproject.toml declares no console script, so `validated-memory` never "
        "reaches the PATH and every example in the docs is unrunnable"
    )
    assert re.search(r"^validated-memory\s*=", text, re.M)


def test_the_console_script_points_at_something_callable():
    """Declaring an entry point that does not resolve is the same as not having one."""
    text = PYPROJECT.read_text(encoding="utf-8")
    target = re.search(r'^validated-memory\s*=\s*"([^"]+)"', text, re.M).group(1)
    module, _, function = target.partition(":")
    result = subprocess.run(
        [sys.executable, "-c",
         f"import {module} as m; assert callable(getattr(m, {function!r}))"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"the entry point {target!r} does not resolve: {result.stderr.strip()}"
    )


def test_the_module_form_runs_without_installing_anything():
    """`python3 -m validated_memory` is the form that works from the plugin."""
    result = subprocess.run(
        [sys.executable, "-m", "validated_memory", "route", "fix a typo"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Level 1" in result.stdout


def test_the_readme_quickstart_names_a_skill_that_exists():
    """The first thing anyone types after installing must not point at nothing."""
    text = README.read_text(encoding="utf-8")
    invocations = re.findall(r"^> use ([a-z][a-z0-9-]+)$", text, re.M)
    assert invocations, "the README no longer tells anyone what to run first"
    for name in invocations:
        assert (SKILLS_DIR / name).is_dir(), (
            f"the README tells people to run {name!r}, which is not a skill"
        )


def test_no_page_references_a_skill_that_does_not_exist():
    """Renames are silent. This is the net under them."""
    existing = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}
    pages = [README] + sorted(DOCS_DIR.rglob("*.md")) + sorted(SKILLS_DIR.rglob("SKILL.md"))
    broken = []
    for page in pages:
        for name in re.findall(r"skills/([a-z][a-z0-9-]+)/SKILL\.md", page.read_text(encoding="utf-8")):
            if name not in existing:
                broken.append(f"{page.relative_to(REPO_ROOT)} -> {name}")
    assert not broken, "references to skills that do not exist:\n  " + "\n  ".join(broken)


def test_the_plugin_invocation_is_documented_where_it_is_needed():
    """Installed as a plugin the CLI is not on the PATH, and that has to be said."""
    for page in (README, SKILLS_DIR / "route-work-to-the-right-model" / "SKILL.md"):
        text = page.read_text(encoding="utf-8")
        assert "CLAUDE_PLUGIN_ROOT" in text and "python3 -m validated_memory" in text, (
            f"{page.relative_to(REPO_ROOT)} shows `validated-memory ...` but never "
            "says how to run it from an installed plugin, where it is not on the PATH"
        )
