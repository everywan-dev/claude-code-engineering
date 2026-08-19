"""End-to-end tests for `derive`: the re-derived knowledge index.

Fixtures are synthetic adopter trees: a `knowledge/` directory holding curated
knowledge units, each a Markdown file whose frontmatter carries the contract.
`derive` writes `knowledge-index.md` in the working directory (never inside
`knowledge/`, since anything ending in `.md` there is read as a unit).
"""

import re

INDEX_FILENAME = "knowledge-index.md"

ACTIVE_UNIT = """\
id: kb-0001
evidence: measured
anchors: []
"""


def test_derive_writes_the_index_for_a_single_unit(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "derive: 1 unit(s) indexed" in result.stdout

    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert index.startswith("# Knowledge index\n")
    assert "Derived: " in index
    assert "Basis: 1 unit(s) under knowledge/" in index
    assert "| kb-0001 | active | measured | unknown |" in index


def test_many_to_one_supersession_marks_the_superseded_unit(
    adopter_dir, write_unit, run_cli
):
    # kb-0001 is superseded by both kb-0002 and kb-0003 (many-to-one): the
    # effective state names every superseding id, sorted, and the superseded
    # unit is still listed, never omitted.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")
    write_unit(
        "kb-0003.md",
        "id: kb-0003\nevidence: hypothesis\nsupersedes:\n  - kb-0001\nanchors: []\n",
    )
    write_unit(
        "kb-0002.md",
        "id: kb-0002\nevidence: verifiable\nsupersedes:\n  - kb-0001\nanchors: []\n",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "Basis: 3 unit(s) under knowledge/" in index
    assert "| kb-0001 | superseded by kb-0002, kb-0003 | measured | unknown |" in index
    assert "| kb-0002 | active | verifiable | unknown |" in index
    assert "| kb-0003 | active | hypothesis | unknown |" in index


# --- validation gates derive ---------------------------------------------


def test_a_validation_error_gates_and_writes_nothing(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: probable\nanchors: []\n")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: evidence: " in result.stderr
    assert not (adopter_dir / INDEX_FILENAME).exists()


def test_a_validation_warning_does_not_gate_derive(adopter_dir, write_unit, run_cli):
    # No anchors is a WARNING, not an ERROR; derive still writes the index.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: knowledge/kb-0001.md: anchors: " in result.stderr
    assert (adopter_dir / INDEX_FILENAME).exists()


# --- --check ---------------------------------------------------------------


def test_check_without_a_prior_derive_gates_pointing_at_derive(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", ACTIVE_UNIT)

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert INDEX_FILENAME in result.stderr
    assert "derive" in result.stderr
    assert not (adopter_dir / INDEX_FILENAME).exists()


def test_check_passes_right_after_derive(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "derive --check: index is up to date" in result.stdout


def test_check_ignores_only_the_derived_timestamp(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    lines = index_path.read_text(encoding="utf-8").split("\n")
    lines = [
        "Derived: 2000-01-01T00:00:00Z" if line.startswith("Derived: ") else line
        for line in lines
    ]
    index_path.write_text("\n".join(lines), encoding="utf-8")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


def test_a_hand_edited_index_fails_check_with_error(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    mutated = index_path.read_text(encoding="utf-8").replace(
        "| kb-0001 | active | measured | unknown |",
        "| kb-0001 | active | hypothesis | unknown |",
    )
    index_path.write_text(mutated, encoding="utf-8")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert f"ERROR: {INDEX_FILENAME}: index: " in result.stderr
    # --check never writes, even when it fails.
    assert index_path.read_text(encoding="utf-8") == mutated


def test_deleting_the_derived_line_fails_check(adopter_dir, write_unit, run_cli):
    # The timestamp's value is ignored, but the line itself is content: a
    # hand-deleted `Derived:` line is a mutation and must fail the check.
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    lines = index_path.read_text(encoding="utf-8").split("\n")
    lines = [line for line in lines if not line.startswith("Derived: ")]
    index_path.write_text("\n".join(lines), encoding="utf-8")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert f"ERROR: {INDEX_FILENAME}: index: " in result.stderr
    assert "Derived" in result.stderr


def test_a_mismatch_names_the_line_as_numbered_on_disk(
    adopter_dir, write_unit, run_cli
):
    # The row sits on line 8 of the file (title, blank, Derived, Basis,
    # blank, header, separator, row); the message must use that numbering.
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    mutated = index_path.read_text(encoding="utf-8").replace(
        "| kb-0001 | active | measured | unknown |",
        "| kb-0001 | active | hypothesis | unknown |",
    )
    index_path.write_text(mutated, encoding="utf-8")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert "at line 8" in result.stderr


def test_an_extra_trailing_line_fails_check_naming_the_line(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write("\n")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert "at line 9" in result.stderr
    assert "end of file" in result.stderr
    assert "['']" not in result.stderr


def test_check_does_not_rewrite_the_index_on_success(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    index_path = adopter_dir / INDEX_FILENAME
    before = index_path.read_text(encoding="utf-8")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert index_path.read_text(encoding="utf-8") == before


def test_check_with_a_validation_error_gates_without_reading_the_index(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    run_cli("derive", cwd=adopter_dir)
    write_unit("kb-0002.md", "id: kb-0002\nevidence: probable\nanchors: []\n")

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0002.md: evidence: " in result.stderr


# --- PATH resolution mirrors `validate` -------------------------------------


def test_a_missing_default_directory_gates_and_points_at_init(adopter_dir, run_cli):
    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "knowledge" in result.stderr
    assert "init" in result.stderr
    assert not (adopter_dir / INDEX_FILENAME).exists()


def test_a_missing_explicit_path_gates(adopter_dir, run_cli):
    result = run_cli("derive", "nowhere", cwd=adopter_dir)

    assert result.returncode == 1
    assert "nowhere" in result.stderr


def test_an_explicit_path_overrides_the_default_directory(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    (adopter_dir / "knowledge").rename(adopter_dir / "facts")

    result = run_cli("derive", "facts", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "Basis: 1 unit(s) under facts/" in index


def test_a_single_file_can_be_the_derivation_source(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)
    write_unit("kb-0002.md", "id: kb-0002\nevidence: probable\nanchors: []\n")

    result = run_cli("derive", "knowledge/kb-0001.md", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "Basis: 1 unit(s) under knowledge/kb-0001.md" in index
    assert "| kb-0001 | active | measured | unknown |" in index


def test_derive_never_mutates_the_source_units(adopter_dir, write_unit, run_cli):
    path = write_unit("kb-0001.md", ACTIVE_UNIT)
    before = path.read_text(encoding="utf-8")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert path.read_text(encoding="utf-8") == before


# --- the declared extension applies to derive too ---------------------------


def test_a_declared_extension_violation_gates_derive(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document(
        "validated-memory.md",
        "extension:\n  schema: knowledge-extension.md\n  version: \"1\"\n",
    )
    write_document(
        "knowledge-extension.md",
        "fields:\n  - name: domain\n    type: enum\n    values:\n      - network\n",
    )
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors: []\ndomain: telepathy\n",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: domain: " in result.stderr
    assert not (adopter_dir / INDEX_FILENAME).exists()


# --- derivation date and basis format ---------------------------------------


def test_derived_declares_an_iso8601_utc_timestamp(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", ACTIVE_UNIT)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    match = re.search(r"^Derived: (.+)$", index, re.MULTILINE)
    assert match, index
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", match.group(1))


def test_an_empty_knowledge_directory_warns_and_derives_an_empty_index(
    adopter_dir, run_cli
):
    (adopter_dir / "knowledge").mkdir()

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "Basis: 0 unit(s) under knowledge/" in index


def test_a_verdict_log_that_is_not_utf8_is_reported_not_raised(
    adopter_dir, write_unit, run_cli
):
    # The log is the reader's source of verdicts. Fail-loud means a finding
    # naming the file, not a traceback: a traceback tells the adopter nothing
    # about which file to look at and gates by crashing rather than by rule.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")
    (adopter_dir / "verdicts.jsonl").write_bytes(b"\xff\xfe not utf-8\n")

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "verdicts.jsonl" in result.stderr
    assert "ERROR" in result.stderr


def test_a_verdict_record_whose_key_fields_are_not_strings_is_reported(
    adopter_dir, write_unit, run_cli
):
    # A hand-edited log can carry anything. An unhashable value used to reach
    # the dict key and raise TypeError instead of being reported with its line.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")
    (adopter_dir / "verdicts.jsonl").write_text(
        '{"unit": [], "system": "repo-a", "kind": "git_ref", "verdict": "current"}\n',
        encoding="utf-8",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "verdicts.jsonl:1:" in result.stderr



# --- an anchor is identified by what it points at ----------------------------

BY_REF_PROBE = """\
import sys, json
env = json.loads(sys.stdin.read())
ref = env.get("payload", {}).get("ref")
print(json.dumps({"verdict": "drifted" if ref == "main" else "current"}))
"""

TWO_REFS_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload:
      ref: main
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload:
      ref: release
"""


def test_two_anchors_of_one_system_and_kind_keep_their_own_verdicts(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # Two refs of the same repository are the same `(system, kind)` and a
    # legitimate pair. Keyed on that pair alone, the second probed anchor
    # overwrote the first and the drift vanished: the index said `current`
    # about a unit with a drifted anchor -- a false "still true", and one
    # whose answer depended on the order the anchors were written in.
    command = write_probe("probes/by_ref.py", BY_REF_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {command}\n")
    write_unit("kb-0001.md", TWO_REFS_UNIT)
    probed = run_cli("probe", cwd=adopter_dir)
    assert "1 current, 1 drifted" in probed.stdout

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted |" in index


def test_the_verdict_of_one_anchor_does_not_move_when_another_is_reprobed(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # Re-probing appends; history is never rewritten. Each anchor must read
    # its own latest record, not the log's latest record for the pair.
    command = write_probe("probes/by_ref.py", BY_REF_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {command}\n")
    write_unit("kb-0001.md", TWO_REFS_UNIT)
    run_cli("probe", cwd=adopter_dir)
    run_cli("probe", cwd=adopter_dir)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted |" in index


ONE_ANCHOR_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload:
      ref: main
"""


def test_a_record_written_before_payloads_is_never_attributed_to_an_anchor(
    adopter_dir, write_unit, run_cli
):
    # A log written by an earlier version carries no payload, so it cannot say
    # what was probed -- not even for a unit with a single anchor, because the
    # anchor may have been re-captured since and now point somewhere else.
    # Attributing it would risk reporting `current` for something that has
    # drifted, which is the failure the payload was added to prevent. The
    # record is kept in the log and ignored; the anchor reads `unknown` until
    # it is probed again.
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)
    (adopter_dir / "verdicts.jsonl").write_text(
        '{"recorded_at": "2026-08-01T00:00:00Z", "unit": "kb-0001", '
        '"system": "repo-a", "kind": "git_ref", "verdict": "current", '
        '"detail": null}\n',
        encoding="utf-8",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | unknown (repo-a) |" in index


def test_a_record_whose_payload_is_null_is_rejected_not_read_as_absent(
    adopter_dir, write_unit, run_cli
):
    # Presence, not value: an explicit `null` is a malformed record. Reading
    # it as "written before payloads" would file it under the key reserved for
    # records that genuinely predate them.
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)
    (adopter_dir / "verdicts.jsonl").write_text(
        '{"recorded_at": "2026-08-01T00:00:00Z", "unit": "kb-0001", '
        '"system": "repo-a", "kind": "git_ref", "payload": null, '
        '"verdict": "current", "detail": null}\n',
        encoding="utf-8",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 1
    assert "verdicts.jsonl:1:" in result.stderr
    assert "'payload' field is not a mapping" in result.stderr



def test_a_record_with_a_payload_supersedes_one_written_without(
    adopter_dir, write_unit, run_cli
):
    # The anchor reads its own record and ignores the one that cannot say what
    # it measured -- whichever order the two were written in.
    write_unit("kb-0001.md", ONE_ANCHOR_UNIT)
    (adopter_dir / "verdicts.jsonl").write_text(
        '{"recorded_at": "2026-08-01T00:00:00Z", "unit": "kb-0001", '
        '"system": "repo-a", "kind": "git_ref", "verdict": "current", '
        '"detail": null}\n'
        '{"recorded_at": "2026-08-02T00:00:00Z", "unit": "kb-0001", '
        '"system": "repo-a", "kind": "git_ref", "payload": {"ref": "main"}, '
        '"verdict": "drifted", "detail": null}\n',
        encoding="utf-8",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted |" in index


def test_a_payload_matches_whatever_order_its_keys_were_written_in(
    adopter_dir, write_unit, run_cli
):
    # The anchor writes `ref` then `repo`; the record writes `repo` then `ref`.
    # They are the same payload, so they are the same anchor: the key is
    # canonical, not textual.
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors:\n"
        "  - system: repo-a\n    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload:\n      ref: main\n      repo: '.'\n",
    )
    (adopter_dir / "verdicts.jsonl").write_text(
        '{"recorded_at": "2026-08-02T00:00:00Z", "unit": "kb-0001", '
        '"system": "repo-a", "kind": "git_ref", '
        '"payload": {"repo": ".", "ref": "main"}, '
        '"verdict": "drifted", "detail": null}\n',
        encoding="utf-8",
    )

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted |" in index



# --- the verdict column reads the real service view of verdicts.jsonl -------

CURRENT_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "current"}))
"""

DRIFTED_PROBE = """\
import sys, json
sys.stdin.read()
print(json.dumps({"verdict": "drifted"}))
"""

TWO_ANCHOR_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: repo-a
    kind: git_ref
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
  - system: repo-b
    kind: unregistered_kind
    captured_at: 2026-08-01T00:00:00Z
    payload: {}
"""


def test_a_unit_never_probed_stays_unknown_naming_every_system(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", TWO_ANCHOR_UNIT)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | unknown (repo-a, repo-b) |" in index


def test_derive_reports_the_worst_verdict_and_flags_unknown_systems(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    write_unit("kb-0001.md", TWO_ANCHOR_UNIT)
    run_cli("probe", cwd=adopter_dir)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    # repo-a is current, repo-b was never registered (unknown); the worst of
    # the two is unknown, and the cell names the system(s) behind it.
    assert "| kb-0001 | active | measured | unknown (repo-b) |" in index


def test_derive_flags_unknowns_alongside_a_worse_drifted_verdict(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    drifted_cmd = write_probe("probes/drifted_probe.py", DRIFTED_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {drifted_cmd}\n")
    write_unit("kb-0001.md", TWO_ANCHOR_UNIT)
    run_cli("probe", cwd=adopter_dir)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted (unknown: repo-b) |" in index


def test_derive_reports_a_plain_current_verdict_when_every_anchor_is_current(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors:\n"
        "  - system: repo-a\n    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n    payload: {}\n",
    )
    run_cli("probe", cwd=adopter_dir)

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | current |" in index


def test_only_active_units_are_probed_a_superseded_unit_keeps_its_last_verdict(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # kb-0001 is superseded by kb-0002 inside the same validated set; `probe`
    # only walks active units, so kb-0001's anchor is never dispatched and
    # its cell stays unknown even though a probe is registered for its kind.
    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors:\n"
        "  - system: repo-a\n    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n    payload: {}\n",
    )
    write_unit(
        "kb-0002.md",
        "id: kb-0002\nevidence: measured\nsupersedes:\n  - kb-0001\nanchors:\n"
        "  - system: repo-b\n    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n    payload: {}\n",
    )

    probe_result = run_cli("probe", cwd=adopter_dir)
    assert probe_result.returncode == 0, probe_result.stderr
    assert "1 anchor(s) probed across 1 unit(s)" in probe_result.stdout

    result = run_cli("derive", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    index = (adopter_dir / INDEX_FILENAME).read_text(encoding="utf-8")
    assert "| kb-0001 | superseded by kb-0002 | measured | unknown (repo-a) |" in index
    assert "| kb-0002 | active | measured | current |" in index


def test_probing_after_a_derive_fails_check_because_verdicts_are_index_content(
    adopter_dir, write_document, write_unit, write_probe, run_cli
):
    # `--check` protects the whole recalculated index, and the verdict column
    # is part of it: probing after a derive changes what the index would say,
    # so a stale on-disk index correctly fails --check.
    write_unit("kb-0001.md", TWO_ANCHOR_UNIT)
    run_cli("derive", cwd=adopter_dir)

    current_cmd = write_probe("probes/current_probe.py", CURRENT_PROBE)
    write_document("validated-memory.md", f"probes:\n  git_ref: {current_cmd}\n")
    run_cli("probe", cwd=adopter_dir)

    result = run_cli("derive", "--check", cwd=adopter_dir)

    assert result.returncode == 1
    assert f"ERROR: {INDEX_FILENAME}: index: " in result.stderr
