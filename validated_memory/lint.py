"""The `lint` subcommand: the agent-memory layer of the adopter.

The agent-memory layer is one Markdown file per fact, plus a one-line-per-
entry index (`MEMORY.md`) at the root of the memory directory. `lint`
enforces five things: the index and the files agree in both directions, each
file's frontmatter is complete, `name` matches the filename that is the
memory's canonical identity, a wikilink between memories names a real memory
(or is flagged as pending), and the supersession convention -- a
`description` rewritten to start with `superseded by [[name]]` -- is either
well formed or reported.

The rules live here; how the layer is read and how a reference resolves live
in `memory`, so that a second reader of the same layer cannot resolve
references differently from `lint`.
"""

from pathlib import Path, PurePosixPath

from . import memory as memory_module
from .findings import ERROR, WARNING, Finding, report
from .frontmatter import FrontmatterError, parse

DEFAULT_MEMORY_DIR = memory_module.DEFAULT_DIR
INDEX_FILENAME = memory_module.INDEX_FILENAME

MEMORY_TYPES = ("user", "project", "feedback", "reference")


def run(path, stdout, stderr):
    """Lint every memory file under `path` and report findings. Returns an exit code."""
    target = Path(path) if path else Path(DEFAULT_MEMORY_DIR)
    documents, findings = _collect(target, explicit=bool(path))
    findings.extend(_lint_memories(documents))
    return report("lint", len(documents), "memory file(s)", findings, stdout, stderr)


def _collect(target, explicit):
    """Resolve the memory directory and its index, and read every memory file."""
    location = target.as_posix()
    if not target.exists():
        if explicit:
            message = "no such file or directory"
        else:
            message = (
                f"no agent-memory directory found at '{location}'; pass a PATH "
                "or run 'validated-memory init'"
            )
        return [], [Finding(ERROR, location, "target", message)]

    index_path = target / INDEX_FILENAME
    if not index_path.exists():
        return [], [
            Finding(
                ERROR,
                index_path.as_posix(),
                "index",
                f"index '{INDEX_FILENAME}' not found; run 'validated-memory init'",
            )
        ]

    documents = memory_module.documents(target)
    entries = memory_module.index_entries(index_path.read_text(encoding="utf-8"))
    findings = _check_sync(index_path.as_posix(), entries, documents)

    return documents, findings


def _check_sync(index_location, entries, documents):
    """Check the index and the files agree in both directions."""
    findings = []
    by_relpath = {document.relpath: document for document in documents}
    referenced = set()
    for entry in entries:
        relpath = PurePosixPath(entry.href).as_posix()
        referenced.add(relpath)
        if relpath not in by_relpath:
            findings.append(
                Finding(
                    ERROR,
                    index_location,
                    "entry",
                    f"'{entry.href}' has no matching memory file",
                )
            )
    for relpath, document in by_relpath.items():
        if relpath not in referenced:
            findings.append(
                Finding(
                    ERROR,
                    document.location,
                    "index",
                    f"memory file has no entry in '{INDEX_FILENAME}'",
                )
            )
    return findings


def _lint_memories(documents):
    """Lint each memory file's frontmatter, then cross-file name resolution.

    Names are collected in a first pass, once every document has parsed, so
    duplicate detection and reference resolution do not depend on file order --
    the same two-pass shape `validate` uses for id declaration and supersedes
    resolution.
    """
    findings = _check_filename_collisions(documents)
    parsed = []
    for document in documents:
        try:
            data = parse(document.text)
        except FrontmatterError as error:
            findings.append(
                Finding(
                    ERROR,
                    document.location,
                    "frontmatter",
                    error.message,
                    line=error.lineno,
                )
            )
            continue
        parsed.append((document.location, data, memory_module.body(document.text)))

    for location, data, _body in parsed:
        findings.extend(_check_memory(location, data))

    declared_names = {}
    for location, data, _body in parsed:
        name = data.get("name")
        if not memory_module.is_declared(name):
            continue
        if name in declared_names:
            findings.append(
                Finding(
                    ERROR,
                    location,
                    "name",
                    f"duplicate name '{name}', already declared by "
                    f"{declared_names[name]}",
                )
            )
        else:
            declared_names[name] = location

    resolution = memory_module.resolution(
        documents, {location: data.get("name") for location, data, _body in parsed}
    )
    for location, data, body in parsed:
        own_name = data.get("name")
        if not memory_module.is_declared(own_name):
            own_name = None
        description = data.get("description")
        findings.extend(
            _check_description_references(location, own_name, description, resolution)
        )
        findings.extend(_check_references(location, "body", body, resolution))

    return findings


def _check_filename_collisions(documents):
    """Report two memories claiming the same canonical identity.

    Two files in one directory cannot share a name, so this only ever fires
    across subdirectories. It is a fact about the files, so it is checked
    before any frontmatter is read and holds even when neither file parses.

    A WARNING for the same reason the divergence rule is one -- it becomes an
    ERROR in 2.0.0 alongside it. Reporting it matters now because without it
    `lint` tells both files to repair `name` towards the same value, and
    following that advice lands on the duplicate-name ERROR unannounced.
    """
    findings = []
    first_seen = {}
    for document in documents:
        filename = memory_module.filename(document.location)
        if not filename:
            continue  # no identity at all; its own rule reports that
        if filename not in first_seen:
            first_seen[filename] = document.location
            continue
        findings.append(
            Finding(
                WARNING,
                document.location,
                "filename",
                f"the filename '{filename}' is also carried by "
                f"{first_seen[filename]}; the filename is the canonical "
                "identity, so these are two memories with the same identity "
                "-- rename one",
            )
        )
    return findings


