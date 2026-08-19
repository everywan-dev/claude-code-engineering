"""The `probe` subcommand: run freshness probes and record ternary verdicts.

`probe` requires a valid source: it runs the same validation as `validate`
first (the base contract plus the adopter's declared extension) and probes
nothing when that validation reports an ERROR. It then walks the anchors of
every *active* unit -- one superseded within the validated set is not current
-- and dispatches each anchor to the probe registered for its `kind` in
`validated-memory.md`'s `probes` map.

Probe contract: the registered command is split with `shlex.split` and run
without a shell. It receives the anchor's envelope on stdin, as JSON:
`{"system": ..., "kind": ..., "captured_at": ..., "payload": {...}}` -- no
unit id, the producer/store boundary. It answers on stdout, as JSON:
`{"verdict": "current" | "drifted" | "unknown", "detail": "..."}` (`detail`
optional), with exit 0. Any failure falls back to `unknown`, with a note
explaining why, and never aborts the run: no probe registered for the
anchor's `kind` (or no configuration at all), a command that cannot be run,
a non-zero exit, unparseable stdout, or a verdict outside the domain.

Every anchor probed is appended to `verdicts.jsonl` (see `verdicts`), one
JSON line per anchor, regardless of the outcome.
"""

import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import derive as derive_module
from . import extension as extension_module
from . import validate
from . import verdicts as verdicts_module
from .findings import EXIT_ERROR, EXIT_OK, WARNING, Finding


def run(path, stdout, stderr):
    """Probe every active unit's anchors and record their verdicts."""
    documents, ok = validate.gated_source(path, stderr)
    if not ok:
        return EXIT_ERROR

    registry = extension_module.probes(Path())
    records, probe_findings = _probe_all(documents, registry)

    if records:
        try:
            verdicts_module.append(records)
        except OSError as error:
            print(
                f"ERROR: {verdicts_module.LOG_FILENAME}: log: cannot be written: "
                f"{error}",
                file=stderr,
            )
            return EXIT_ERROR

    for finding in probe_findings:
        print(finding.render(), file=stderr)

    print(_summary(records), file=stdout)
    return EXIT_OK


def _probe_all(documents, registry):
    """Dispatch every anchor of every active unit. Returns `(records, findings)`."""
    states = derive_module.effective_states(documents)
    recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    recorded_at = recorded_at.replace("+00:00", "Z")

    records = []
    findings = []
    for unit_id in sorted(states):
        data, state = states[unit_id]
        if state != "active":
            continue
        for position, anchor in enumerate(data.get("anchors") or []):
            verdict, detail, note = _dispatch(anchor, registry)
            if note:
                findings.append(
                    Finding(WARNING, unit_id, f"anchors[{position}]", note)
                )
            records.append(
                {
                    "recorded_at": recorded_at,
                    "unit": unit_id,
                    "system": anchor.get("system"),
                    "kind": anchor.get("kind"),
                    "payload": anchor.get("payload"),
                    "verdict": verdict,
                    "detail": detail,
                }
            )
    return records, findings


def _dispatch(anchor, registry):
    """Run the probe registered for `anchor`'s kind. Never raises.

    Returns `(verdict, detail, note)`: `note` is None on success, and set to
    an explanation whenever the outcome falls back to `unknown`.
    """
    kind = anchor.get("kind")
    command = registry.get(kind)
    if not command:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"no probe registered for kind '{kind}'",
        )

    try:
        argv = shlex.split(command)
    except ValueError as error:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"probe command '{command}' cannot be parsed: {error}",
        )

    envelope = json.dumps(
        {
            "system": anchor.get("system"),
            "kind": anchor.get("kind"),
            "captured_at": anchor.get("captured_at"),
            "payload": anchor.get("payload"),
        }
    )

    try:
        result = subprocess.run(
            argv, input=envelope, capture_output=True, text=True, check=False
        )
    except OSError as error:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"probe command '{command}' could not be run: {error}",
        )

    if result.returncode != 0:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"probe command '{command}' exited {result.returncode}: "
            f"{result.stderr.strip()}",
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"probe command '{command}' produced unparseable output on stdout",
        )

    if not isinstance(payload, dict) or payload.get("verdict") not in verdicts_module.VERDICTS:
        return (
            verdicts_module.UNKNOWN,
            None,
            f"probe command '{command}' returned a verdict outside "
            + ", ".join(verdicts_module.VERDICTS),
        )

    return payload["verdict"], payload.get("detail"), None


def _summary(records):
    counts = {verdict: 0 for verdict in verdicts_module.VERDICTS}
    units = set()
    for record in records:
        counts[record["verdict"]] += 1
        units.add(record["unit"])
    return (
        f"probe: {len(records)} anchor(s) probed across {len(units)} unit(s): "
        f"{counts[verdicts_module.CURRENT]} current, "
        f"{counts[verdicts_module.DRIFTED]} drifted, "
        f"{counts[verdicts_module.UNKNOWN]} unknown"
    )
