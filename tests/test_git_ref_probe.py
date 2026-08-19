"""End-to-end tests for the bundled `git_ref` probe.

Two seams, both outside the package's internals:

- The probe module's own stdin/stdout contract, invoked directly as
  `python3 -m validated_memory.probes.git_ref` -- exactly the command `init`
  registers for it -- to pin the contract in isolation from the rest of the
  framework.
- The `probe` subcommand dispatching to it through the adopter's registry in
  `validated-memory.md`, exactly like an adopter-written probe (AC4), with
  `derive` afterwards reading back the verdicts it recorded (AC5).

Fixture git repositories are built with `git` subprocess calls, with an
explicit committer/author identity via env vars so the tests never depend on
global git configuration.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "probe",
    "GIT_AUTHOR_EMAIL": "probe@test",
    "GIT_COMMITTER_NAME": "probe",
    "GIT_COMMITTER_EMAIL": "probe@test",
}

# Exactly the command `init` registers in `validated-memory.md` for `git_ref`
# (see `init.CONFIG`): registering anything else here would test a different
# mechanism than the one an adopter actually gets.
GIT_REF_COMMAND = "python3 -m validated_memory.probes.git_ref"


def _git(repo_dir, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        env={**os.environ, **_GIT_IDENTITY_ENV},
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _init_repo(repo_dir):
    """Create a one-commit git repo on branch `main` and return its HEAD sha."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "init", "-q", "-b", "main")
    (repo_dir / "file.txt").write_text("hello\n", encoding="utf-8")
    _git(repo_dir, "add", "file.txt")
    _git(repo_dir, "commit", "-q", "-m", "first commit")
    return _git(repo_dir, "rev-parse", "HEAD").strip()


def _advance_repo(repo_dir):
    """Add a second commit to `repo_dir` and return the new HEAD sha."""
    (repo_dir / "file2.txt").write_text("world\n", encoding="utf-8")
    _git(repo_dir, "add", "file2.txt")
    _git(repo_dir, "commit", "-q", "-m", "second commit")
    return _git(repo_dir, "rev-parse", "HEAD").strip()


@pytest.fixture
def run_probe_module():
    """Invoke `python3 -m validated_memory.probes.git_ref` with `envelope` on stdin."""

    def _run(envelope, env=None):
        run_env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        if env is not None:
            run_env = {**run_env, **env}
        stdin = envelope if isinstance(envelope, str) else json.dumps(envelope)
        return subprocess.run(
            [sys.executable, "-m", "validated_memory.probes.git_ref"],
            input=stdin,
            capture_output=True,
            text=True,
            env=run_env,
            check=False,
        )

    return _run


def _envelope(repo, ref, commit):
    return {
        "system": "repo-a",
        "kind": "git_ref",
        "captured_at": "2026-08-01T00:00:00Z",
        "payload": {"repo": repo, "ref": ref, "commit": commit},
    }


# --- the module's own stdin/stdout contract, pinned directly ----------------


def test_current_when_the_ref_still_points_at_the_captured_commit(
    tmp_path, run_probe_module
):
    repo_dir = tmp_path / "repo"
    sha = _init_repo(repo_dir)

    result = run_probe_module(_envelope(str(repo_dir), "refs/heads/main", sha))

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer == {"verdict": "current", "detail": None}


def test_drifted_when_the_ref_has_moved_since_capture_with_detail(
    tmp_path, run_probe_module
):
    repo_dir = tmp_path / "repo"
    captured_sha = _init_repo(repo_dir)
    current_sha = _advance_repo(repo_dir)

    result = run_probe_module(
        _envelope(str(repo_dir), "refs/heads/main", captured_sha)
    )

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "drifted"
    assert "refs/heads/main" in answer["detail"]
    assert captured_sha in answer["detail"]
    assert current_sha in answer["detail"]


def test_unknown_when_the_repo_is_inaccessible(tmp_path, run_probe_module):
    missing_repo = tmp_path / "no-such-repo"

    result = run_probe_module(
        _envelope(str(missing_repo), "refs/heads/main", "deadbeef")
    )

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert answer["detail"]


