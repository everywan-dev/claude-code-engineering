"""End-to-end tests for adopting a harness memory directory that already exists.

`init --harness-memory PATH` normally leaves a real (non-symlink) PATH alone.
The exception these tests cover: when PATH is recognizably the harness's own
agent memory -- Markdown files carrying the memory frontmatter -- `init`
absorbs it into this project's `memory/`, parks the original alongside as a
`.bak`, and only then creates the symlink. Nothing is ever deleted or
overwritten, and `lint` must pass clean on the merged result.
"""

MEMORY_FRONTMATTER = (
    "name: {name}\ndescription: {description}\nmetadata:\n  type: user\n"
)


def write_native(directory, name, description="A fact.", body="Memory body.\n"):
    """Write a harness-shaped memory file into `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.md"
    path.write_text(
        "---\n"
        + MEMORY_FRONTMATTER.format(name=name, description=description)
        + "---\n\n"
        + body,
        encoding="utf-8",
    )
    return path


def write_native_index(directory, *entries):
    """Write a harness-shaped `MEMORY.md` index into `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "MEMORY.md"
    path.write_text(
        "# Agent memory\n\n" + "".join(f"{entry}\n" for entry in entries),
        encoding="utf-8",
    )
    return path


# --- the happy path: absorb, park, link ---------------------------------------


def test_a_native_memory_directory_is_absorbed_parked_and_linked(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert native.is_symlink()
    assert native.resolve() == (adopter_dir / "memory").resolve()
    assert (adopter_dir / "memory" / "coffee-preference.md").is_file()
    parked = tmp_path / "harness" / "memory.bak"
    assert parked.is_dir() and not parked.is_symlink()
    assert (parked / "coffee-preference.md").is_file()


def test_lint_passes_clean_on_the_merged_memory(adopter_dir, tmp_path, run_cli):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    linted = run_cli("lint", cwd=adopter_dir)

    assert linted.returncode == 0, linted.stderr
    assert "ERROR" not in linted.stderr
    assert "WARNING" not in linted.stderr


def test_the_harness_index_line_is_carried_over_verbatim(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    entry = "- [Coffee preference](coffee-preference.md) — oat milk, no sugar"
    write_native_index(native, entry)

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert entry in index
    # The placeholder `init` writes into a fresh index goes once it has entries.
    assert "No entries yet." not in index


def test_a_memory_the_harness_index_never_listed_gets_a_synthesized_entry(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native)  # an index with no entries at all

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    linted = run_cli("lint", cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "- [coffee-preference](coffee-preference.md) — Prefers oat milk." in index
    assert linted.returncode == 0, linted.stderr


def test_a_memory_in_a_subdirectory_is_adopted_with_its_path(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native / "archive", "old-fact", "Something from before.")
    write_native_index(native, "- [Old fact](archive/old-fact.md) — from before")

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    linted = run_cli("lint", cwd=adopter_dir)

    assert (adopter_dir / "memory" / "archive" / "old-fact.md").is_file()
    assert linted.returncode == 0, linted.stderr


def test_entries_are_appended_to_an_index_that_already_has_some(
    adopter_dir, tmp_path, run_cli, write_memory, write_index
):
    existing = "- [Deploy window](deploy-window.md) — Tuesdays only"
    write_memory(
        "deploy-window.md",
        "name: deploy-window\ndescription: Tuesdays only.\nmetadata:\n  type: project\n",
    )
    write_index(f"# Agent memory\n\n{existing}\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    adopted = "- [Coffee preference](coffee-preference.md) — oat milk"
    write_native_index(native, adopted)

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    linted = run_cli("lint", cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert existing in index
    assert adopted in index
    assert linted.returncode == 0, linted.stderr


def test_an_index_entry_already_there_is_not_duplicated_by_absorption(
    adopter_dir, tmp_path, run_cli, write_index
):
    # The project's index lists a file it does not have -- a stale entry -- and
    # the harness turns out to hold exactly that file. Absorbing it must reuse
    # the entry already there, not append a second one for the same file.
    stale = "- [Coffee preference](coffee-preference.md) — oat milk"
    write_index(f"# Agent memory\n\n{stale}\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, stale)

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert index.count("(coffee-preference.md)") == 1, index


def test_a_padded_href_still_carries_the_harness_line_over(
    adopter_dir, tmp_path, run_cli, write_index
):
    # The harness index pads the link target. The href is a key -- it is what
    # says which entry names which file -- so a reader that does not normalize
    # it fails to find the line and synthesizes one instead, silently losing
    # what a human wrote about the fact.
    write_index("# Agent memory\n\nNo entries yet.\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference]( coffee-preference.md ) — oat milk")

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "— oat milk" in index, index


def test_an_index_entry_written_with_a_path_alias_is_not_duplicated(
    adopter_dir, tmp_path, run_cli, write_index
):
    # './coffee-preference.md' and 'coffee-preference.md' name the same file.
    # Comparing the hrefs as raw strings makes them look like two entries and
    # appends a second one; reconciling has to normalize the path the way the
    # index/file cross-check already does.
    write_index("# Agent memory\n\n- [Coffee](./coffee-preference.md) — oat milk\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert index.count("coffee-preference.md)") == 1, index


def test_a_malformed_entry_does_not_keep_the_placeholder_alive(
    adopter_dir, tmp_path, run_cli, write_index
):
    # A bullet whose link target is blank is not an entry naming a file, so an
    # index holding only that one is still an index with no entries: the
    # placeholder must go when real entries arrive.
    write_index("# Agent memory\n\nNo entries yet.\n- [Malformed](   )\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")

    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    index = (adopter_dir / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "No entries yet." not in index, index


# --- collisions: the project's own copy always wins ---------------------------


def test_a_conflicting_file_is_kept_warned_about_and_preserved_in_the_bak(
    adopter_dir, tmp_path, run_cli, write_memory, write_index
):
    write_memory(
        "coffee-preference.md",
        "name: coffee-preference\ndescription: Prefers black coffee.\n"
        "metadata:\n  type: user\n",
    )
    write_index("# Agent memory\n\n- [Coffee preference](coffee-preference.md) — black\n")
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "coffee-preference.md" in result.stderr
    project_copy = (adopter_dir / "memory" / "coffee-preference.md").read_text(
        encoding="utf-8"
    )
    assert "Prefers black coffee." in project_copy
    parked = tmp_path / "harness" / "memory.bak" / "coffee-preference.md"
    assert "Prefers oat milk." in parked.read_text(encoding="utf-8")


def test_a_file_that_is_already_identical_is_absorbed_without_a_warning(
    adopter_dir, tmp_path, run_cli, write_index
):
    native = tmp_path / "harness" / "memory"
    source = write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")
    project_copy = adopter_dir / "memory" / "coffee-preference.md"
    project_copy.parent.mkdir(parents=True, exist_ok=True)
    project_copy.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    write_index("# Agent memory\n\n- [Coffee preference](coffee-preference.md) — oat milk\n")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr


# --- parking never overwrites --------------------------------------------------


def test_parking_picks_the_next_free_bak_slot(adopter_dir, tmp_path, run_cli):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    occupied = tmp_path / "harness" / "memory.bak"
    occupied.mkdir(parents=True)
    (occupied / "keep-me.txt").write_text("Do not touch.\n", encoding="utf-8")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (occupied / "keep-me.txt").read_text(encoding="utf-8") == "Do not touch.\n"
    assert (tmp_path / "harness" / "memory.bak.1" / "coffee-preference.md").is_file()


# --- what does not qualify is still left alone --------------------------------


def test_a_directory_holding_a_non_markdown_file_is_left_untouched(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    (native / "notes.txt").write_text("Not a memory.\n", encoding="utf-8")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "notes.txt" in result.stderr
    assert not native.is_symlink()
    assert (native / "coffee-preference.md").is_file()
    assert not (tmp_path / "harness" / "memory.bak").exists()


def test_a_non_markdown_file_is_left_untouched_even_when_it_looks_like_a_memory(
    adopter_dir, tmp_path, run_cli
):
    # Absorption only ever copies '.md' files, so a memory-shaped file under
    # any other suffix would be parked into the backup and never seen again.
    # Recognition has to reject the directory on the suffix alone, before its
    # contents are read.
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    (native / "stray.yaml").write_text(
        "---\n"
        + MEMORY_FRONTMATTER.format(name="stray", description="Looks like a memory.")
        + "---\n\nBody.\n",
        encoding="utf-8",
    )

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "stray.yaml" in result.stderr
    assert not native.is_symlink()
    assert (native / "stray.yaml").is_file()


def test_a_hidden_file_disqualifies_the_directory_like_any_other(
    adopter_dir, tmp_path, run_cli
):
    # Recognition counts hidden files too. A stray '.gitkeep' or '.DS_Store'
    # therefore blocks the merge until a human removes it -- strict by design,
    # and the WARNING names the file so the fix is obvious.
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    (native / ".gitkeep").write_text("", encoding="utf-8")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert ".gitkeep" in result.stderr
    assert not native.is_symlink()


def test_a_directory_holding_only_the_index_qualifies(adopter_dir, tmp_path, run_cli):
    # A harness index with no facts under it is still recognizably agent
    # memory: absorbing it is a no-op, but the path gets its symlink instead
    # of warning on every session start forever.
    native = tmp_path / "harness" / "memory"
    write_native_index(native)

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert native.is_symlink()
    assert (tmp_path / "harness" / "memory.bak" / "MEMORY.md").is_file()


def test_a_markdown_file_without_memory_frontmatter_is_left_untouched(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    (native / "readme.md").write_text("Just prose, no frontmatter.\n", encoding="utf-8")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "readme.md" in result.stderr
    assert not native.is_symlink()
    assert (native / "readme.md").is_file()


def test_a_directory_of_memories_with_no_index_still_qualifies(
    adopter_dir, tmp_path, run_cli
):
    # The harness's index may be absent; the memory files alone are enough to
    # recognize the directory, and their entries get synthesized.
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    linted = run_cli("lint", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert native.is_symlink()
    assert linted.returncode == 0, linted.stderr


# --- the empty directory: nothing to absorb, nothing to park ------------------


def test_an_empty_directory_is_replaced_by_the_symlink(adopter_dir, tmp_path, run_cli):
    native = tmp_path / "harness" / "memory"
    native.mkdir(parents=True)

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr
    assert native.is_symlink()
    assert native.resolve() == (adopter_dir / "memory").resolve()
    assert not (tmp_path / "harness" / "memory.bak").exists()


# --- idempotency ---------------------------------------------------------------


def test_re_running_after_absorption_keeps_the_symlink_and_absorbs_nothing(
    adopter_dir, tmp_path, run_cli
):
    native = tmp_path / "harness" / "memory"
    write_native(native, "coffee-preference", "Prefers oat milk.")
    write_native_index(native, "- [Coffee preference](coffee-preference.md) — oat milk")
    run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)
    index_after_first = (adopter_dir / "memory" / "MEMORY.md").read_text(
        encoding="utf-8"
    )

    result = run_cli("init", "--harness-memory", str(native), cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert "kept symlink" in result.stdout
    assert "adopted" not in result.stdout
    assert (adopter_dir / "memory" / "MEMORY.md").read_text(
        encoding="utf-8"
    ) == index_after_first
    assert not (tmp_path / "harness" / "memory.bak.1").exists()
