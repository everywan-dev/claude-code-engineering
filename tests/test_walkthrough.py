"""End-to-end test for the documented walkthrough (`docs/walkthrough.md`).

This test runs the exact command sequence the walkthrough documents -- init,
create a unit, validate, derive, probe, supersede, derive again -- over a
fixture adopter tree, including a fixture git repository for the bundled
`git_ref` probe, exactly as `init` registers it. If this test and the doc
ever diverge, the test wins and the doc is corrected to match (see this
repo's CLAUDE.md, "TDD where there is behavior").

Fixture git repository handling mirrors `tests/test_git_ref_probe.py`,
duplicated locally (not imported) so each test file stays self-contained,
consistent with the rest of this suite.
"""

import json
import os
import subprocess

_GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "walkthrough",
    "GIT_AUTHOR_EMAIL": "walkthrough@test",
    "GIT_COMMITTER_NAME": "walkthrough",
    "GIT_COMMITTER_EMAIL": "walkthrough@test",
}


def _git(repo_dir, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        env={**os.environ, **_GIT_IDENTITY_ENV},
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _init_fixture_repo(repo_dir):
    """Create a one-commit git repo on branch `main` and return its HEAD sha."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "init", "-q", "-b", "main")
    (repo_dir / "file.txt").write_text("hello\n", encoding="utf-8")
    _git(repo_dir, "add", "file.txt")
    _git(repo_dir, "commit", "-q", "-m", "first commit")
    return _git(repo_dir, "rev-parse", "HEAD").strip()


def _verdict_records(adopter_dir):
    path = adopter_dir / "verdicts.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_the_documented_walkthrough_reproduces_end_to_end(
    adopter_dir, write_unit, run_cli
):
    # --- 1. init: adopt the layout ------------------------------------------
    init_result = run_cli("init", cwd=adopter_dir)
    assert init_result.returncode == 0, init_result.stderr
    assert "init: 5 created, 0 kept, 0 error(s), 0 warning(s)" in init_result.stdout
    # `init` already registers the bundled `git_ref` probe: no extra
    # configuration step is needed before the unit below can be probed.
    config = (adopter_dir / "validated-memory.md").read_text(encoding="utf-8")
    assert "git_ref: python3 -m validated_memory.probes.git_ref" in config

    # --- 2. create a knowledge unit, anchored to a fixture git repo ---------
    sha = _init_fixture_repo(adopter_dir / "repo")
    write_unit(
        "kb-0001.md",
        "id: kb-0001\n"
        "evidence: measured\n"
        "anchors:\n"
        "  - system: sample-repo\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-12T00:00:00Z\n"
        "    payload:\n"
        "      repo: repo\n"
        "      ref: refs/heads/main\n"
        f"      commit: {sha}\n",
        body="The sample repository's default branch is at this commit.\n",
    )

    # --- 3. validate ----------------------------------------------------------
    validate_result = run_cli("validate", cwd=adopter_dir)
    assert validate_result.returncode == 0, validate_result.stderr
    assert validate_result.stderr == ""
    assert (
        "validate: 1 unit(s) checked, 0 error(s), 0 warning(s)"
        in validate_result.stdout
    )

    # --- 4. derive (before probing: the anchor was never checked) -----------
    derive_result = run_cli("derive", cwd=adopter_dir)
    assert derive_result.returncode == 0, derive_result.stderr
    assert derive_result.stderr == ""
    assert "derive: 1 unit(s) indexed" in derive_result.stdout
    index = (adopter_dir / "knowledge-index.md").read_text(encoding="utf-8")
    # Never probed yet: the verdict cell names the system behind the unknown.
    assert "| kb-0001 | active | measured | unknown (sample-repo) |" in index

    # --- 5. probe ---------------------------------------------------------------
    probe_result = run_cli("probe", cwd=adopter_dir)
    assert probe_result.returncode == 0, probe_result.stderr
    assert probe_result.stderr == ""
    assert (
        "probe: 1 anchor(s) probed across 1 unit(s): 1 current, 0 drifted, 0 unknown"
        in probe_result.stdout
    )
    records = _verdict_records(adopter_dir)
    assert records[-1]["unit"] == "kb-0001"
    assert records[-1]["verdict"] == "current"

    # --- 6. supersede: a new unit, the old one untouched ------------------------
    write_unit(
        "kb-0002.md",
        "id: kb-0002\n"
        "evidence: verifiable\n"
        "supersedes:\n"
        "  - kb-0001\n"
        "anchors:\n"
        "  - system: sample-repo\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-12T00:05:00Z\n"
        "    payload:\n"
        "      repo: repo\n"
        "      ref: refs/heads/main\n"
        f"      commit: {sha}\n",
        body="Re-checked and confirmed: same commit, upgraded to verifiable.\n",
    )
    kb_0001_before = (adopter_dir / "knowledge" / "kb-0001.md").read_text(
        encoding="utf-8"
    )

    # --- 7. derive again: both units, verdict history preserved -----------------
    final_derive = run_cli("derive", cwd=adopter_dir)
    assert final_derive.returncode == 0, final_derive.stderr
    assert final_derive.stderr == ""
    assert "derive: 2 unit(s) indexed" in final_derive.stdout
    final_index = (adopter_dir / "knowledge-index.md").read_text(encoding="utf-8")
    # kb-0001 is now superseded, but keeps the "current" verdict already
    # recorded for it: derive never mutates a unit, and never re-probes.
    assert "| kb-0001 | superseded by kb-0002 | measured | current |" in final_index
    # kb-0002 is active, with its own, not-yet-probed anchor.
    assert "| kb-0002 | active | verifiable | unknown (sample-repo) |" in final_index
    # Superseding kb-0001 never touched its file.
    assert (
        adopter_dir / "knowledge" / "kb-0001.md"
    ).read_text(encoding="utf-8") == kb_0001_before
