"""End-to-end tests for `probe`: the freshness-probe framework.

Fixtures register fake probes in `validated-memory.md`'s `probes:` map. A fake
probe is a small Python script invoked through the interpreter
(`sys.executable script.py`), so no `chmod +x` or shebang is needed: the
registered command is just split with `shlex.split`, exactly like any other
probe command would be.

`probe` writes one append-only JSON line per anchor probed to `verdicts.jsonl`
in the working directory. That file is a produced artifact, like
`knowledge-index.md`, so tests read it directly instead of importing any
package internals.
"""

import json

VERDICT_LOG = "verdicts.jsonl"

ACTIVE_UNIT = """\
id: kb-0001
evidence: measured
anchors: []
"""


def _records(adopter_dir):
    path = adopter_dir / VERDICT_LOG
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --- the validation gate (shared with validate/derive) ----------------------


def test_a_validation_error_gates_and_probes_nothing(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: probable\nanchors: []\n")

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: evidence: " in result.stderr
    assert not (adopter_dir / VERDICT_LOG).exists()


def test_a_validation_warning_does_not_gate_probe(adopter_dir, write_unit, run_cli):
    # No anchors is a WARNING, not an ERROR; probe still runs (there is
    # nothing to probe, but the run itself is not blocked).
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: knowledge/kb-0001.md: anchors: " in result.stderr


def test_a_missing_default_directory_gates_and_points_at_init(adopter_dir, run_cli):
    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 1
    assert "knowledge" in result.stderr
    assert "init" in result.stderr


def test_an_explicit_path_overrides_the_default_directory(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    (adopter_dir / "knowledge").rename(adopter_dir / "facts")

    result = run_cli("probe", "facts", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


# --- the probe contract: dispatch by kind, the three verdicts, detail -------

CURRENT_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "current"}))
"""

DRIFTED_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "drifted", "detail": "branch moved since captured_at"}))
"""

UNKNOWN_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "unknown", "detail": "probe could not reach the system"}))
"""

THREE_ANCHOR_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
  - system: api-b
    kind: http_health
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
  - system: queue-c
    kind: sync_state
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
"""


