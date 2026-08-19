"""The router has to keep listing every skill, forever.

`pick-the-right-skill` is the front door. A skill that is not listed there is a
skill nobody will find, which is the same as not shipping it.

This is the drift guard: add a skill and forget to route it, and this fails.
It reads the Markdown surface as data, like the rest of the structural tests --
nothing here imports the package's internals.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
ROUTER = "pick-the-right-skill"


def _skill_names():
    return {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}


def _routed_names():
    text = (SKILLS_DIR / ROUTER / "SKILL.md").read_text(encoding="utf-8")
    return set(re.findall(r"\[`([a-z][a-z0-9-]+)`\]\(\.\./", text))


def test_every_skill_is_reachable_from_the_router():
    missing = _skill_names() - _routed_names() - {ROUTER}
    assert not missing, (
        "these skills are not listed in "
        f"skills/{ROUTER}/SKILL.md, so nobody will find them: {sorted(missing)}"
    )


def test_the_router_does_not_point_at_skills_that_do_not_exist():
    ghosts = _routed_names() - _skill_names()
    assert not ghosts, f"the router links to skills that do not exist: {sorted(ghosts)}"


def test_every_router_link_resolves_to_a_real_file():
    text = (SKILLS_DIR / ROUTER / "SKILL.md").read_text(encoding="utf-8")
    broken = [
        target
        for target in re.findall(r"\]\((\.\./[^)]+)\)", text)
        if not (SKILLS_DIR / ROUTER / target).resolve().exists()
    ]
    assert not broken, f"broken links in the router: {broken}"