def test_unknown_when_the_ref_does_not_exist(tmp_path, run_probe_module):
    repo_dir = tmp_path / "repo"
    _init_repo(repo_dir)

    result = run_probe_module(
        _envelope(str(repo_dir), "refs/heads/does-not-exist", "deadbeef")
    )

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert "does-not-exist" in answer["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"repo": "."},
        {"repo": ".", "ref": "refs/heads/main"},
        {"repo": "", "ref": "refs/heads/main", "commit": "deadbeef"},
    ],
)
def test_unknown_when_the_payload_is_missing_fields(payload, run_probe_module):
    envelope = {
        "system": "repo-a",
        "kind": "git_ref",
        "captured_at": "2026-08-01T00:00:00Z",
        "payload": payload,
    }

    result = run_probe_module(envelope)

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert answer["detail"]


def test_unknown_and_never_a_crash_on_malformed_stdin(run_probe_module):
    result = run_probe_module("this is not json")

    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert answer["detail"]


def test_unknown_when_git_is_not_on_path(tmp_path, run_probe_module):
    repo_dir = tmp_path / "repo"
    sha = _init_repo(repo_dir)

    result = run_probe_module(
        _envelope(str(repo_dir), "refs/heads/main", sha), env={"PATH": ""}
    )

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert answer["detail"]


def test_a_repo_value_with_shell_metacharacters_is_never_shell_interpreted(
    tmp_path, run_probe_module
):
    # No shell is invoked to resolve the ref: a value that would matter to a
    # shell is just an inaccessible path to git -- never executed.
    marker = tmp_path / "should-not-exist"
    payload_repo = f"; touch {marker} ;"

    result = run_probe_module(_envelope(payload_repo, "refs/heads/main", "deadbeef"))

    assert result.returncode == 0, result.stderr
    answer = json.loads(result.stdout)
    assert answer["verdict"] == "unknown"
    assert not marker.exists()


# --- e2e via the `probe` framework: dispatch by kind (AC4), with `derive`
# reading the recorded verdicts back (AC5) ------------------------------------


def _register_git_ref_probe(write_document):
    write_document("validated-memory.md", f"probes:\n  git_ref: {GIT_REF_COMMAND}\n")


def _unit_with_git_ref_anchor(repo, ref, commit):
    return (
        "id: kb-0001\n"
        "evidence: measured\n"
        "anchors:\n"
        "  - system: repo-a\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload:\n"
        f"      repo: {repo}\n"
        f"      ref: {ref}\n"
        f"      commit: {commit}\n"
    )


def _verdict_records(adopter_dir):
    path = adopter_dir / "verdicts.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_probe_dispatches_git_ref_by_kind_and_reports_current(
    adopter_dir, write_document, write_unit, run_cli
):
    sha = _init_repo(adopter_dir / "repo")
    _register_git_ref_probe(write_document)
    write_unit("kb-0001.md", _unit_with_git_ref_anchor("repo", "refs/heads/main", sha))

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (
        "probe: 1 anchor(s) probed across 1 unit(s): 1 current, 0 drifted, 0 unknown"
        in result.stdout
    )
    records = _verdict_records(adopter_dir)
    assert records[-1]["verdict"] == "current"
    assert records[-1]["kind"] == "git_ref"
    assert records[-1]["detail"] is None

    derive_result = run_cli("derive", cwd=adopter_dir)

    assert derive_result.returncode == 0, derive_result.stderr
    index = (adopter_dir / "knowledge-index.md").read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | current |" in index


def test_probe_reports_drifted_with_detail_after_the_ref_advances(
    adopter_dir, write_document, write_unit, run_cli
):
    repo_dir = adopter_dir / "repo"
    captured_sha = _init_repo(repo_dir)
    _register_git_ref_probe(write_document)
    write_unit(
        "kb-0001.md", _unit_with_git_ref_anchor("repo", "refs/heads/main", captured_sha)
    )
    current_sha = _advance_repo(repo_dir)

    result = run_cli("probe", cwd=adopter_dir)

    assert result.returncode == 0, result.stderr
    assert (
        "probe: 1 anchor(s) probed across 1 unit(s): 0 current, 1 drifted, 0 unknown"
        in result.stdout
    )
    record = _verdict_records(adopter_dir)[-1]
    assert record["verdict"] == "drifted"
    assert captured_sha in record["detail"]
    assert current_sha in record["detail"]

    derive_result = run_cli("derive", cwd=adopter_dir)

    assert derive_result.returncode == 0, derive_result.stderr
    index = (adopter_dir / "knowledge-index.md").read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | drifted |" in index