def test_probe_dispatches_by_kind_and_records_the_three_verdicts_with_detail(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    drifted_cmd = write_probe("probes/drifted_probe.py", DRIFTED_PROBE)
    unknown_cmd = write_probe("probes/unknown_probe.py", UNKNOWN_PROBE)
    write_document(
        "validated-memory.md",
        "probes:\n"
        f"  git_ref: {current_cmd}\n"
        f"  http_health: {drifted_cmd}\n"
        f"  sync_state: {unknown_cmd}\n",
    )
    write_unit("kb-0001.md", THREE_ANCHOR_UNIT)

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (
        "probe: 3 anchor(s) probed across 1 unit(s): "
        "1 current, 1 drifted, 1 unknown" in result.stdout
    )

    records = {(record["system"], record["kind"]): record for record in _records(adopter_dir)}
    assert records[("repo-a", "git_ref")]["verdict"] == "current"
    assert records[("repo-a", "git_ref")]["detail"] is None
    assert records[("api-b", "http_health")]["verdict"] == "drifted"
    assert (
        records[("api-b", "http_health")]["detail"] == "branch moved since captured_at"
    )
    assert records[("queue-c", "sync_state")]["verdict"] == "unknown"
    assert (
        records[("queue-c", "sync_state")]["detail"]
        == "probe could not reach the system"
    )
    for record in records.values():
        assert record["unit"] == "kb-0001"
        assert "recorded_at" in record


# --- failure never aborts the run: unknown with a note -----------------------

CRASH_PROBE = """\
raise RuntimeError("simulated probe crash")
"""

UNREGISTERED_AND_CRASHING_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: no_such_probe
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
  - system: repo-b
    kind: crashy
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
"""


def test_a_missing_registration_and_a_crashing_probe_both_yield_unknown_without_aborting(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    crash_cmd = write_probe("probes/crash_probe.py", CRASH_PROBE)
    write_document("validated-memory.md", f"probes:\n  crashy: {crash_cmd}\n")
    write_unit("kb-0001.md", UNREGISTERED_AND_CRASHING_UNIT)

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (
        "probe: 2 anchor(s) probed across 1 unit(s): "
        "0 current, 0 drifted, 2 unknown" in result.stdout
    )
    assert "WARNING: kb-0001: anchors[0]: " in result.stderr
    assert "no_such_probe" in result.stderr
    assert "WARNING: kb-0001: anchors[1]: " in result.stderr

    records = {record["system"]: record for record in _records(adopter_dir)}
    assert records["repo-a"]["verdict"] == "unknown"
    assert records["repo-b"]["verdict"] == "unknown"


GARBAGE_PROBE = """\
print("not json")
"""

OUT_OF_DOMAIN_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "maybe"}))
"""


def test_a_missing_executable_unparseable_output_and_an_out_of_domain_verdict_all_yield_unknown(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    garbage_cmd = write_probe("probes/garbage_probe.py", GARBAGE_PROBE)
    out_of_domain_cmd = write_probe("probes/out_of_domain_probe.py", OUT_OF_DOMAIN_PROBE)
    write_document(
        "validated-memory.md",
        "probes:\n"
        "  missing_exe: /no/such/executable-at-all\n"
        f"  garbage: {garbage_cmd}\n"
        f"  out_of_domain: {out_of_domain_cmd}\n",
    )
    write_unit(
        "kb-0001.md",
        "id: kb-0001\n"
        "evidence: measured\n"
        "anchors:\n"
        "  - system: repo-a\n"
        "    kind: missing_exe\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload: {}\n"
        "  - system: repo-b\n"
        "    kind: garbage\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload: {}\n"
        "  - system: repo-c\n"
        "    kind: out_of_domain\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload: {}\n",
    )

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (
        "probe: 3 anchor(s) probed across 1 unit(s): "
        "0 current, 0 drifted, 3 unknown" in result.stdout
    )
    records = {record["system"]: record for record in _records(adopter_dir)}
    assert records["repo-a"]["verdict"] == "unknown"
    assert records["repo-b"]["verdict"] == "unknown"
    assert records["repo-c"]["verdict"] == "unknown"


def test_with_no_configuration_at_all_every_anchor_falls_back_to_unknown(
    adopter_dir, write_unit, run_cli
):
    # No `validated-memory.md` means an empty probe registry: the same
    # fallback path as a `kind` that is simply not registered in it.
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: kb-0001: anchors[0]: no probe registered for kind 'git_ref'" in (
        result.stderr
    )
    records = _records(adopter_dir)
    assert len(records) == 1
    assert records[0]["verdict"] == "unknown"


# --- append-only history; the service view is the latest record -------------

ONE_ANCHOR_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
"""


def test_re_probing_appends_to_the_log_without_clobbering_history(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)

    run_cli("probe", cwd=adopter_dir)

    drifted_cmd = write_probe("probes/drifted_probe.py", DRIFTED_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {drifted_cmd}\n")

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    records = _records(adopter_dir)
    # History is never rewritten: both runs' records are on the log, in order.
    assert len(records) == 2
    assert records[0]["verdict"] == "current"
    assert records[1]["verdict"] == "drifted"
    # The service view -- what a reader wants -- is the latest one.
    assert records[-1]["verdict"] == "drifted"


# --- an unwritable log is an operational ERROR, not a data finding ----------


def test_an_unwritable_verdict_log_is_an_operational_error(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # `verdicts.jsonl` is a directory, not a file: appending to it raises
    # OSError. Verdicts are data, so a `drifted` outcome never gates -- but a
    # registry that cannot be written is an operational failure and must.
    (adopter_dir / VERDICT_LOG).mkdir()
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 1
    assert f"ERROR: {VERDICT_LOG}: " in result.stderr


# --- a corrupt verdict log fails loud for its readers -------------------------


def test_a_corrupt_verdict_log_gates_derive_with_an_error(
    adopter_dir, write_unit, run_cli
):
    # `probe` only appends; `derive` is the reader, and a reader must never
    # guess about a log it cannot parse -- nor dump a raw traceback.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")
    (adopter_dir / "verdicts.jsonl").write_text("not json\n", encoding="utf-8")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: verdicts.jsonl:1: " in result.stderr
    assert "Traceback" not in result.stderr
    assert not (adopter_dir / "knowledge-index.md").exists()


def test_a_verdict_outside_the_domain_in_the_log_gates_derive(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")
    record = (
        '{"kind": "git_ref", "recorded_at": "2026-08-12T08:00:00Z", '
        '"system": "repo-a", "unit": "kb-0001", "verdict": "maybe"}\n'
    )
    (adopter_dir / "verdicts.jsonl").write_text(record, encoding="utf-8")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: verdicts.jsonl:1: " in result.stderr
    assert "maybe" in result.stderr
    assert "Traceback" not in result.stderr


def test_the_record_carries_the_payload_that_was_probed(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # The log is a historical record. Without the payload it can say that
    # something of some kind in some system was probed, but not which thing --
    # a record that cannot say what it measured is not evidence.
    command = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {command}\n")
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors:\n"
        "  - system: repo-a\n    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n    payload:\n      ref: main\n",
    )

    run_cli("probe", cwd=adopter_dir)

    log = (adopter_dir / "verdicts.jsonl").read_text(encoding="utf-8")
    record = json.loads(log.splitlines()[0])
    assert record["payload"] == {"ref": "main"}
