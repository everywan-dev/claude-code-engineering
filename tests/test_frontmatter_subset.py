"""End-to-end tests for the bounded YAML subset the frontmatter parser accepts.

Everything outside the subset is an ERROR reported against the unit: the
parser never guesses and never validates a document it did not fully
understand.
"""

import pytest

OUT_OF_SUBSET = [
    ("tab_indentation", "id: kb-0001\nevidence: measured\nanchors:\n\t- system: repo\n"),
    ("block_scalar", "id: kb-0001\nevidence: measured\nnote: |\n  multi\n  line\n"),
    ("folded_scalar", "id: kb-0001\nevidence: measured\nnote: >\n  folded\n"),
    ("yaml_anchor", "id: &base kb-0001\nevidence: measured\n"),
    ("yaml_alias", "id: kb-0001\nevidence: *base\n"),
    ("inline_list", "id: kb-0001\nevidence: measured\nsupersedes: [kb-0000]\n"),
    (
        "inline_mapping",
        "id: kb-0001\nevidence: measured\nanchors: {system: repo}\n",
    ),
    ("duplicate_key", "id: kb-0001\nid: kb-0002\nevidence: measured\n"),
    ("key_without_value", "id: kb-0001\nevidence: measured\nsupersedes:\n"),
    (
        "inconsistent_indentation",
        "id: kb-0001\nevidence: measured\nanchors:\n  - system: repo\n kind: git_ref\n",
    ),
    (
        "list_where_a_mapping_started",
        "id: kb-0001\nevidence: measured\n- stray\n",
    ),
    ("no_colon", "id: kb-0001\nevidence measured\n",),
    ("empty_frontmatter", ""),
]


@pytest.mark.parametrize(
    "name,frontmatter", OUT_OF_SUBSET, ids=[case[0] for case in OUT_OF_SUBSET]
)
def test_out_of_subset_frontmatter_gates(name, frontmatter, adopter_dir, write_unit, run_cli):
    write_unit(f"{name}.md", frontmatter)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1, result.stdout
    assert f"knowledge/{name}.md" in result.stderr
    assert "frontmatter" in result.stderr


def test_unterminated_frontmatter_gates(adopter_dir, run_cli):
    path = adopter_dir / "knowledge" / "unterminated.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nid: kb-0001\nevidence: measured\n", encoding="utf-8")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "unterminated frontmatter" in result.stderr


def test_a_parse_error_stops_the_unit_from_being_validated(
    adopter_dir, write_unit, run_cli
):
    # The unit is both unparseable and semantically wrong: only the parse
    # error is reported, because nothing may be validated on a best-effort read.
    write_unit("broken.md", "id: kb-0001\nevidence: probable\nnote: |\n  block\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "frontmatter" in result.stderr
    assert "evidence" not in result.stderr
    assert result.stderr.count("ERROR") == 1


def test_the_error_names_the_offending_line(adopter_dir, write_unit, run_cli):
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nnote: |\n  block\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    # Line 4 of the file: '---', 'id', 'evidence', 'note'.
    assert "knowledge/kb-0001.md:4:" in result.stderr


def test_comments_and_blank_lines_are_accepted(adopter_dir, write_unit, run_cli):
    write_unit(
        "kb-0001.md",
        "# leading comment\n"
        "id: kb-0001  # trailing comment\n"
        "\n"
        "evidence: measured\n"
        "anchors: []\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr


def test_quoted_scalars_are_accepted(adopter_dir, write_unit, run_cli):
    write_unit(
        "kb-0001.md",
        'id: "kb-0001"\n'
        "evidence: 'measured'\n"
        "anchors:\n"
        "  - system: \"adopter repo\"\n"
        "    kind: git_ref\n"
        "    captured_at: '2026-08-11T10:00:00Z'\n"
        "    payload:\n"
        "      ref: refs/heads/main\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


def test_an_apostrophe_inside_a_plain_scalar_is_not_a_quote(
    adopter_dir, write_unit, run_cli
):
    write_unit(
        "kb-0001.md",
        "id: kb-0001\n"
        "evidence: measured\n"
        "anchors:\n"
        "  - system: the adopter's repo\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-11\n"
        "    payload: {}\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
