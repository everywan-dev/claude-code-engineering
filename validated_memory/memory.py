"""How the agent-memory layer is read, and how a reference resolves.

The layer is one Markdown file per fact under a memory directory, plus a
one-line-per-entry index (`MEMORY.md`) at its root. This module knows how to
read that -- collect the files, parse the index, find the body, extract
wikilinks, parse the supersession marker -- and how a reference to another
memory resolves. It holds no rules: nothing here decides whether what it read
is well formed. `lint` is the rules on top of it.

The split exists so a second reader cannot resolve references differently
from `lint`. Resolution has three subtleties that are easy to get wrong
apart: it goes by `name` while the canonical identity is the filename
(ADR 0001), a filename only explains an unresolved reference when it is
unambiguous, and ambiguity is counted over every file collected rather than
over the ones whose frontmatter happened to parse.
"""

import re
from collections import namedtuple
from pathlib import PurePosixPath

DEFAULT_DIR = "memory"
SUFFIX = ".md"
INDEX_FILENAME = "MEMORY.md"

INDEX_ENTRY_PATTERN = re.compile(r"^-\s+\[([^\]]*)\]\(([^)]+)\)(.*)$")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
SUPERSEDED_PREFIX = "superseded by "
SUPERSEDED_WIKILINK_PATTERN = re.compile(r"^\[\[([^\]]+)\]\]")

# One memory file as it was read. `relpath` is the path the index refers to
# it by; `location` is the path a finding names.
Document = namedtuple("Document", "location relpath text")

# One `- [Title](file.md) — note` line of the index. `note` is whatever
# follows the link, free text this layer does not interpret; `line` is the
# entry as written, stripped of surrounding whitespace, which is what a
# reader that has to preserve it rather than re-render it needs.
IndexEntry = namedtuple("IndexEntry", "title href note line")

# How a reference to another memory resolves. `by_name` is what resolution
# actually goes by; `by_filename` only ever explains a reference that did not
# resolve, since the canonical identity is the filename and that is what a
# writer reaches for.
Resolution = namedtuple("Resolution", "by_name by_filename")

# A parsed `superseded by [[name]]` marker. `target` is None when the marker
# opened but no wikilink followed it, and then `remainder` is empty: nothing
# after an unparseable marker can be read as an ordinary reference. Otherwise
# `remainder` is the description text after the marker, which still has to be
# scanned for ordinary wikilinks.
Supersession = namedtuple("Supersession", "target remainder")


def filename(location):
    """Return the memory's canonical identity: its filename minus `.md`.

    Not `PurePosixPath.stem`, which reads a leading dot as the start of a name
    rather than as a suffix boundary: a file called `.md` has `stem == '.md'`,
    which would hand it the identity `.md` instead of none at all.
    """
    name = PurePosixPath(location).name
    if name.endswith(SUFFIX):
        return name[: -len(SUFFIX)]
    return name  # pragma: no cover - only `*.md` files are ever collected


def documents(target):
    """Every memory file under `target`, sorted, as `Document`s.

    The index itself is excluded: it is not a memory. Whether `target` or the
    index exist at all is the caller's business -- this reads what is there.
    """
    index_path = target / INDEX_FILENAME
    return [
        Document(
            location=candidate.as_posix(),
            relpath=candidate.relative_to(target).as_posix(),
            text=candidate.read_text(encoding="utf-8"),
        )
        for candidate in sorted(target.rglob(f"*{SUFFIX}"))
        if candidate.is_file() and candidate != index_path
    ]


def index_entries(text):
    """Return every bullet-with-link entry of the index, in order.

    Only lines shaped `- [Title](file.md)` count as entries; headers and prose
    are ignored. The href is stripped here rather than by each caller: it is
    used as a key, and two callers stripping it differently is how they come
    to disagree about which entry names which file.
    """
    entries = []
    for line in text.splitlines():
        match = INDEX_ENTRY_PATTERN.match(line.strip())
        if match:
            title, href, note = match.groups()
            entries.append(
                IndexEntry(title, href.strip(), note.strip(), line.strip())
            )
    return entries


def body(text):
    """Return the document text after the closing frontmatter fence.

    Called only once the frontmatter has already been parsed, so the fences
    are known to be well formed.
    """
    lines = text.split("\n")
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return "\n".join(lines[index + 1 :])
    return ""  # pragma: no cover - unreachable once the frontmatter parsed


def wikilinks(text):
    """Return the `[[name]]` targets in `text`, first occurrence first, once each."""
    if not isinstance(text, str):
        return []
    targets = []
    seen = set()
    for match in WIKILINK_PATTERN.finditer(text):
        target = match.group(1)
        if target in seen:
            continue
        seen.add(target)
        targets.append(target)
    return targets


def supersession(description):
    """Parse the supersession marker, when the description opens with one.

    Returns None when there is no marker at all -- an ordinary description --
    and a `Supersession` otherwise, whose `target` is None when the prefix was
    not followed by a parseable wikilink.
    """
    if not isinstance(description, str) or not description.startswith(
        SUPERSEDED_PREFIX
    ):
        return None
    remainder = description[len(SUPERSEDED_PREFIX) :]
    match = SUPERSEDED_WIKILINK_PATTERN.match(remainder)
    if not match:
        return Supersession(None, "")
    return Supersession(match.group(1), remainder[match.end() :])


def resolution(documents_read, declared):
    """Build the resolution tables for a memory set.

    `declared` maps a location to the `name` its frontmatter declares, for the
    documents whose frontmatter parsed. `documents_read` is every document
    collected, parsed or not -- ambiguity is counted over all of them, so a
    filename shared by two memories stays ambiguous even when only one of the
    two has readable frontmatter: the readable one is not thereby known to be
    the memory that was meant.
    """
    by_filename = {}
    for document in documents_read:
        by_filename.setdefault(filename(document.location), []).append(
            declared.get(document.location)
        )
    return Resolution(
        by_name=set(name for name in declared.values() if is_declared(name)),
        by_filename={
            name: names[0]
            for name, names in by_filename.items()
            if len(names) == 1 and is_declared(names[0])
        },
    )


def filename_hint(target, resolved):
    """Name the file a reference was reaching for, when it is certain which.

    None when no single file carries that filename -- there is nothing certain
    to say, and guessing would send the repair to the wrong file.
    """
    declared = resolved.by_filename.get(target)
    if declared is None:
        return None
    return f"'{target}{SUFFIX}' declares name '{declared}'"


def is_declared(value):
    """Say whether a frontmatter value counts as a declared name.

    Shared with `lint` rather than restated there: resolution and the rules
    have to agree about which names exist, and two definitions of that are
    how a name the rules accept gets left out of resolution.
    """
    return isinstance(value, str) and bool(value.strip())
