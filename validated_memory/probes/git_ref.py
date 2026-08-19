"""The bundled `git_ref` probe: freshness for a git repository ref.

Ships with the plugin and is invocable as
`python3 -m validated_memory.probes.git_ref` -- exactly the command `init`
registers for it in the adopter's `validated-memory.md` (see `init`). It
implements the probe contract documented in the README's `probe` section:
read the anchor's envelope as JSON on stdin, answer `{"verdict": ...,
"detail": ...}` as JSON on stdout, and exit 0. This probe holds itself to
that contract directly, not just via the framework's fallback: every
failure mode is caught here and reported as `unknown` with an explanatory
`detail`, never a raw traceback, never a non-zero exit.

Payload contract (interpreted here; the envelope's `payload` is opaque to
the framework and to the base contract):

    payload:
      repo: .                       # local path or URL `git` understands
      ref: refs/heads/main          # full ref name, as `git ls-remote` expects
      commit: <sha at capture time> # what `ref` resolved to when the anchor
                                     # was captured

The live commit is resolved with `git ls-remote <repo> <ref>`, run as a
subprocess without a shell -- uniform for local paths and URLs, and `git` is
a system binary, not a pip dependency, keeping the stdlib-only rule intact.

- the live commit equals `commit` -- `current`.
- it differs -- `drifted`, with a detail naming the ref and both shas.
- the verdict cannot be determined -- `unknown`, with a detail explaining
  why: `repo`, `ref` or `commit` missing from the payload; a repo that
  cannot be reached; a ref that does not exist (`git ls-remote` exits clean
  with no output); `git` not installed; or the call taking longer than a
  fixed, generous timeout (a single call, not the framework loop, so a
  fixed timeout is enough).
"""

import json
import subprocess
import sys

from .. import verdicts as verdicts_module

_LS_REMOTE_TIMEOUT_SECONDS = 30


def main():
    """Read the envelope on stdin, answer the verdict on stdout. Always exits 0."""
    verdict, detail = _safe_evaluate(sys.stdin)
    print(json.dumps({"verdict": verdict, "detail": detail}))
    return 0


def _safe_evaluate(stdin):
    """Evaluate the envelope, never letting an exception escape.

    This probe must never abort the `probe` run it is part of: any error
    that was not anticipated by a more specific branch below still ends up
    as `unknown` with a note, not a crash.
    """
    try:
        return _evaluate(stdin)
    except Exception as error:  # noqa: BLE001 -- deliberately catch-all
        return verdicts_module.UNKNOWN, f"probe crashed evaluating the anchor: {error}"


def _evaluate(stdin):
    envelope, error = _parse_envelope(stdin.read())
    if error:
        return verdicts_module.UNKNOWN, error

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        return verdicts_module.UNKNOWN, "payload is missing or is not a JSON object"

    fields, error = _payload_fields(payload)
    if error:
        return verdicts_module.UNKNOWN, error
    repo, ref, commit = fields

    sha, error = _resolve_ref(repo, ref)
    if error:
        return verdicts_module.UNKNOWN, error

    if sha == commit:
        return verdicts_module.CURRENT, None
    return (
        verdicts_module.DRIFTED,
        f"ref '{ref}' moved from {commit} (captured) to {sha} (current)",
    )


def _parse_envelope(raw):
    """Return `(envelope, error)`: `error` is set when `raw` is not a JSON object."""
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as error:
        return None, f"envelope on stdin is not valid JSON: {error.msg}"
    if not isinstance(envelope, dict):
        return None, "envelope on stdin is not a JSON object"
    return envelope, None


def _payload_fields(payload):
    """Return `((repo, ref, commit), error)`: error names any missing field."""
    values = {name: payload.get(name) for name in ("repo", "ref", "commit")}
    missing = [name for name, value in values.items() if not _is_non_empty_string(value)]
    if missing:
        return None, f"payload is missing: {', '.join(missing)}"
    return (values["repo"], values["ref"], values["commit"]), None


def _resolve_ref(repo, ref):
    """Resolve `ref`'s live commit in `repo` via `git ls-remote`. Returns `(sha, error)`."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo, ref],
            capture_output=True,
            text=True,
            timeout=_LS_REMOTE_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return None, "the 'git' binary is not installed or not on PATH"
    except subprocess.TimeoutExpired:
        return None, (
            f"'git ls-remote {repo} {ref}' timed out after "
            f"{_LS_REMOTE_TIMEOUT_SECONDS}s"
        )
    except OSError as error:
        return None, f"'git ls-remote {repo} {ref}' could not be run: {error}"

    if result.returncode != 0:
        detail = result.stderr.strip() or "git ls-remote failed"
        return None, f"repo '{repo}' is inaccessible: {detail}"

    line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not line:
        return None, f"ref '{ref}' does not exist in repo '{repo}'"
    return line.split()[0], None


def _is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    sys.exit(main())