def test_probe_reports_unknown_cleanly_for_an_inaccessible_repo_and_a_missing_ref(
    adopter_dir, write_document, write_unit, run_cli
):
    _init_repo(adopter_dir / "repo")
    _register_git_ref_probe(write_document)
    write_unit(
        "kb-0001.md",
        "id: kb-0001\n"
        "evidence: measured\n"
        "anchors:\n"
        "  - system: repo-a\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload:\n"
        "      repo: no-such-repo\n"
        "      ref: refs/heads/main\n"
        "      commit: deadbeef\n"
        "  - system: repo-b\n"
        "    kind: git_ref\n"
        "    captured_at: 2026-08-01T00:00:00Z\n"
        "    payload:\n"
        "      repo: repo\n"
        "      ref: refs/heads/does-not-exist\n"
        "      commit: deadbeef\n",
    )

    result = run_cli("probe", cwd=adopter_dir)

    # A clean probing run: exit 0, no ERROR. This is not even a
    # framework-level WARNING fallback -- the probe itself ran, answered
    # `unknown`, and explained why. `unknown` is data, not a finding.
    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert (
        "probe: 2 anchor(s) probed across 1 unit(s): 0 current, 0 drifted, 2 unknown"
        in result.stdout
    )

    records = {record["system"]: record for record in _verdict_records(adopter_dir)}
    assert records["repo-a"]["verdict"] == "unknown"
    assert records["repo-a"]["detail"]
    assert records["repo-b"]["verdict"] == "unknown"
    assert "does-not-exist" in records["repo-b"]["detail"]

    derive_result = run_cli("derive", cwd=adopter_dir)

    assert derive_result.returncode == 0, derive_result.stderr
    index = (adopter_dir / "knowledge-index.md").read_text(encoding="utf-8")
    assert "| kb-0001 | active | measured | unknown (repo-a, repo-b) |" in index


# --- textual sha comparison: the capture side must match ls-remote ----------


def test_an_abbreviated_captured_sha_reads_as_drifted(tmp_path, run_probe_module):
    # The comparison is textual against the full sha `git ls-remote` returns:
    # a capture made with an abbreviated sha never matches, and reads as
    # drifted even though the ref did not move. The payload contract demands
    # the full sha for exactly this reason.
    repo_dir = tmp_path / "repo"
    sha = _init_repo(repo_dir)

    result = run_probe_module(
        _envelope(str(repo_dir), "refs/heads/main", sha[:12])
    )

    verdict = json.loads(result.stdout)
    assert verdict["verdict"] == "drifted"


def test_an_annotated_tag_compares_against_the_tag_object_sha(
    tmp_path, run_probe_module
):
    # `git ls-remote <repo> refs/tags/v1` resolves to the tag OBJECT for an
    # annotated tag, never the peeled commit: a capture must use what the ref
    # resolves to (`git rev-parse v1`), not `v1^{commit}`.
    repo_dir = tmp_path / "repo"
    _init_repo(repo_dir)
    _git(repo_dir, "tag", "-a", "v1", "-m", "release v1")
    tag_object_sha = _git(repo_dir, "rev-parse", "v1").strip()
    peeled_sha = _git(repo_dir, "rev-parse", "v1^{commit}").strip()
    assert tag_object_sha != peeled_sha

    with_tag_object = run_probe_module(
        _envelope(str(repo_dir), "refs/tags/v1", tag_object_sha)
    )
    with_peeled = run_probe_module(
        _envelope(str(repo_dir), "refs/tags/v1", peeled_sha)
    )

    assert json.loads(with_tag_object.stdout)["verdict"] == "current"
    assert json.loads(with_peeled.stdout)["verdict"] == "drifted"
