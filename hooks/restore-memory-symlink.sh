#!/bin/bash
# restore-memory-symlink.sh -- SessionStart hook for the validated-memory plugin.
#
# Restores the harness's move-proof `--harness-memory` symlink for whatever
# project the harness just opened, so an adopter never has to re-run
# `validated-memory init --harness-memory` by hand after a rename, a
# re-clone, or simply a new session. See the README's "`--harness-memory
# PATH`" section (under `init`) and docs/adoption.md ("The startup hook")
# for the full contract this delegates to.
#
# Fail-open, unconditionally: every branch below either does nothing or
# calls `init`, which is itself idempotent and never destroys data (see
# validated_memory/init.py). Nothing in this script ever deletes a file,
# and the script always exits 0 -- a SessionStart hook must never be able
# to break session startup, whatever it finds.
#
# One thing `init` does do on this path is merge: if the harness memory
# location computed below already holds the harness's own agent memory,
# `init` absorbs it into the project, parks the original as a '.bak' and
# then links (see validated_memory/adopt.py, and the README's "Absorbing an
# existing harness memory directory"). That is deliberate and happens here,
# unattended, on the first session after a project adopts the plugin -- it
# still deletes nothing, and it still exits 0 either way.
#
# What "adopted" means here: the project directory the harness just opened
# (`$CLAUDE_PROJECT_DIR`) has both `validated-memory.md` and `memory/` at
# its root. Anything else -- not adopted yet, only half-scaffolded, or no
# project directory at all -- is a clean no-op.
#
# Harness memory location: this mirrors the per-project layout Claude Code
# itself uses under `~/.claude/projects/` -- one directory per project, named
# after the project's own path with every character that is not a letter or a
# digit replaced by '-'. That covers '_' and '.', not just '/': a project at
# `/home/u/Claude/billing_platform/invoice_migration` lands under
# `-home-u-Claude-billing-platform-invoice-migration`, and `/home/u/.ssh` under
# `-home-u--ssh`. Getting this wrong fails silently -- `init` reports success
# against a directory the harness never reads -- so it is pinned by a test.
#
#   ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/<project dir, [^A-Za-z0-9] -> '-'>/memory

set -u

if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
  exit 0
fi

# Normalize away a trailing slash so the slug below never doubles a '-'.
project_dir="${CLAUDE_PROJECT_DIR%/}"

if [ ! -f "$project_dir/validated-memory.md" ] || [ ! -d "$project_dir/memory" ]; then
  # Not an adopter project (or only half-scaffolded): nothing to restore.
  exit 0
fi

config_dir="${CLAUDE_CONFIG_DIR:-${HOME:-}/.claude}"
if [ -z "${CLAUDE_CONFIG_DIR:-}" ] && [ -z "${HOME:-}" ]; then
  echo "restore-memory-symlink: no CLAUDE_CONFIG_DIR and no HOME; skipping" >&2
  exit 0
fi

# Resolve a relative config dir against THIS shell's cwd, before the subshell
# below changes into the project: otherwise `init` would resolve it against
# the project directory and write a spurious tree inside the adopter repo.
case "$config_dir" in
  /*) ;;
  *) config_dir="$PWD/$config_dir" ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
  echo "restore-memory-symlink: python3 not found on PATH; skipping" >&2
  exit 0
fi

# Computed with python3 rather than `sed` on purpose: the substitution is per
# character, and `sed`'s character class depends on the locale, which a hook
# does not control -- under LC_ALL=C an accented character would become two or
# three '-' instead of one, and the path would silently miss.
slug=$(printf '%s' "$project_dir" | python3 -c '
import re, sys
sys.stdout.write(re.sub(r"[^A-Za-z0-9]", "-", sys.stdin.read()))
')
if [ -z "$slug" ]; then
  echo "restore-memory-symlink: could not derive the project slug; skipping" >&2
  exit 0
fi
harness_memory="$config_dir/projects/$slug/memory"

# The plugin's own package root: this script lives at <plugin root>/hooks/,
# so its parent directory is where `validated_memory/` lives. Computed from
# the script's own path rather than trusted to `$CLAUDE_PLUGIN_ROOT` alone,
# so it also works when this repo is exercised directly (tests, or a manual
# run) without going through a full plugin install.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
if [ -z "$script_dir" ]; then
  echo "restore-memory-symlink: could not resolve the plugin's own path; skipping" >&2
  exit 0
fi
plugin_root="$(dirname "$script_dir")"

(
  cd "$project_dir" 2>/dev/null || exit 0
  PYTHONPATH="$plugin_root${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m validated_memory init --harness-memory "$harness_memory" >/dev/null
)

# Whatever happened inside the subshell above -- created, kept, re-pointed,
# or even an internal error -- this hook always reports success: init's own
# fail-open WARNINGs are already visible on stderr (stdout alone is
# silenced), and a SessionStart hook must never gate session startup.
exit 0
