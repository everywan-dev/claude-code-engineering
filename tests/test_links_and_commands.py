"""Every link in a skill, agent or command has to resolve, and commands have to
be well formed.

The existing reference check only recognised links written as
`skills/<name>/SKILL.md`. Skills link to each other as `../<name>/SKILL.md`,
which that pattern never matched -- so the cross-references between skills, which
are most of the links in the collection, were unchecked. None were broken when
this was written; nothing was stopping the next rename from breaking them, which
is the same thing as being untested.

`commands/` had no check at all. A slash command with malformed frontmatter is
not loaded, and a plugin that silently ships one fewer command than it documents
is the failure this project exists to prevent.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"

LINK = re.compile(r"\]\((?!https?://|mailto:)([^)#]+)(?:#[^)]*)?\)")
# Fenced blocks are examples of a format, not links to follow. Skills legitimately
# show `- [Title](short-kebab-slug.md)` to teach the shape of an index entry, and
# `[<closed ticket title>](link)` as a placeholder. Treating those as broken links
# is how a link checker earns a reputation for crying wolf and gets switched off.
FENCE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
# Same reasoning for inline code: `- [Title](file.md)` in a sentence is showing
# the shape of a line, not linking to a file called file.md.
INLINE_CODE = re.compile(r"`[^`\n]*`")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _markdown_files():
    yield from SKILLS_DIR.rglob("*.md")
    yield from AGENTS_DIR.glob("*.md")
    if COMMANDS_DIR.is_dir():
        yield from COMMANDS_DIR.glob("*.md")


def test_every_relative_link_resolves():
    broken = []
    for page in _markdown_files():
        prose = INLINE_CODE.sub("", FENCE.sub("", page.read_text(encoding="utf-8")))
        for target in LINK.findall(prose):
            if not (page.parent / target.strip()).resolve().exists():
                broken.append(f"{page.relative_to(REPO_ROOT)} -> {target.strip()}")
    assert not broken, (
        "links pointing at files that do not exist:\n  " + "\n  ".join(broken)
    )


def test_the_check_would_notice_a_broken_link():
    """Proof the pattern above actually matches how skills link to each other."""
    sample = "See [`some-skill`](../some-skill/SKILL.md) for the vocabulary."
    assert LINK.findall(sample) == ["../some-skill/SKILL.md"], (
        "the link pattern no longer matches the form skills use to cross-reference, "
        "so it would pass while every cross-link rotted"
    )


def test_the_check_ignores_examples_inside_code_fences():
    """The other half: it must not report a format example as a broken link."""
    sample = (
        "Real: [a](../a/SKILL.md)\n\n"
        "```markdown\n- [Title](short-kebab-slug.md)\n```\n\n"
        "Inline: bullets shaped `- [Title](file.md)` are index entries.\n"
    )
    cleaned = INLINE_CODE.sub("", FENCE.sub("", sample))
    assert LINK.findall(cleaned) == ["../a/SKILL.md"]


def test_every_command_has_usable_frontmatter():
    if not COMMANDS_DIR.is_dir():
        return
    problems = []
    for command in sorted(COMMANDS_DIR.glob("*.md")):
        block = FRONTMATTER.match(command.read_text(encoding="utf-8"))
        if not block:
            problems.append(f"{command.name}: no frontmatter, so it will not load")
            continue
        if not re.search(r"^description:\s*\S", block.group(1), re.M):
            problems.append(f"{command.name}: no description, so it is invisible in help")
    assert not problems, "\n  ".join(problems)


def test_commands_only_allow_tools_they_document():
    """`allowed-tools` is a permission grant. It should not be wider than the
    command's own instructions, or the grant is doing something unreviewed."""
    if not COMMANDS_DIR.is_dir():
        return
    for command in sorted(COMMANDS_DIR.glob("*.md")):
        text = command.read_text(encoding="utf-8")
        block = FRONTMATTER.match(text)
        if not block:
            continue
        allowed = re.search(r"^allowed-tools:\s*(.+)$", block.group(1), re.M)
        if not allowed:
            continue
        body = text[block.end():]
        for grant in re.findall(r"Bash\(([^)]+)\)", allowed.group(1)):
            binary = grant.split("(")[0].split(":")[0].strip().split()[0]
            assert binary in body, (
                f"{command.name} grants Bash access to {binary!r} but never "
                "mentions it in its instructions"
            )
