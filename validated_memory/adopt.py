"""Absorbing a pre-existing harness agent-memory directory.

`init --harness-memory PATH` wants PATH to be a symlink into this project's
`memory/`. When PATH is already a real directory holding the harness's own
agent memory, refusing to touch it leaves two live memories that cannot see
each other. This module handles that one case: it recognizes the directory as
agent memory, copies what it holds into the project's `memory/`, parks the
original alongside as a `.bak`, and hands the freed path back so the caller
can create the symlink.

Recognition is deliberately strict, because the alternative to a false
positive is a WARNING and the alternative to a false negative is moving a
directory that belongs to something else.
"""

import shutil
from pathlib import Path, PurePosixPath

from .findings import WARNING, Finding
from .frontmatter import FrontmatterError, parse
from .lint import MEMORY_TYPES
from .memory import INDEX_FILENAME, SUFFIX as MEMORY_SUFFIX, index_entries

PARKED_SUFFIX = ".bak"

# The line `init` writes into a fresh index, dropped as soon as the index
# gains its first real entry so it does not sit there contradicting them.
PLACEHOLDER = "No entries yet."


def take_over(path, memory_dir, stdout):
    """Free `path` by absorbing the agent memory it holds into `memory_dir`.

    Returns `(freed, findings)`: `freed` says whether `path` no longer exists
    and the caller may create its symlink. Every failure is fail-open -- a
    WARNING and `freed` False -- so a startup hook built on this can never
    break a session.
    """
    if path.is_dir() and not any(path.iterdir()):
        # An empty directory holds nothing to absorb and nothing to park.
        # `rmdir` is the one removal here, and the operating system refuses it
        # on anything that is not empty: it cannot lose data.
        path.rmdir()
        print(f"init: removed empty directory {path.as_posix()}", file=stdout)
        return True, []

    reason = _unrecognized(path)
    if reason is not None:
        return False, [Finding(WARNING, path.as_posix(), "symlink", reason)]

    adopted, findings = _absorb(path, memory_dir, stdout)
    _reconcile_index(path, memory_dir, adopted)
    parked = _park(path)
    print(f"init: parked {path.as_posix()} -> {parked.as_posix()}", file=stdout)
    return True, findings


def _unrecognized(path):
    """Return why `path` is not recognizably agent memory, or None if it is."""
    if not path.is_dir():
        return (
            "already exists and is not a symlink; it is not an agent-memory "
            "directory either, so it was left untouched"
        )
    memories = 0
    for entry in sorted(path.rglob("*")):
        if entry.is_dir():
            continue
        if entry.suffix != MEMORY_SUFFIX:
            # Rejected on the suffix alone, before the contents are read:
            # absorption only ever copies '.md' files, so anything else would
            # be parked into the backup and never seen again.
            return (
                f"already exists and holds '{entry.name}', which is not a "
                f"'{MEMORY_SUFFIX}' file; it was left untouched"
            )
        if entry.name == INDEX_FILENAME and entry.parent == path:
            # The harness's own index is recognition enough on its own: a
            # directory holding it and nothing else is still agent memory.
            memories += 1
            continue
        if not _is_memory(entry):
            return (
                f"already exists and holds '{entry.name}', which does not carry "
                "the agent-memory frontmatter; it was left untouched"
            )
        memories += 1
    if not memories:
        return "already exists and holds no agent-memory files; it was left untouched"
    return None


def _is_memory(path):
    """Say whether `path` carries the frontmatter `lint` requires of a memory."""
    try:
        data = parse(path.read_text(encoding="utf-8"))
    except (FrontmatterError, OSError, UnicodeDecodeError):
        return False
    metadata = data.get("metadata")
    return (
        isinstance(data.get("name"), str)
        and isinstance(data.get("description"), str)
        and isinstance(metadata, dict)
        and metadata.get("type") in MEMORY_TYPES
    )


def _absorb(source, memory_dir, stdout):
    """Copy every memory file under `source` into `memory_dir`, never overwriting.

    Returns `(adopted, findings)`, where `adopted` lists the relative paths
    actually copied -- what `_reconcile_index` then has to account for.
    """
    adopted = []
    findings = []
    for entry in sorted(source.rglob(f"*{MEMORY_SUFFIX}")):
        if not entry.is_file():
            continue
        relative = entry.relative_to(source)
        if relative.as_posix() == INDEX_FILENAME:
            continue
        destination = memory_dir / relative
        if destination.exists():
            if destination.read_bytes() != entry.read_bytes():
                findings.append(
                    Finding(
                        WARNING,
                        (memory_dir / relative).as_posix(),
                        "adopt",
                        f"this project already has a different "
                        f"'{relative.as_posix()}'; the project's copy was kept "
                        "and the harness's is preserved in the parked backup",
                    )
                )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry, destination)
        adopted.append(relative.as_posix())
    if adopted:
        print(
            f"init: adopted {len(adopted)} memory file(s) from {source.as_posix()}",
            file=stdout,
        )
    return adopted, findings


def _reconcile_index(source, memory_dir, adopted):
    """Give every adopted file an entry in the project's index.

    The adopted file's own entry is taken from the harness's index when it has
    one -- that line is what a human wrote about the fact -- and synthesized
    from the file's frontmatter otherwise. Lines already in the project's index
    are never rewritten or removed: reconciling only ever appends.
    """
    if not adopted:
        return
    index_path = memory_dir / INDEX_FILENAME
    text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    known = {href for href, _line in _index_entries(text)}
    native = dict(_index_entries(_read(source / INDEX_FILENAME)))

    added = []
    for relative in adopted:
        if relative in known:
            continue
        known.add(relative)
        entry = native.get(relative)
        if entry is None:
            entry = _synthesize(memory_dir / relative, relative)
        added.append(entry)
    if not added:
        return

    lines = text.splitlines()
    if not list(_index_entries(text)):
        lines = [line for line in lines if line.strip() != PLACEHOLDER]
    while lines and not lines[-1].strip():
        lines.pop()
    index_path.write_text("\n".join(lines + added) + "\n", encoding="utf-8")


def _index_entries(text):
    """Yield `(relpath, line)` for every index entry that names a file.

    The path is normalized the way the index/file cross-check normalizes it,
    so `./coffee.md` and `coffee.md` are one entry for one file rather than
    two. A bullet whose link target is blank names no file and is not an
    entry here -- `lint` reports it as malformed on its own.
    """
    for entry in index_entries(text):
        if not entry.href:
            continue
        yield PurePosixPath(entry.href).as_posix(), entry.line


def _synthesize(path, relative):
    """Build an index entry for a memory file the harness's index did not list."""
    try:
        data = parse(path.read_text(encoding="utf-8"))
    except (FrontmatterError, OSError, UnicodeDecodeError):  # pragma: no cover
        return f"- [{relative}]({relative})"
    return f"- [{data['name']}]({relative}) — {data['description']}"


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _park(path):
    """Rename `path` aside to the first free `.bak` slot and return the new path."""
    parked = Path(f"{path}{PARKED_SUFFIX}")
    attempt = 0
    while parked.exists():
        attempt += 1
        parked = Path(f"{path}{PARKED_SUFFIX}.{attempt}")
    path.rename(parked)
    return parked
