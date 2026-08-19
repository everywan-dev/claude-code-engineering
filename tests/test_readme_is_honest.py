"""The README has to keep telling the truth about the repository.

A README is the one file everybody reads and nobody tests, so it is the first
place a project starts lying: counts that drifted, links to files that were
renamed, credit that quietly disappeared.

These are the claims worth pinning:

- every relative link resolves to a file that exists;
- the counts it advertises match what is actually on disk;
- every skill adapted from third-party material still carries its attribution,
  and the licence it arrived under is still shipped.

The last one is not cosmetic. Redistributing MIT material without its notice is
a licence violation, and it is exactly the kind of thing that rots silently
through a rename.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"
UPSTREAM = "mattpocock/skills"
UPSTREAM_LICENCE = REPO_ROOT / "LICENSES" / "mattpocock-skills-MIT.txt"


def _readme_text():
    return README.read_text(encoding="utf-8")


def _adapted_skills():
    return [
        d.name
        for d in SKILLS_DIR.iterdir()
        if d.is_dir() and UPSTREAM in (d / "SKILL.md").read_text(encoding="utf-8")
    ]


def test_every_relative_link_in_the_readme_resolves():
    broken = []
    for target in re.findall(r"\]\(([^)#][^)]*)\)", _readme_text()):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (REPO_ROOT / target.split("#")[0]).exists():
            broken.append(target)
    assert not broken, f"README links to files that do not exist: {broken}"


def test_the_skill_count_matches_the_directory():
    """Both counts the README gives have to hold: the total, and the split.

    It legitimately states two different numbers -- how many skills there are,
    and how many of those are original -- so each is checked against what the
    directory actually contains rather than lumped together.
    """
    actual = len([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    text = _readme_text()

    total = {int(n) for n in re.findall(r"^# .*|(\d+) skills, \d+ review agents", text, re.M) if n}
    total |= {int(n) for n in re.findall(r"## The (\d+) skills", text)}
    assert total, "the README no longer states how many skills there are"
    assert total == {actual}, (
        f"README advertises {sorted(total)} skills in total, the directory has {actual}"
    )

    own = actual - len(_adapted_skills())
    advertised = {int(n) for n in re.findall(r"remaining (\d+) skills", text)}
    assert advertised == {own}, (
        f"README claims {sorted(advertised)} original skills; "
        f"{actual} total minus {len(_adapted_skills())} adapted is {own}"
    )


def test_the_agent_count_matches_the_directory():
    actual = len(list(AGENTS_DIR.glob("*.md")))
    advertised = {int(n) for n in re.findall(r"(\d+) (?:review )?agents", _readme_text())}
    assert advertised == {actual}, (
        f"README advertises {sorted(advertised)} agents, the directory has {actual}"
    )


def test_adapted_skills_are_credited_in_the_readme():
    """Credit that only lives in the individual files is credit nobody reads."""
    text = _readme_text()
    assert UPSTREAM in text, "the README no longer credits the upstream collection"
    assert "MIT" in text
    assert "Matt Pocock" in text
    advertised = {int(n) for n in re.findall(r"(\d+) of the \d+ skills", text)}
    assert advertised == {len(_adapted_skills())}, (
        f"README says {sorted(advertised)} adapted skills, "
        f"{len(_adapted_skills())} carry the attribution"
    )


def test_the_upstream_licence_is_still_shipped():
    assert UPSTREAM_LICENCE.exists(), "the MIT licence text is no longer shipped"
    content = UPSTREAM_LICENCE.read_text(encoding="utf-8")
    assert "MIT License" in content
    assert "Matt Pocock" in content


def test_every_adapted_skill_states_its_origin():
    uncredited = [
        d.name
        for d in SKILLS_DIR.iterdir()
        if d.is_dir()
        and UPSTREAM in (d / "SKILL.md").read_text(encoding="utf-8")
        and "Copyright (c) 2026 Matt Pocock" not in (d / "SKILL.md").read_text(encoding="utf-8")
    ]
    assert not uncredited, f"adapted skills missing the copyright line: {uncredited}"