def _check_description_references(location, own_name, description, resolution):
    """Check the supersession marker (if any), then any remaining wikilink.

    A wikilink that opens a well-formed `superseded by [[name]]` marker is
    checked by the supersession rule below, not by the generic wikilink scan,
    so it is not reported twice.
    """
    if not isinstance(description, str):
        return []
    findings = []
    scan_text = description
    marker = memory_module.supersession(description)
    if marker is not None:
        scan_text = marker.remainder
        if marker.target is None:
            findings.append(
                Finding(
                    ERROR,
                    location,
                    "description",
                    "malformed supersession marker: 'superseded by ' must be "
                    "followed by a [[wikilink]]",
                )
            )
        else:
            findings.extend(
                _check_supersession_target(
                    location, own_name, marker.target, resolution
                )
            )
    findings.extend(_check_references(location, "description", scan_text, resolution))
    return findings


def _check_supersession_target(location, own_name, target, resolution):
    """Check the successor a memory is retired onto.

    Order matters. A target that resolves to another memory is a valid
    supersession even when it happens to equal this file's own filename, so
    resolution is settled first. Only then does the filename count as naming
    this memory itself -- it is the canonical identity, so retiring a memory
    onto it is retiring it onto itself, whatever `name` currently says.
    """
    if target in resolution.by_name and target != own_name:
        return []
    if target == own_name or target == memory_module.filename(location):
        return [
            Finding(
                ERROR,
                location,
                "description",
                f"supersession points at itself: '{target}'",
            )
        ]
    hint = memory_module.filename_hint(target, resolution)
    if hint is None:
        message = f"supersession points at '{target}', which does not exist"
    else:
        # Unlike a wikilink, a successor cannot be left pending: this gates.
        # Saying the memory does not exist would send the repair to the wrong
        # file, so the message names what actually fails to resolve.
        message = (
            f"supersession points at '{target}', which does not resolve by "
            f"name; {hint}"
        )
    return [Finding(ERROR, location, "description", message)]


def _check_references(location, field, text, resolution):
    """Report every wikilink in `text` that does not resolve to a memory."""
    findings = []
    for target in memory_module.wikilinks(text):
        if target in resolution.by_name:
            continue
        hint = memory_module.filename_hint(target, resolution)
        if hint is None:
            message = f"wikilink to '{target}' has no matching memory (not written yet)"
        else:
            # The file is right there; what does not resolve is its `name`.
            # Saying 'not written yet' here would point at the wrong repair.
            message = f"wikilink to '{target}' has no matching memory; {hint}"
        findings.append(Finding(WARNING, location, field, message))
    return findings


def _check_memory(location, data):
    findings = []
    name_findings = _check_name(location, data)
    findings.extend(name_findings)
    if not name_findings:
        findings.extend(_check_filename_identity(location, data))
    findings.extend(_check_description(location, data))
    findings.extend(_check_type(location, data))
    return findings


def _check_name(location, data):
    if "name" not in data:
        return [Finding(ERROR, location, "name", "required field is missing")]
    name = data["name"]
    if not memory_module.is_declared(name):
        return [
            Finding(
                ERROR, location, "name", f"{_describe(name)} is not a non-empty string"
            )
        ]
    return []


def _check_filename_identity(location, data):
    """Check `name` against the filename, which is the canonical identity.

    When the two disagree the filename wins and `name` is repaired to match it,
    never the other way round: a third of a real corpus carries titles in
    `name` -- spaces, dots, capitals -- for which no rename exists (ADR 0001).

    This is a WARNING rather than an ERROR purely as a migration concession for
    memory sets written before the rule. It becomes an ERROR in 2.0.0.
    """
    name = data["name"]
    filename = memory_module.filename(location)
    if not filename:
        return [
            Finding(
                WARNING,
                location,
                "name",
                f"the filename '{PurePosixPath(location).name}' carries no "
                "identity once the '.md' suffix is removed; rename the file",
            )
        ]
    if name == filename:
        return []
    return [
        Finding(
            WARNING,
            location,
            "name",
            f"'{name}' does not match the filename '{filename}'; the filename "
            "is the canonical identity -- repair 'name' to match it",
        )
    ]


def _check_description(location, data):
    if "description" not in data:
        return [Finding(ERROR, location, "description", "required field is missing")]
    description = data["description"]
    if not memory_module.is_declared(description):
        return [
            Finding(
                ERROR,
                location,
                "description",
                f"{_describe(description)} is not a non-empty string",
            )
        ]
    return []


def _check_type(location, data):
    metadata = data.get("metadata")
    if not isinstance(metadata, dict) or "type" not in metadata:
        return [Finding(ERROR, location, "metadata.type", "required field is missing")]
    kind = metadata["type"]
    if kind not in MEMORY_TYPES:
        return [
            Finding(
                ERROR,
                location,
                "metadata.type",
                f"{_describe(kind)} is not one of " + ", ".join(MEMORY_TYPES),
            )
        ]
    return []


def _describe(value):
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, list):
        return "a list"
    if isinstance(value, dict):
        return "a mapping"
    return "a missing value"
