"""End-to-end tests for `lint` against the agent-memory layer.

Fixtures are synthetic adopter trees: a `memory/` directory holding one
Markdown file per fact, each with frontmatter in the Claude Code harness
shape, plus a one-line-per-entry index at `memory/MEMORY.md`.
"""

HEALTHY_MEMORY = """\
name: coffee-preference
description: Prefers oat milk in coffee.
metadata:
  type: user
"""

HEALTHY_INDEX = """\
# Agent memory

- [Coffee preference](coffee-preference.md) — oat milk in coffee
"""


def test_healthy_memory_passes_clean(adopter_dir, write_memory, write_index, run_cli):
    write_memory("coffee-preference.md", HEALTHY_MEMORY)
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "WARNING" not in result.stderr
    assert "1 memory file(s) checked" in result.stdout


# --- index/file sync, in both directions --------------------------------------


def test_index_entry_without_a_matching_file_gates(adopter_dir, write_index, run_cli):
    write_index("- [Missing](missing.md) — a fact that was removed\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/MEMORY.md: entry: " in result.stderr
    assert "missing.md" in result.stderr


def test_a_memory_file_without_an_index_entry_gates(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("coffee-preference.md", HEALTHY_MEMORY)
    write_index("# Agent memory\n")  # no entries at all

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/coffee-preference.md: index: " in result.stderr
    assert "MEMORY.md" in result.stderr


# --- frontmatter completeness --------------------------------------------------

INVALID_FRONTMATTER = [
    (
        "name_missing",
        "description: Prefers oat milk in coffee.\nmetadata:\n  type: user\n",
        "name",
    ),
    (
        "description_missing",
        "name: coffee-preference\nmetadata:\n  type: user\n",
        "description",
    ),
    (
        "type_missing",
        "name: coffee-preference\ndescription: Prefers oat milk.\nmetadata: {}\n",
        "metadata.type",
    ),
    (
        "metadata_missing",
        "name: coffee-preference\ndescription: Prefers oat milk.\n",
        "metadata.type",
    ),
    (
        "type_out_of_domain",
        (
            "name: coffee-preference\ndescription: Prefers oat milk.\n"
            "metadata:\n  type: opinion\n"
        ),
        "metadata.type",
    ),
]


def test_every_incomplete_frontmatter_gates_naming_file_and_field(
    adopter_dir, write_memory, write_index, run_cli
):
    entries = []
    for name, frontmatter, _field in INVALID_FRONTMATTER:
        write_memory(f"{name}.md", frontmatter)
        entries.append(f"- [{name}]({name}.md) — fixture entry")
    write_index("\n".join(entries) + "\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    for name, _frontmatter, field in INVALID_FRONTMATTER:
        expected = f"ERROR: memory/{name}.md: {field}: "
        assert expected in result.stderr, (
            f"{name}: missing finding for field '{field}'\n{result.stderr}"
        )


def test_malformed_frontmatter_gates_naming_the_line(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("broken.md", "name: coffee-preference\ndescription: |\n  block\n")
    write_index("- [Broken](broken.md) — fixture entry\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "frontmatter" in result.stderr
    # A parse error is the only finding for a file: nothing is validated on a
    # best-effort basis once the frontmatter itself could not be parsed.
    assert "name" not in result.stderr.split("frontmatter")[0]
    assert "memory/broken.md:3:" in result.stderr


# --- duplicate name --------------------------------------------------------


def test_duplicate_name_gates_naming_both_files(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("first.md", HEALTHY_MEMORY)
    write_memory("second.md", HEALTHY_MEMORY)
    write_index(
        "- [First](first.md) — fixture entry\n- [Second](second.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "duplicate name 'coffee-preference'" in result.stderr
    assert "memory/first.md" in result.stderr
    assert "memory/second.md" in result.stderr
    # A duplicate `name` implies at least one divergence: two files in one
    # directory cannot share a filename, so both are reported diverging too.
    assert result.stderr.count("does not match the filename") == 2


# --- wikilinks -------------------------------------------------------------


def test_a_broken_wikilink_in_description_warns_without_gating(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md",
        "name: coffee-preference\n"
        "description: See also [[tea-preference]].\n"
        "metadata:\n  type: user\n",
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/coffee-preference.md: description: " in result.stderr
    assert "tea-preference" in result.stderr
    assert "1 warning(s)" in result.stdout


def test_a_broken_wikilink_in_the_body_warns_without_gating(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md", HEALTHY_MEMORY, body="Related: [[tea-preference]].\n"
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/coffee-preference.md: body: " in result.stderr
    assert "tea-preference" in result.stderr


def test_a_repeated_broken_wikilink_warns_once_per_field(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md",
        HEALTHY_MEMORY,
        body="See [[tea-preference]] and again [[tea-preference]].\n",
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert result.stderr.count("tea-preference") == 1


def test_a_wikilink_resolving_to_a_real_memory_is_not_a_finding(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md",
        HEALTHY_MEMORY,
        body="Related: [[tea-preference]].\n",
    )
    write_memory(
        "tea-preference.md",
        "name: tea-preference\ndescription: Prefers green tea.\nmetadata:\n  type: user\n",
    )
    write_index(
        HEALTHY_INDEX + "- [Tea preference](tea-preference.md) — green tea\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr


# --- filename identity (ADR 0001) --------------------------------------------

# The filename without `.md` is a memory's canonical identity; `name` is the
# identifier wikilinks resolve against, and gives way to the filename when the
# two disagree. Resolution itself is unchanged -- still by `name`.

DIVERGING_MEMORY = """\
name: Coffee Preference
description: Prefers oat milk in coffee.
metadata:
  type: user
"""


def test_a_name_diverging_from_its_filename_warns_without_gating(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("coffee-preference.md", DIVERGING_MEMORY)
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "WARNING: memory/coffee-preference.md: name: " in result.stderr
    assert "1 warning(s)" in result.stdout


def test_the_divergence_warning_names_both_sides_and_the_repair(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("coffee-preference.md", DIVERGING_MEMORY)
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert "'Coffee Preference'" in result.stderr
    assert "'coffee-preference'" in result.stderr
    # The message states which side is canonical and which one gets repaired,
    # so the reader never has to guess the direction of the fix.
    assert "canonical" in result.stderr
    assert "repair 'name'" in result.stderr


def test_a_name_matching_its_filename_is_not_a_finding(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("coffee-preference.md", HEALTHY_MEMORY)
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr


def test_a_memory_in_a_subdirectory_is_compared_by_its_filename(
    adopter_dir, write_memory, write_index, run_cli
):
    # The comparison is against the filename alone, never the path the file
    # sits at: a memory in a subdirectory whose `name` matches is clean.
    write_memory("personal/coffee-preference.md", HEALTHY_MEMORY)
    write_index("- [Coffee](personal/coffee-preference.md) — oat milk\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr


def test_an_incomplete_name_is_not_also_reported_as_diverging(
    adopter_dir, write_memory, write_index, run_cli
):
    # A missing or empty `name` already gates on its own rule; piling the
    # divergence warning on top would report the same defect twice.
    write_memory(
        "coffee-preference.md",
        "description: Prefers oat milk in coffee.\nmetadata:\n  type: user\n",
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/coffee-preference.md: name: " in result.stderr
    assert "0 warning(s)" in result.stdout


def test_a_wikilink_to_a_diverging_file_names_the_cause(
    adopter_dir, write_memory, write_index, run_cli
):
    # Without the hint this reads as "not written yet" about a file that is
    # right there -- the wikilink is fine, the target's `name` is not.
    write_memory("coffee-preference.md", DIVERGING_MEMORY)
    write_memory(
        "notes.md",
        "name: notes\ndescription: Scratch notes.\nmetadata:\n  type: project\n",
        body="Related: [[coffee-preference]].\n",
    )
    write_index(
        HEALTHY_INDEX + "- [Notes](notes.md) — scratch notes\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/notes.md: body: " in result.stderr
    assert "coffee-preference.md" in result.stderr
    assert "declares name 'Coffee Preference'" in result.stderr
    assert "not written yet" not in result.stderr


def test_a_wikilink_with_no_file_behind_it_keeps_the_generic_message(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md", HEALTHY_MEMORY, body="Related: [[tea-preference]].\n"
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "not written yet" in result.stderr
    assert "declares name" not in result.stderr


def test_an_ambiguous_filename_keeps_the_generic_wikilink_message(
    adopter_dir, write_memory, write_index, run_cli
):
    # Two files in different subdirectories share a filename, so naming one of
    # them as the cause would be a guess. The generic message stands.
    write_memory(
        "alpha/shared.md",
        "name: alpha-fact\ndescription: One fact.\nmetadata:\n  type: project\n",
    )
    write_memory(
        "beta/shared.md",
        "name: beta-fact\ndescription: Another fact.\nmetadata:\n  type: project\n",
    )
    write_memory(
        "notes.md",
        "name: notes\ndescription: Scratch notes.\nmetadata:\n  type: project\n",
        body="Related: [[shared]].\n",
    )
    write_index(
        "- [Alpha](alpha/shared.md) — one fact\n"
        "- [Beta](beta/shared.md) — another fact\n"
        "- [Notes](notes.md) — scratch notes\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/notes.md: body: " in result.stderr
    assert "not written yet" in result.stderr
    assert "declares name" not in result.stderr


# --- supersession convention ------------------------------------------------


def test_a_well_formed_supersession_is_recognized_without_findings(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_memory("coffee-preference.md", HEALTHY_MEMORY)
    write_index(
        "- [Old](old-coffee-preference.md) — fixture entry\n"
        "- [New](coffee-preference.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "WARNING" not in result.stderr


def test_a_malformed_supersession_marker_gates(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by coffee-preference\n"
        "metadata:\n  type: user\n",
    )
    write_index("- [Old](old-coffee-preference.md) — fixture entry\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/old-coffee-preference.md: description: " in result.stderr
    assert "supersession" in result.stderr


def test_a_supersession_pointing_at_a_missing_memory_gates(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_index("- [Old](old-coffee-preference.md) — fixture entry\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/old-coffee-preference.md: description: " in result.stderr
    assert "coffee-preference" in result.stderr
    assert "WARNING" not in result.stderr


def test_a_supersession_pointing_at_itself_gates(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by [[old-coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_index("- [Old](old-coffee-preference.md) — fixture entry\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/old-coffee-preference.md: description: " in result.stderr
    assert "itself" in result.stderr


def test_a_supersession_pointing_at_a_diverging_file_names_the_cause(
    adopter_dir, write_memory, write_index, run_cli
):
    # Same defect the wikilink warning names, but here it gates: the successor
    # a memory is retired onto cannot be left pending, so the ERROR has to
    # point at the repair rather than claim the memory does not exist.
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_memory("coffee-preference.md", DIVERGING_MEMORY)
    write_index(
        "- [Old](old-coffee-preference.md) — fixture entry\n"
        "- [New](coffee-preference.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/old-coffee-preference.md: description: " in result.stderr
    assert "does not resolve by name" in result.stderr
    assert "declares name 'Coffee Preference'" in result.stderr
    assert "which does not exist" not in result.stderr


def test_a_supersession_pointing_at_its_own_filename_is_itself(
    adopter_dir, write_memory, write_index, run_cli
):
    # The memory's canonical identity is its filename, so superseding that
    # name is superseding itself -- whatever `name` currently says.
    write_memory(
        "coffee-preference.md",
        "name: Coffee Preference\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/coffee-preference.md: description: " in result.stderr
    assert "itself" in result.stderr


def test_a_supersession_resolving_by_name_is_not_read_as_itself(
    adopter_dir, write_memory, write_index, run_cli
):
    # The superseding file's own filename happens to equal the `name` another
    # memory declares. The target resolves to that other memory, so this is a
    # valid supersession -- not a memory pointing at itself.
    write_memory(
        "coffee-preference.md",
        "name: old-note\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_memory(
        "newer.md",
        "name: coffee-preference\n"
        "description: Prefers oat milk in coffee.\n"
        "metadata:\n  type: user\n",
    )
    write_index(
        "- [Old](coffee-preference.md) — fixture entry\n"
        "- [New](newer.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "itself" not in result.stderr
    assert "supersession" not in result.stderr
    # Both files still diverge from their filenames; that is the only finding.
    assert "2 warning(s)" in result.stdout


def test_an_unparseable_sibling_still_makes_a_filename_ambiguous(
    adopter_dir, write_memory, write_index, run_cli
):
    # Two files share a filename but only one parses. The hint must still be
    # withheld: the parsed one is not known to be the memory that was meant.
    write_memory(
        "alpha/shared.md",
        "name: alpha-fact\ndescription: |\n  block\n",
    )
    write_memory(
        "beta/shared.md",
        "name: beta-fact\ndescription: Another fact.\nmetadata:\n  type: project\n",
    )
    write_memory(
        "notes.md",
        "name: notes\ndescription: Scratch notes.\nmetadata:\n  type: project\n",
        body="Related: [[shared]].\n",
    )
    write_index(
        "- [Alpha](alpha/shared.md) — one fact\n"
        "- [Beta](beta/shared.md) — another fact\n"
        "- [Notes](notes.md) — scratch notes\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert "WARNING: memory/notes.md: body: " in result.stderr
    assert "not written yet" in result.stderr
    assert "declares name" not in result.stderr


def test_a_file_named_only_md_carries_no_identity(
    adopter_dir, write_memory, write_index, run_cli
):
    # Removing the '.md' suffix leaves nothing, so there is no identity for
    # `name` to match -- and the repair is the one the rule otherwise forbids:
    # rename the file, because it has no name to begin with.
    write_memory(".md", HEALTHY_MEMORY)
    write_index("- [Nameless](.md) — no identity\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/.md: name: " in result.stderr
    assert "no identity" in result.stderr


def test_an_empty_name_is_not_also_reported_as_diverging(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md",
        "name: ''\ndescription: Prefers oat milk.\nmetadata:\n  type: user\n",
    )
    write_index(HEALTHY_INDEX)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "ERROR: memory/coffee-preference.md: name: " in result.stderr
    assert "0 warning(s)" in result.stdout


def test_a_supersession_resolving_onto_a_diverging_successor_is_valid(
    adopter_dir, write_memory, write_index, run_cli
):
    # The successor resolves by `name` while its own file is named something
    # else. That is a valid supersession plus a divergence to repair -- not a
    # broken successor.
    write_memory(
        "old-coffee-preference.md",
        "name: old-coffee-preference\n"
        "description: superseded by [[coffee-preference]]\n"
        "metadata:\n  type: user\n",
    )
    write_memory(
        "newer.md",
        "name: coffee-preference\n"
        "description: Prefers oat milk in coffee.\n"
        "metadata:\n  type: user\n",
    )
    write_index(
        "- [Old](old-coffee-preference.md) — fixture entry\n"
        "- [New](newer.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "supersession" not in result.stderr
    assert "1 warning(s)" in result.stdout


def test_two_memories_sharing_a_filename_are_reported(
    adopter_dir, write_memory, write_index, run_cli
):
    # The filename is the canonical identity, so two files carrying the same
    # one are two memories claiming the same identity. Without this, `lint`
    # tells both to repair `name` towards the same value, and following that
    # advice lands on the duplicate-name ERROR with no warning it was coming.
    write_memory(
        "alpha/shared.md",
        "name: alpha-fact\ndescription: One fact.\nmetadata:\n  type: project\n",
    )
    write_memory(
        "beta/shared.md",
        "name: beta-fact\ndescription: Another fact.\nmetadata:\n  type: project\n",
    )
    write_index(
        "- [Alpha](alpha/shared.md) — one fact\n"
        "- [Beta](beta/shared.md) — another fact\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING: memory/beta/shared.md: filename: " in result.stderr
    assert "'shared'" in result.stderr
    assert "memory/alpha/shared.md" in result.stderr


def test_a_shared_filename_is_reported_even_when_one_file_does_not_parse(
    adopter_dir, write_memory, write_index, run_cli
):
    # The collision is a fact about the files, not about their frontmatter.
    write_memory("alpha/shared.md", "name: alpha-fact\ndescription: |\n  block\n")
    write_memory(
        "beta/shared.md",
        "name: beta-fact\ndescription: Another fact.\nmetadata:\n  type: project\n",
    )
    write_index(
        "- [Alpha](alpha/shared.md) — one fact\n"
        "- [Beta](beta/shared.md) — another fact\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert "WARNING: memory/beta/shared.md: filename: " in result.stderr


def test_distinct_filenames_across_subdirectories_are_not_a_collision(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "alpha/alpha-fact.md",
        "name: alpha-fact\ndescription: One fact.\nmetadata:\n  type: project\n",
    )
    write_memory(
        "beta/beta-fact.md",
        "name: beta-fact\ndescription: Another fact.\nmetadata:\n  type: project\n",
    )
    write_index(
        "- [Alpha](alpha/alpha-fact.md) — one fact\n"
        "- [Beta](beta/beta-fact.md) — another fact\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr


# --- target resolution -------------------------------------------------------


def test_a_missing_default_directory_gates_and_points_at_init(adopter_dir, run_cli):
    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "memory" in result.stderr
    assert "init" in result.stderr


def test_a_missing_explicit_path_gates(adopter_dir, run_cli):
    result = run_cli("lint", "nowhere", cwd=adopter_dir)

    assert result.returncode == 1
    assert "nowhere" in result.stderr
    assert "no such file or directory" in result.stderr


def test_a_missing_index_gates_and_points_at_init(
    adopter_dir, write_memory, run_cli
):
    write_memory("coffee-preference.md", HEALTHY_MEMORY)

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "MEMORY.md" in result.stderr
    assert "init" in result.stderr
    assert "0 memory file(s) checked" in result.stdout


def test_an_empty_memory_directory_with_an_empty_index_is_clean(
    adopter_dir, write_index, run_cli
):
    write_index("# Agent memory\n\nNo entries yet.\n")

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "WARNING" not in result.stderr
    assert "0 memory file(s) checked" in result.stdout


def test_explicit_path_overrides_the_default_directory(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory("coffee-preference.md", HEALTHY_MEMORY)
    write_index(HEALTHY_INDEX)
    (adopter_dir / "memory").rename(adopter_dir / "facts")

    result = run_cli("lint", "facts", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr


# --- ERROR and WARNING are reported apart -------------------------------------


def test_errors_and_warnings_are_reported_apart(
    adopter_dir, write_memory, write_index, run_cli
):
    write_memory(
        "coffee-preference.md",
        "name: coffee-preference\n"
        "description: See also [[tea-preference]].\n"
        "metadata:\n  type: user\n",
    )
    write_memory("broken.md", "name: broken\nmetadata:\n  type: user\n")
    write_index(
        "- [Warned](coffee-preference.md) — fixture entry\n"
        "- [Failed](broken.md) — fixture entry\n"
    )

    result = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 1
    assert "1 error(s)" in result.stdout
    assert "1 warning(s)" in result.stdout
