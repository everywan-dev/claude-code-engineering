"""The append-only verdict log: `probe` writes it, `derive` reads it.

Each `probe` run appends one JSON line per anchor probed to `verdicts.jsonl`
in the working directory -- never under `knowledge/`, for the same reason
`knowledge-index.md` lives outside it (see `derive`). History is never
rewritten: the log only grows. The service view a reader wants is the latest
record per anchor -- an anchor being what its `(system, kind, payload)` names,
see `anchor_key` -- computed here rather than stored, since storing it would
mean rewriting the log on every probe.
"""

import json
from pathlib import Path

LOG_FILENAME = "verdicts.jsonl"


class VerdictLogError(Exception):
    """Raised when the log cannot be read as verdict records.

    A reader must never guess about a log it cannot parse: a truncated write
    or a hand edit is reported with its line, fail-loud, instead of serving
    verdicts computed from a record that was silently skipped.

    `lineno` is None when the fault is the file's rather than a line's -- it
    could not be opened or decoded at all.
    """

    def __init__(self, lineno, message):
        super().__init__(message)
        self.lineno = lineno
        self.message = message

CURRENT = "current"
DRIFTED = "drifted"
UNKNOWN = "unknown"
VERDICTS = (CURRENT, DRIFTED, UNKNOWN)

# Worst-first severity for aggregation: drifted outranks unknown outranks
# current.
_SEVERITY = {DRIFTED: 2, UNKNOWN: 1, CURRENT: 0}


def worst(verdicts):
    """The most severe verdict among `verdicts` (drifted > unknown > current)."""
    return max(verdicts, key=lambda verdict: _SEVERITY[verdict])


def append(records, root=Path()):
    """Append `records` to the log, one JSON line each. Never rewrites."""
    path = Path(root) / LOG_FILENAME
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


KEY_FIELDS = ("unit", "system", "kind")

# The key a record written before payloads were recorded lands under. Such a
# record is never read by an anchor: the log cannot say which anchor it was
# about, nor what that anchor pointed at when it was written. Attributing it
# would risk reporting `current` for something that has since drifted, which
# is the failure the payload was added to prevent. It is kept, because the log
# is history and history is not rewritten, and it is ignored.
NO_PAYLOAD = None


def anchor_key(unit_id, system, kind, payload):
    """The key one anchor's verdicts are recorded and read under.

    An anchor is identified by what it points at -- its system, its kind and
    its payload. `captured_at` dates a capture, it does not identify one.

    Keyed on `(system, kind)` alone, two legitimately distinct anchors of one
    unit -- two refs of the same repository, both `git_ref` on the same system
    -- collapsed into one entry, so the later verdict overwrote the earlier and
    a `drifted` could disappear behind a `current`. The index then reported a
    unit as current while one of its anchors had drifted, and which one won
    depended on the order the anchors happened to be written in.
    """
    return (unit_id, system, kind, _canonical(payload))


def _canonical(payload):
    """A hashable, stable rendering of a payload, or `NO_PAYLOAD` if absent.

    `sort_keys` makes two equal mappings render identically whatever order
    they were written in; a list keeps its order, because there the order is
    part of what the payload says.
    """
    if payload is None:
        return NO_PAYLOAD
    return json.dumps(payload, sort_keys=True)


def records(root=Path()):
    """Yield `(lineno, record)` for every record in the log, fail-loud.

    The single place the log is turned into records, so every reader of it
    accepts and rejects exactly the same files. Reading the file is part of
    that: a log that cannot be opened or decoded is a log that cannot be read,
    and letting an `OSError` or a `UnicodeDecodeError` past here would surface
    as a traceback rather than as the finding this promises.
    """
    path = Path(root) / LOG_FILENAME
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise VerdictLogError(None, f"cannot be read: {error}") from error
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise VerdictLogError(
                lineno, f"not a JSON record: {error.msg}"
            ) from error
        if not isinstance(record, dict):
            raise VerdictLogError(lineno, "record is not a JSON object")
        yield lineno, record


def _keyed(lineno, record):
    """Return `(key, verdict)` for one record, or raise `VerdictLogError`.

    The key fields are checked to be strings before they are used as one: a
    hand-edited log can carry a list there, and an unhashable value reaching
    the dictionary raises `TypeError` instead of naming the line at fault.
    """
    try:
        fields = tuple(record[field] for field in KEY_FIELDS)
        verdict = record["verdict"]
    except KeyError as error:
        raise VerdictLogError(lineno, f"record is missing the {error} field") from error
    for field, value in zip(KEY_FIELDS, fields):
        if not isinstance(value, str):
            raise VerdictLogError(lineno, f"the '{field}' field is not a string")
    # Presence, not value: only an absent field means "written before
    # payloads were recorded". An explicit `null` is a malformed record, and
    # letting it pass would file it under the same key as an absent one.
    payload = record.get("payload")
    if "payload" in record and not isinstance(payload, dict):
        raise VerdictLogError(lineno, "the 'payload' field is not a mapping")
    if verdict not in VERDICTS:
        raise VerdictLogError(
            lineno,
            f"'{verdict}' is not one of " + ", ".join(VERDICTS),
        )
    return anchor_key(*fields, payload), verdict


def service_view(root=Path()):
    """The latest verdict per `(unit, system, kind)`, or `{}` if never probed.

    Raises `VerdictLogError` on a log that cannot be read as records.
    """
    view = {}
    for lineno, record in records(root):
        key, verdict = _keyed(lineno, record)
        view[key] = verdict
    return view
