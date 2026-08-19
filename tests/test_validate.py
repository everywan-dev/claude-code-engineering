"""End-to-end tests for `validate` against the base contract.

Fixtures are synthetic adopter trees: a `knowledge/` directory holding curated
knowledge units, each a Markdown file whose frontmatter carries the contract.
"""

VALID_UNIT = """\
id: kb-0001
evidence: measured
anchors:
  - system: adopter-repo
    kind: git_ref
    captured_at: 2026-08-11T10:00:00Z
    payload:
      repo: .
      ref: refs/heads/main
provenance:
  - docs/measurements/run-2026-08-11.md
"""

SUPERSEDING_UNIT = """\
id: kb-0002
evidence: hypothesis
supersedes:
  - kb-0001
anchors:
  - system: adopter-repo
    kind: git_ref
    captured_at: 2026-08-11
    payload: {}
"""


def test_valid_units_pass_clean(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", VALID_UNIT)
    write_unit("kb-0002.md", SUPERSEDING_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "WARNING" not in result.stderr
    assert "2" in result.stdout


def test_units_are_found_recursively(adopter_dir, write_unit, run_cli):
    write_unit("nested/deep/kb-0001.md", VALID_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "1" in result.stdout


def test_explicit_path_overrides_the_default_directory(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", VALID_UNIT)
    (adopter_dir / "knowledge").rename(adopter_dir / "facts")

    result = run_cli("validate", "facts", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


# --- base contract: field-level errors ---------------------------------------

INVALID_FIELDS = [
    (
        "evidence_out_of_domain",
        "id: kb-0001\nevidence: probable\n",
        "evidence",
    ),
    (
        "evidence_missing",
        "id: kb-0001\n",
        "evidence",
    ),
    (
        "id_missing",
        "evidence: measured\n",
        "id",
    ),
    (
        "id_not_a_string",
        "id:\n  - kb-0001\nevidence: measured\n",
        "id",
    ),
    (
        "unknown_top_level_field",
        "id: kb-0001\nevidence: measured\nseverity: high\n",
        "severity",
    ),
    (
        "anchor_envelope_incomplete",
        (
            "id: kb-0001\nevidence: measured\n"
            "anchors:\n  - system: repo\n    kind: git_ref\n"
        ),
        "anchors[0]",
    ),
    (
        "anchor_unknown_field",
        (
            "id: kb-0001\nevidence: measured\n"
            "anchors:\n  - system: repo\n    kind: git_ref\n"
            "    captured_at: 2026-08-11\n    payload: {}\n    extra: nope\n"
        ),
        "anchors[0]",
    ),
    (
        "anchor_captured_at_not_iso",
        (
            "id: kb-0001\nevidence: measured\n"
            "anchors:\n  - system: repo\n    kind: git_ref\n"
            "    captured_at: yesterday\n    payload: {}\n"
        ),
        "anchors[0].captured_at",
    ),
    (
        "anchor_captured_at_not_a_real_date",
        (
            "id: kb-0001\nevidence: measured\n"
            "anchors:\n  - system: repo\n    kind: git_ref\n"
            "    captured_at: 2026-02-31\n    payload: {}\n"
        ),
        "anchors[0].captured_at",
    ),
    (
        "anchor_payload_not_a_mapping",
        (
            "id: kb-0001\nevidence: measured\n"
            "anchors:\n  - system: repo\n    kind: git_ref\n"
            "    captured_at: 2026-08-11\n    payload: []\n"
        ),
        "anchors[0].payload",
    ),
    (
        "anchors_not_a_list",
        "id: kb-0001\nevidence: measured\nanchors:\n  system: repo\n",
        "anchors",
    ),
    (
        "provenance_not_a_list",
        "id: kb-0001\nevidence: measured\nprovenance: docs/source.md\n",
        "provenance",
    ),
]


def test_every_invalid_unit_gates_naming_unit_and_field(adopter_dir, write_unit, run_cli):
    for name, frontmatter, _field in INVALID_FIELDS:
        write_unit(f"{name}.md", frontmatter)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    for name, _frontmatter, field in INVALID_FIELDS:
        expected = f"ERROR: knowledge/{name}.md: {field}: "
        assert expected in result.stderr, (
            f"{name}: missing finding for field '{field}'\n{result.stderr}"
        )


def test_missing_frontmatter_is_an_error(adopter_dir, run_cli):
    path = adopter_dir / "knowledge" / "no-frontmatter.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Just a document\n", encoding="utf-8")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "no-frontmatter.md" in result.stderr
    assert "frontmatter" in result.stderr


def test_a_contract_finding_names_the_unit_and_field_without_a_line(
    adopter_dir, write_unit, run_cli
):
    # A contract rule speaks about the unit as a whole, so it carries no line;
    # only the parser knows where it stopped (see the frontmatter tests).
    write_unit("kb-0001.md", "id: kb-0001\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert (
        "ERROR: knowledge/kb-0001.md: evidence: required field is missing"
        in result.stderr
    )


# --- base contract: cross-unit errors ----------------------------------------


def test_duplicate_id_gates_naming_both_units(adopter_dir, write_unit, run_cli):
    write_unit("first.md", VALID_UNIT)
    write_unit("second.md", VALID_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "duplicate id 'kb-0001'" in result.stderr
    assert "knowledge/first.md" in result.stderr
    assert "knowledge/second.md" in result.stderr


def test_supersedes_pointing_at_a_missing_id_gates(adopter_dir, write_unit, run_cli):
    write_unit(
        "kb-0002.md",
        "id: kb-0002\nevidence: measured\nsupersedes:\n  - kb-0404\nanchors: []\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0002.md: supersedes: " in result.stderr
    assert "kb-0404" in result.stderr


def test_self_supersession_gates(adopter_dir, write_unit, run_cli):
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nsupersedes:\n  - kb-0001\nanchors: []\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "supersedes itself" in result.stderr


def test_supersession_across_files_resolves_in_any_order(
    adopter_dir, write_unit, run_cli
):
    # The superseding unit sorts before the unit it supersedes.
    write_unit(
        "aaa.md",
        "id: kb-0002\nevidence: measured\nsupersedes:\n  - kb-0001\nanchors: []\n",
    )
    write_unit("zzz.md", "id: kb-0001\nevidence: measured\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


# --- WARNING does not gate; ERROR does ---------------------------------------


def test_a_unit_without_anchors_warns_without_gating(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: knowledge/kb-0001.md: anchors: " in result.stderr
    assert "1 warning(s)" in result.stdout


def test_an_empty_anchor_list_warns_without_gating(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr


def test_warnings_and_errors_are_reported_apart(adopter_dir, write_unit, run_cli):
    write_unit("warned.md", "id: kb-0001\nevidence: measured\n")
    write_unit("failed.md", "id: kb-0002\nevidence: probable\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "1 error(s)" in result.stdout
    assert "2 warning(s)" in result.stdout


# --- target resolution --------------------------------------------------------


def test_a_missing_default_directory_gates_and_points_at_init(adopter_dir, run_cli):
    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "knowledge" in result.stderr
    assert "init" in result.stderr


def test_a_missing_explicit_path_gates(adopter_dir, run_cli):
    result = run_cli("validate", "nowhere", cwd=adopter_dir)

    assert result.returncode == 1
    assert "nowhere" in result.stderr


def test_an_empty_knowledge_directory_warns_without_gating(adopter_dir, run_cli):
    (adopter_dir / "knowledge").mkdir()

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr


def test_a_single_file_can_be_validated(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", VALID_UNIT)
    write_unit("kb-0002.md", "id: kb-0002\nevidence: probable\nanchors: []\n")

    result = run_cli("validate", "knowledge/kb-0001.md", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "1 unit(s) checked" in result.stdout


def test_supersession_resolves_against_the_validated_set_only(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")
    write_unit("kb-0002.md", SUPERSEDING_UNIT)

    result = run_cli("validate", "knowledge/kb-0002.md", cwd=adopter_dir)

    assert result.returncode == 1
    assert "does not exist in the validated set" in result.stderr


# --- supersession cycles -----------------------------------------------------


def _unit(unit_id, supersedes):
    return f"id: {unit_id}\nevidence: measured\nsupersedes:\n  - {supersedes}\n"


def test_a_two_unit_supersession_cycle_gates(adopter_dir, write_unit, run_cli):
    # Both are superseded, so neither is live: the pair vanishes from the
    # index's active view and `probe` stops probing it, since only active
    # units are probed. Nothing was deleted, yet nothing is checked either.
    write_unit("kb-0001.md", _unit("kb-0001", "kb-0002"))
    write_unit("kb-0002.md", _unit("kb-0002", "kb-0001"))

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "supersession cycle" in result.stderr
    assert "kb-0001" in result.stderr
    assert "kb-0002" in result.stderr


def test_a_longer_supersession_cycle_gates(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", _unit("kb-0001", "kb-0002"))
    write_unit("kb-0002.md", _unit("kb-0002", "kb-0003"))
    write_unit("kb-0003.md", _unit("kb-0003", "kb-0001"))

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "supersession cycle" in result.stderr
    assert result.stderr.count("supersession cycle") == 1


def test_a_supersession_chain_that_ends_is_clean(adopter_dir, write_unit, run_cli):
    # kb-0003 supersedes kb-0002 supersedes kb-0001: a chain with a live end.
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\n")
    write_unit("kb-0002.md", _unit("kb-0002", "kb-0001"))
    write_unit("kb-0003.md", _unit("kb-0003", "kb-0002"))

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "cycle" not in result.stderr


def test_self_supersession_is_not_also_reported_as_a_cycle(
    adopter_dir, write_unit, run_cli
):
    # A unit pointing at itself already has its own ERROR; a self-loop is a
    # cycle of one, and reporting both would say the same thing twice.
    write_unit("kb-0001.md", _unit("kb-0001", "kb-0001"))

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "supersedes itself" in result.stderr
    assert "cycle" not in result.stderr


def test_two_separate_cycles_are_both_reported(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", _unit("kb-0001", "kb-0002"))
    write_unit("kb-0002.md", _unit("kb-0002", "kb-0001"))
    write_unit("kb-0003.md", _unit("kb-0003", "kb-0004"))
    write_unit("kb-0004.md", _unit("kb-0004", "kb-0003"))

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert result.stderr.count("supersession cycle") == 2
