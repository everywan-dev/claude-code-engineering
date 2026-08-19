# Adoption guide

How to bring a project onto validated-memory: install the plugin, bootstrap
the layout, declare an extension, register probes, and gate CI on the
derived index. For the full command reference, see the
[README](../README.md). For a worked example end to end, see
[the walkthrough](walkthrough.md).

## 1. Install the plugin

Install `validated-memory` as a Claude Code plugin (however your harness
manages plugins -- a marketplace, a local plugin path, or a checkout
referenced directly). Once installed, its five skills are discovered from
`skills/*/SKILL.md` by directory convention, and its startup hook from
`hooks/hooks.json` -- neither needs any registration inside the adopter
project.

## 2. Bootstrap the layout

From the adopter project's root:

```
python3 -m validated_memory init
```

See the README's [`init`](../README.md#init) section for exactly what this
creates. It is idempotent and safe to re-run: existing files are never
touched.

If the harness needs to read agent memory from a fixed location outside this
project (see [Agent memory](../README.md#agent-memory)), also pass
`--harness-memory PATH`; see [the startup hook](#the-startup-hook) below for
how this stays in sync automatically after the first run.

If the harness has already been writing agent memory of its own for this
project, PATH is a real directory, not free. `init` merges it rather than
leaving two memories that cannot see each other: it copies the memory files
into this project's `memory/`, gives each one an entry in `MEMORY.md`, parks
the harness's original directory alongside as `PATH.bak`, and only then
creates the symlink. Nothing is overwritten and nothing is deleted -- see
[Absorbing an existing harness memory
directory](../README.md#absorbing-an-existing-harness-memory-directory) for
the recognition rule, the conflict rule, and what happens on failure. After
it runs, `lint` is the check that the merge is sound.

Right after bootstrapping, confirm both enforcement commands pass clean:

```
python3 -m validated_memory validate
python3 -m validated_memory lint
```

## 3. Declare an extension (optional)

The base contract (see [Base contract](../README.md#base-contract)) is
deliberately small. If units in this project need adopter-specific fields on
top of it, declare them in `knowledge-extension.md` and point
`validated-memory.md`'s `extension:` block at it -- see
[Declared extension](../README.md#declared-extension) for the
field-declaration format and the versioning rule. Skip this step entirely if
the base contract is enough: `init` already scaffolds a valid, empty
extension (`fields: []`), and leaving it empty is a normal, supported end
state, not a stub that must be filled in.

## 4. Register probes

For every anchor `kind` curated-knowledge units in this project will use,
register the command that probes it under `probes:` in
`validated-memory.md` -- see [the probe contract](../README.md#probe) for
the command's stdin/stdout shape. `init` already registers `git_ref`, the
plugin's bundled probe (see
[The bundled `git_ref` probe](../README.md#the-bundled-git_ref-probe));
register any other `kind` this project's anchors use the same way.

## 5. Gate CI on the derived index

If this project versions `knowledge-index.md`, add a CI step that fails when
it has drifted from the units or from freshly recorded verdicts:

```
python3 -m validated_memory validate
python3 -m validated_memory lint
python3 -m validated_memory derive --check
```

`derive --check` recalculates the index in memory and compares it against
the committed file, ignoring only the `Derived:` timestamp -- see
[`derive`](../README.md#derive). Run `validate` and `lint` first, so a
contract violation is reported with its own message rather than surfacing as
an opaque index mismatch. This plugin's own `.gitlab-ci.yml` runs `validate`,
`lint` and the full test suite as its gate; add `derive --check` to a
project's CI the same way once that project commits its index.

Run `python3 -m validated_memory probe` on whatever cadence fits the project
(a scheduled job, a pre-release check, ...) before the `derive --check` gate,
so the verdict column reflects current probing rather than going stale -- see
[`probe`](../README.md#probe).

## The startup hook

`hooks/restore-memory-symlink.sh`, wired as a `SessionStart` hook, keeps a
`--harness-memory` symlink alive across renames, re-clones, and fresh
sessions, without any manual step:

- Not an adopter project (no `validated-memory.md`, or no `memory/`, at the
  project root) -- does nothing.
- An adopter project -- computes the harness's per-project memory location
  and re-runs `init --harness-memory` against it, silencing its stdout.
  Idempotent and fail-open: any problem it hits (missing tools, a path it
  cannot touch, ...) is reported to stderr and the hook still exits clean,
  so it can never break session startup.

This is also where a pre-existing harness memory directory gets absorbed, on
the first session after adoption, without anyone running anything by hand.
The `.bak` it leaves behind is the only manual follow-up worth doing: once
`lint` passes and the merged memory looks right, that backup can be removed
whenever the adopter wants -- the plugin never touches it again.

Nothing here needs to be invoked by hand in the common case: it runs on
every session start for every adopter project that has ever asked for a
harness-memory symlink.
