"""End-to-end tests for `validate` against a declared extension.

An adopter extends the base contract without forking it: a configuration file
at the project root points at a versioned schema, and the schema declares the
adopter's own fields with closed domains.
"""

import pytest

CONFIG = """\
extension:
  schema: knowledge-extension.md
  version: "1"
"""

SCHEMA = """\
fields:
  - name: domain
    type: enum
    values:
      - network
      - storage
  - name: owner
    type: string
"""

EXTENDED_UNIT = """\
id: kb-0001
evidence: measured
anchors: []
domain: network
owner: platform-team
"""


def test_a_unit_carrying_declared_extension_fields_passes(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "1 unit(s) checked" in result.stdout


def test_a_value_outside_the_declared_domain_gates_naming_unit_and_field(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors: []\ndomain: telepathy\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: domain: " in result.stderr
    assert "telepathy" in result.stderr
    assert "network, storage" in result.stderr


def test_a_field_the_schema_does_not_declare_gates_naming_unit_and_field(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors: []\nseverity: high\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    finding = _finding_for(result.stderr, "knowledge/kb-0001.md", "severity")
    # With an extension configured, the message must point at it: the adopter
    # declares the field there, not in the base contract.
    assert "extension" in finding, finding


def test_a_malformed_schema_stops_validation_with_an_explicit_error(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", "fields:\n\t- name: domain\n")
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR" in result.stderr
    assert "knowledge-extension.md" in result.stderr
    # Fail-loud: a schema that cannot be read is never downgraded to
    # base-contract-only validation, so no unit is reported as checked.
    assert "0 unit(s) checked" in result.stdout


def test_without_a_config_only_the_base_contract_applies(
    adopter_dir, write_unit, run_cli
):
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "1 unit(s) checked" in result.stdout
    finding = _finding_for(result.stderr, "knowledge/kb-0001.md", "domain")
    assert "extension" not in finding, finding


def test_a_string_field_holding_a_collection_gates(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit(
        "kb-0001.md",
        "id: kb-0001\nevidence: measured\nanchors: []\n"
        "owner:\n  - platform-team\n  - network-team\n",
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: owner: " in result.stderr


def test_a_declared_field_holding_an_empty_value_gates(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit(
        "kb-0001.md",
        'id: kb-0001\nevidence: measured\nanchors: []\nowner: ""\n',
    )

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: knowledge/kb-0001.md: owner: " in result.stderr


def test_a_config_without_an_extension_block_applies_the_base_contract(
    adopter_dir, write_document, write_unit, run_cli
):
    # `extension` is one adopter surface among several, not the price of
    # having a configuration file at all.
    write_document(
        "validated-memory.md",
        "id_prefix: kb-\nprobes:\n  git_ref: run-git-ref-probe\n",
    )
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "1 unit(s) checked" in result.stdout


def test_a_config_with_every_adopter_key_loads(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document(
        "validated-memory.md",
        CONFIG + "id_prefix: kb-\nprobes:\n  git_ref: run-git-ref-probe\n",
    )
    write_document("knowledge-extension.md", SCHEMA)
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


def test_a_probe_kind_with_whitespace_cannot_even_be_written(
    adopter_dir, write_document, write_unit, run_cli
):
    # A kind is a frontmatter key, and the parser rejects keys with spaces:
    # the "no whitespace in a probe kind" rule needs no separate check here.
    write_document("validated-memory.md", "probes:\n  git ref: run-probe\n")
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: validated-memory.md:" in result.stderr
    assert "frontmatter" in result.stderr


def test_an_empty_probes_mapping_is_valid(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", "probes: {}\n")
    write_unit("kb-0001.md", "id: kb-0001\nevidence: measured\nanchors: []\n")

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


# --- fail-loud loading: the configuration itself ------------------------------

MALFORMED_CONFIGS = [
    ("schema_missing", 'extension:\n  version: "1"\n'),
    ("version_missing", "extension:\n  schema: knowledge-extension.md\n"),
    ("extension_not_a_mapping", "extension: knowledge-extension.md\n"),
    ("unknown_config_key", "knowledge: knowledge\n"),
    (
        "unknown_extension_key",
        'extension:\n  schema: knowledge-extension.md\n  version: "1"\n  strict: yes\n',
    ),
    ("id_prefix_empty", 'id_prefix: ""\n'),
    ("id_prefix_not_a_scalar", "id_prefix:\n  - kb\n"),
    ("probes_not_a_mapping", "probes: git_ref\n"),
    ("probe_command_empty", 'probes:\n  git_ref: ""\n'),
]


@pytest.mark.parametrize(
    "name,config", MALFORMED_CONFIGS, ids=[case[0] for case in MALFORMED_CONFIGS]
)
def test_a_malformed_config_stops_validation_naming_the_config(
    name, config, adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", config)
    write_document("knowledge-extension.md", SCHEMA)
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1, result.stdout
    assert "ERROR: validated-memory.md: " in result.stderr
    assert "0 unit(s) checked" in result.stdout


def test_a_schema_the_config_points_at_but_does_not_exist_stops_validation(
    adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR" in result.stderr
    assert "knowledge-extension.md" in result.stderr
    assert "0 unit(s) checked" in result.stdout


# --- fail-loud loading: the schema --------------------------------------------

MALFORMED_SCHEMAS = [
    ("fields_missing", "title: adopter fields\n"),
    ("fields_not_a_list", "fields:\n  name: domain\n"),
    ("field_not_a_mapping", "fields:\n  - domain\n"),
    ("name_missing", "fields:\n  - type: string\n"),
    ("type_missing", "fields:\n  - name: domain\n"),
    ("unknown_type", "fields:\n  - name: domain\n    type: colour\n"),
    ("unknown_field_key", "fields:\n  - name: domain\n    type: string\n    rank: 1\n"),
    ("enum_without_values", "fields:\n  - name: domain\n    type: enum\n"),
    (
        "enum_with_empty_values",
        "fields:\n  - name: domain\n    type: enum\n    values: []\n",
    ),
    (
        "values_on_a_non_enum_type",
        "fields:\n  - name: domain\n    type: string\n    values:\n      - network\n",
    ),
    (
        "duplicate_field_name",
        "fields:\n  - name: domain\n    type: string\n  - name: domain\n    type: string\n",
    ),
    ("redeclares_a_base_contract_field", "fields:\n  - name: evidence\n    type: string\n"),
]


@pytest.mark.parametrize(
    "name,schema", MALFORMED_SCHEMAS, ids=[case[0] for case in MALFORMED_SCHEMAS]
)
def test_a_malformed_schema_stops_validation_naming_the_schema(
    name, schema, adopter_dir, write_document, write_unit, run_cli
):
    write_document("validated-memory.md", CONFIG)
    write_document("knowledge-extension.md", schema)
    write_unit("kb-0001.md", EXTENDED_UNIT)

    result = run_cli("validate", cwd=adopter_dir)

    assert result.returncode == 1, result.stdout
    assert "ERROR: knowledge-extension.md: " in result.stderr
    assert "0 unit(s) checked" in result.stdout


def _finding_for(stderr, location, field):
    prefix = f"ERROR: {location}: {field}: "
    for line in stderr.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"no finding for '{field}' in:\n{stderr}")
