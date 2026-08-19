# validated-memory

A Claude Code plugin that packages a validated-memory method for agent projects
as a portable component: skills that make the convention invocable, a single CLI
with the enforcement modules (agent-memory lint, contract validator, index
deriver, freshness probes with a ternary verdict), and a bootstrap scaffold.

Adopter projects keep only Markdown data and configuration; all code lives in
the plugin, so fixes reach every adopter on update. The data stays readable
without the plugin installed.

## Status

**1.0.0** -- v1 complete. Every subcommand is live: `validate` enforces the
base contract and the adopter's declared extension; `lint` enforces the
agent-memory layer; `derive` re-derives the knowledge index, with a `--check` gate, and
reads real freshness verdicts; `probe` runs freshness probes and records
them, including the bundled `git_ref` probe; `init` scaffolds a new adopter
project. Five skills make the method invocable from the CLI surface alone,
and a `SessionStart` hook keeps a `--harness-memory` symlink alive across
sessions -- see "Skills" and "Startup hook" below.

## Layers

- **Agent memory** — one Markdown file per fact plus a one-line-per-entry index,
  versioned inside the adopter repo. Supersession is exercised by rewriting the
  entry's `description`; `lint` enforces the convention.
- **Curated knowledge** — Markdown units with a base contract: identity,
  evidence state (`measured | verifiable | hypothesis`), supersession without
  deletion (`supersedes`, many-to-one), optional anchors separated from
  provenance. `validate` enforces the contract plus the adopter's declared
  extension; `derive` re-derives indexes; `probe` runs freshness probes and
  records ternary verdicts (`current | drifted | unknown`, fail-explicit).

## CLI

```
python3 -m validated_memory <command>
```

Commands: `init`, `lint`, `validate`, `derive`, `probe`.

Exit codes: `0` = clean run or WARNING-only findings (does not gate);
non-zero = ERROR (gates).

### `init`

```
python3 -m validated_memory init [--harness-memory PATH]
```

Scaffolds a new adopter project in the working directory: `knowledge/`
(empty), `memory/` with an empty index (`memory/MEMORY.md`), the adopter
configuration (`validated-memory.md`), and a valid, empty declared-extension
stub (`knowledge-extension.md`). Right after `init` on an empty directory,
`validate` and `lint` both pass clean -- the bootstrap is verified by the
enforcement it bootstraps, not by inspection. (An empty `knowledge/`
directory still reports its usual WARNING for having no units; that does not
gate.)

Each item is created only if missing. An existing item -- including one
already hand-edited -- is never touched: `init` reports `init: created
<path>` or `init: kept <path>` per item, so re-running it is idempotent and
says so. The only way `init` gates (exit 1) is an item it could not create at
all, e.g. no write permission on the target directory.

`validated-memory.md` declares the full adopter surface `extension.py`
validates: the declared extension (`schema`, `version`), the `id_prefix`,
and the probe registry, already mapping `git_ref` to its bundled probe
command (`python3 -m validated_memory.probes.git_ref`; see "The bundled
`git_ref` probe" under `probe` below) -- see "Adopter configuration"
below. `knowledge-extension.md` declares no fields (`fields: []`, a valid,
empty extension) and its body documents, in prose, the field format (`name`,
`type`, `values`; types `string` and `enum`) and the versioning rule.
Both files are plain Markdown with a YAML-subset frontmatter: readable
without the plugin installed.

**`--harness-memory PATH`** makes PATH a move-proof symlink to this
project's `memory/` directory (absolute target), so the harness can read
agent memory from wherever it expects it while the data stays versioned
inside the adopter repo:

- PATH missing: `init` creates the symlink (making parent directories as
  needed).
- PATH already a symlink -- pointing at this project, elsewhere, or broken:
  `init` re-points it at this project's `memory/`. Re-pointing a symlink
  never destroys data, so restoring it after the adopter project is renamed
  or re-cloned is exactly re-running `init --harness-memory PATH` from the
  new location: the link moves, the memory files underneath are untouched.
  Already pointing at the right place is a no-op (`kept`).
- PATH already exists as a real directory holding the harness's own agent
  memory: `init` absorbs it -- see "Absorbing an existing harness memory
  directory" below.
- PATH already exists as anything else real (a file, or a directory that is
  not agent memory): fail-open. `init` reports a WARNING naming what it found
  and why the directory did not qualify, and leaves PATH exactly as it was --
  exit 0, nothing deleted, nothing moved.

Computing PATH from the harness's own layout and calling `init
--harness-memory PATH` automatically on every session start is the plugin's
startup hook (`hooks/restore-memory-symlink.sh`, wired as `SessionStart` in
`hooks/hooks.json` -- see "Startup hook" below), and is **not** part of
`init` itself. `init` only guarantees the hook can call it repeatedly, from
any project state, without ever losing data.

#### Absorbing an existing harness memory directory

A project that adopts this plugin after the harness has already been writing
agent memory of its own finds PATH occupied by a real directory full of
memory files. Leaving it alone would leave two live memories that cannot see
each other: the harness reads its own directory, the plugin reads the
project's `memory/`, and neither shows the other's facts. So `init` absorbs
it, in this order -- nothing is parked until the copy is done:

1. **Recognize.** PATH qualifies only if every file under it is a `.md` file
   and every one of them except a top-level `MEMORY.md` carries the
   agent-memory frontmatter `lint` requires (see "Agent memory" below). A
   top-level `MEMORY.md` alone is recognition enough. Anything else -- a
   stray non-Markdown file, a `.md` without that frontmatter -- disqualifies
   the whole directory, which is then left untouched with a WARNING naming
   the file that disqualified it. Hidden files count: a stray `.gitkeep` or
   `.DS_Store` blocks the merge until someone removes it. The bias is
   deliberate: a false negative costs a warning, a false positive moves a
   directory that belongs to something else.
2. **Copy in.** Every memory file is copied into the project's `memory/`,
   preserving subdirectories, **only where the destination does not exist**.
   A destination that already holds identical content is skipped silently, so
   re-running is quiet. A destination that differs is a real conflict: the
   project's copy is kept, and a WARNING says so -- the harness's version is
   still in the backup from step 4, for a human to reconcile.
3. **Reconcile the index.** Every adopted file gets an entry in the project's
   `memory/MEMORY.md`: the line the harness's own index carried for it when
   there was one, synthesized from the file's `name` and `description`
   otherwise. Reconciling only ever appends -- entries already in the
   project's index are never rewritten or removed -- except for the `No
   entries yet.` placeholder `init` writes into a fresh index, which goes as
   soon as the index has real entries. The result passes `lint` clean, which
   is how the absorption is verified.
4. **Park.** The original directory is renamed alongside itself, to
   `<PATH>.bak` (or `.bak.1`, `.bak.2`, the first free slot -- an existing
   backup is never overwritten). Nothing is deleted: after the run there are
   two copies of every adopted file, one live inside the project and one in
   the backup.
5. **Link.** Only now is the symlink created, so the harness and the plugin
   read the same files from that point on.

The one exception to "nothing is deleted": PATH as an **empty** directory is
removed with `rmdir` and replaced by the symlink, with no backup. `rmdir` is
refused by the operating system on anything that is not empty, so it cannot
lose data, and the alternative -- an empty `.bak` on the side, or a WARNING
on every session start forever -- is worse.

Every failure along the way is fail-open: a WARNING, exit 0, and a state that
still holds every file. The order is what guarantees it -- a failed copy
leaves the original in place and unparked, a failed park leaves the copies in
the project and the original intact, and a failed link leaves the backup path
named in the WARNING.

### `lint`

```
python3 -m validated_memory lint [PATH]
```

Lints the agent-memory layer: every `*.md` file found under PATH, recursively,
except the index `MEMORY.md` itself. With no PATH it reads `memory/` relative
to the working directory. A one-line summary goes to stdout; findings go to
stderr in the same shape `validate` uses:

```
SEVERITY: <location>: <field>: <message>
SEVERITY: <location>:<line>: <field>: <message>    # parse errors only
```

`lint` resolves wikilinks and the supersession convention against the whole
memory set, so a missing `MEMORY.md`, a missing memory directory, or an
explicit PATH that does not exist each stop the run before any file is read.

### `validate`

```
python3 -m validated_memory validate [PATH]
```

Validates every `*.md` unit found under PATH, recursively; PATH may also be a
single unit file. With no PATH it reads `knowledge/` relative to the working
directory. A one-line summary goes to stdout; findings go to stderr as

```
SEVERITY: <unit>: <field>: <message>
SEVERITY: <unit>:<line>: <field>: <message>    # parse errors only
```

A contract rule speaks about the unit as a whole, so it reports no line. Only
the parser reports one, because only the parser knows where it stopped.

Supersession resolves against the validated set: validate the whole knowledge
directory, not a single file, or a `supersedes` entry pointing at a unit you
left out is reported as missing.

### `derive`

```
python3 -m validated_memory derive [PATH] [--check]
```

Re-derives the curated-knowledge index from the units under PATH, resolved
exactly like `validate`'s PATH (default `knowledge/`, single unit file or a
directory, same errors on a missing path). Deriving requires a valid source:
`derive` first runs the same validation as `validate` (base contract plus the
adopter's declared extension). An ERROR finding reports the findings to
stderr, in `validate`'s format, and stops -- nothing is written or checked.
A WARNING does not block.

The index is written to `knowledge-index.md` in the current working
directory, never inside `knowledge/`: anything ending in `.md` there is read
as a unit (see "Keep the schema outside the curated-knowledge directory"
above -- the same reason applies to the index).

```markdown
# Knowledge index

Derived: 2026-08-12T10:00:00Z
Basis: 2 unit(s) under knowledge/

| id | state | evidence | verdict |
|----|-------|----------|---------|
| kb-0001 | superseded by kb-0002 | measured | unknown |
| kb-0002 | active | hypothesis | unknown |
```

- `Derived:` is the UTC ISO-8601 timestamp of the derivation run.
- `Basis:` is the recount basis: how many units, under which path.
- Rows are sorted by `id`. Nothing is omitted: a superseded unit is still
  listed, marked, never mutated.
- **state** is computed, never stored on the unit: `active`, or
  `superseded by <ids>` naming every unit that lists this one in its own
  `supersedes` (many-to-one), sorted and comma-separated.
- **verdict** reads the service view of `verdicts.jsonl` (the log `probe`
  writes -- see the `probe` section below): for each of the unit's anchors,
  the latest verdict recorded for that anchor, or `unknown` when it was never
  probed -- fail-explicit. A unit is graded by the worst of its
  anchors' verdicts (`drifted` > `unknown` > `current`):
  - no anchors: `unknown`, on its own.
  - the worst verdict is `unknown`: `unknown (<systems>)`, naming every
    system behind an `unknown` anchor, sorted and comma-separated -- this
    also covers a unit with anchors that was never probed at all.
  - the worst verdict is `drifted` and some anchors are also `unknown`:
    `drifted (unknown: <systems>)`.
  - otherwise: the verdict alone (`current` or `drifted`).

`--check` recalculates the index in memory instead of writing it, and
compares it against the `knowledge-index.md` already on disk, line by line.
The `Derived:` line must be there, but **its timestamp is ignored** -- it
changes on every run, so what has to match is the rest: `Basis:` and the
table. A missing index is an ERROR pointing at running `derive` first. Any
divergence -- `Basis:`, a row, a missing or extra line -- is an ERROR naming
the first line that does not match, numbered as on disk. `--check` never
writes. A match exits clean with a summary. This makes `derive --check` a
local or CI gate for adopters who version the derived index: hand-editing it,
or letting it drift from the units, fails the check. **The verdict column is
part of that content**: running `probe` between a `derive` and a
`derive --check` changes what the recalculated index says, so the check
correctly fails against the now-stale on-disk index -- run `derive` again to
pick up the new verdicts.

Exit codes: `0` clean, or WARNING-only validation findings; `1` an ERROR
finding (source validation, or a `--check` mismatch); `2` a usage error.

### `probe`

```
python3 -m validated_memory probe [PATH]
```

Runs freshness probes over the anchors of every *active* curated-knowledge
unit found under PATH, resolved exactly like `validate`'s PATH (default
`knowledge/`), and records what each probe answered. "Active" excludes a unit
that appears in another unit's `supersedes` within the validated set -- a
superseded unit is not current, so its anchors are never probed. Probing
requires a valid source: `probe` first runs the same validation as `validate`
and `derive` (base contract plus the adopter's declared extension); an ERROR
finding stops the run before anything is probed. A WARNING does not block.

**Probe contract.** A probe is registered per anchor `kind` in the `probes`
map of `validated-memory.md` (see "Adopter configuration" above). The
registered command is split with `shlex.split` and run **without a shell**.

- It receives the anchor's envelope on **stdin**, as JSON:
  ```json
  {"system": "repo-a", "kind": "git_ref", "captured_at": "2026-08-11T10:00:00Z", "payload": {}}
  ```
  The unit's id is deliberately not included -- the envelope is the
  producer/store boundary, and a probe only needs to know what it is
  checking, not which unit cites it.
- It answers on **stdout**, as JSON, and exits `0`:
  ```json
  {"verdict": "current", "detail": "optional free-form note"}
  ```
  `verdict` is one of `current | drifted | unknown`; `detail` is optional.

Any failure falls back to `unknown`, with a note explaining why, and never
aborts the run: no probe registered for the anchor's `kind` (or no
`validated-memory.md` at all), a command that cannot be run (parse failure,
executable not found), a non-zero exit, stdout that does not parse as JSON,
or a verdict outside the three-value domain. Each such fallback is reported
to stderr as a WARNING finding, in the usual shape:

```
WARNING: <unit>: anchors[<i>]: <message>
```

**The verdict log.** Every anchor probed -- successful or fallen back --
appends one JSON line to `verdicts.jsonl` in the current working directory,
never inside `knowledge/`, for the same reason `knowledge-index.md` lives
outside it (see "Keep the schema outside the curated-knowledge directory"
above). The log is **append-only**: a run never rewrites or removes a prior
line, so the full probing history accumulates. Each line:

```json
{"recorded_at": "2026-08-12T10:00:00Z", "unit": "kb-0001", "system": "repo-a", "kind": "git_ref", "payload": {"ref": "refs/heads/main"}, "verdict": "current", "detail": null}
```

**An anchor is identified by what it points at**: its `system`, its `kind`
and its `payload`. `captured_at` dates a capture; it does not identify one.
That is why the record carries the payload, and it is also what makes the log
a record of what was actually measured rather than of the fact that something
was.

The distinction is not academic. A unit may legitimately carry two anchors
sharing a `(system, kind)` -- two refs of the same repository are both
`git_ref` on the same system. Keyed on that pair alone they collapsed into
one entry, so the later verdict overwrote the earlier: `probe` would report
`1 current, 1 drifted` and the index would then say `current` about a unit
whose anchor had drifted, with the winner decided by the order the anchors
happened to be written in. A false "still true" is the one answer this tool
must never give.

A record written before payloads were recorded carries none, and **is never
attributed to an anchor**. It is not only that the log cannot say which anchor
it was about; it cannot say what that anchor pointed at when it was written,
and an anchor can be re-captured. A single-anchor unit is no exception: its
`payload` may have changed since, so reading the old record would again be
reporting `current` for something that has drifted. The record stays in the
log, because history is not rewritten, and it is ignored: the anchor reads
`unknown` until it is probed again, which repairs itself on the next `probe`.

The payload in a record is compared against the anchor's exactly as the
frontmatter parser produced it, and that parser infers no types -- every
scalar is a string (see "Frontmatter subset"). A record hand-edited to carry
`true` or `3` where the anchor says `"true"` or `"3"` names a different
payload, so it is a different anchor. That is deliberate: coercing them would
be inferring a type, which nothing else here does.

The **service view** a reader wants -- and the one `derive` reads for its
verdict column -- is the latest record per anchor; re-probing
adds new lines, it never edits history.

A summary goes to stdout:

```
probe: 3 anchor(s) probed across 1 unit(s): 1 current, 1 drifted, 1 unknown
```

Exit codes: `0` clean, or WARNING-only findings -- **a `drifted` or
`unknown` verdict is data, not a finding, and never gates `probe`**; `1` an
ERROR (source validation, or the verdict log could not be written); `2` a
usage error.

#### The bundled `git_ref` probe

Ships with the plugin at `validated_memory/probes/git_ref.py`, invocable as
`python3 -m validated_memory.probes.git_ref` -- the command `init` already
registers for `git_ref` in the scaffolded `validated-memory.md` (see
"Adopter configuration" below). It implements the probe contract above for
one `kind`: freshness of a git repository ref.

Its payload, interpreted by the probe -- the envelope itself does not know
its shape:

```yaml
payload:
  repo: .                       # local path or URL `git` understands
  ref: refs/heads/main          # full ref name
  commit: <sha at capture time> # what `ref` resolved to when the anchor
                                 # was captured
```

The live commit is resolved with `git ls-remote <repo> <ref>`, run as a
subprocess without a shell -- uniform for local paths and URLs, and `git` is
a system binary, not a pip dependency, so this keeps the stdlib-only rule.
`git` must be installed and on `PATH`.

The comparison is textual, against the full sha `git ls-remote` returns, so
the capture side must record exactly that: `commit` is the **full 40-hex
sha** the ref resolves to (`git rev-parse <ref>`). Two captures that read
naturally but never match: an abbreviated sha, and -- for an annotated tag --
the peeled commit (`v1^{commit}`), since the ref resolves to the tag
*object*. Both read as a permanent, misleading `drifted`; capture what the
ref resolves to, not what it points at.

- the live commit equals `commit` -- `current`.
- it differs -- `drifted`, with a detail naming the ref and both shas.
- the verdict cannot be determined -- `unknown`, with a detail explaining
  why: `repo`, `ref` or `commit` missing from the payload; a repo that
  cannot be reached; a ref that does not exist (`git ls-remote` exits clean
  with no output); or `git` not installed or not on `PATH`.

Like every probe, it never gates the run over its own verdict, and it holds
itself to the probe contract directly rather than leaning on the
framework's fallback: every failure it can anticipate is caught and turned
into `unknown` with a reason here, so it never raises, never prints a raw
traceback, and never exits non-zero.

## Agent memory

The agent-memory layer is one Markdown file per fact (`memory/*.md`), plus a
one-line-per-entry index at `memory/MEMORY.md`. `lint` enforces five things.

**Frontmatter.** Every memory file's frontmatter carries the shape the Claude
Code harness gives it -- `lint` does not redefine it, only requires it be
complete:

```yaml
name: short-kebab-slug        # required; a non-empty string
description: one-line summary # required; a non-empty string
metadata:
  type: user                  # required; user | project | feedback | reference
```

`name`, `description` or `metadata.type` missing, or `metadata.type` outside
its domain, is an ERROR. Additional keys the harness may add are tolerated
without being checked. A `name` must be unique across the memory set: a
duplicate is an ERROR, since wikilinks resolve by `name` and a duplicate
makes that resolution ambiguous.

**Identity.** A memory's canonical identity is its **filename** without
`.md`. `name` is the identifier wikilinks resolve against, and it gives way
to the filename when the two disagree: the repair is to rewrite `name`, never
to rename the file. The reason is measured rather than aesthetic -- in the
corpus behind ADR 0001, a third of the `name` values were titles carrying
spaces, dots and capitals, for which no rename exists at all.

`lint` reports a divergence against the file, naming both sides and the
direction of the repair:

```
WARNING: memory/coffee-preference.md: name: 'Coffee Preference' does not match
the filename 'coffee-preference'; the filename is the canonical identity --
repair 'name' to match it
```

**This is a WARNING purely as a migration concession**, so that a project
whose memory was written before the rule can adopt the plugin without being
gated on its whole backlog. It is not the norm: the rule is that they match,
and the finding **becomes an ERROR in 2.0.0**. The memory layer carries no
version of its own, so it versions with the plugin. A memory whose `name` is
missing or empty is not also reported as diverging -- that defect already has
its own ERROR, and reporting it twice would say the same thing in two places.

Because the filename is the identity, two memories **carrying the same
filename** are two memories claiming the same identity. Two files in one
directory cannot share a name, so this only arises across subdirectories, and
it is a fact about the files: it is reported even when neither one's
frontmatter parses.

```
WARNING: memory/beta/shared.md: filename: the filename 'shared' is also
carried by memory/alpha/shared.md; the filename is the canonical identity,
so these are two memories with the same identity -- rename one
```

Renaming is the repair here, and it does not contradict the rule above: what
that rule forbids is renaming a file to match its `name`, and what collides
here is two files, not a file and its `name`. Reporting it matters now
because otherwise `lint` tells both files to repair `name` towards the same
value, and following that advice lands on the duplicate-name ERROR with no
warning it was coming. It is a WARNING for the same migration reason, and
**becomes an ERROR in 2.0.0** alongside the divergence rule.

Resolution itself is unchanged: still by `name`. What ADR 0001 settles is
only which of the two fields gives way when they disagree -- see
`docs/adr/0001-filename-is-the-canonical-memory-identity.md`.

**Index.** `MEMORY.md`, at the root of the memory directory, lists one entry
per fact as a Markdown bullet with a link to the file, relative to the
directory:

```markdown
- [Coffee preference](coffee-preference.md) — oat milk in coffee
```

Only bullet lines shaped `- [Title](file.md)` count as entries; headers and
prose are ignored. The index and the memory files must agree in both
directions: an entry whose file does not exist, and a memory file with no
entry in the index, are each an ERROR. A missing `MEMORY.md` stops the run,
pointing at `validated-memory init`.

**Wikilinks.** A `[[name]]` reference in `description` or in a file's body
names another memory by its `name`. A wikilink whose target does not exist is
a WARNING -- it marks something pending to write, and does not gate.

When the target does not resolve but a file **of that name** exists, the
warning names that instead, because "pending to write" would point at the
wrong repair -- the memory is right there, and what does not resolve is its
`name`:

```
WARNING: memory/notes.md: body: wikilink to 'coffee-preference' has no
matching memory; 'coffee-preference.md' declares name 'Coffee Preference'
```

This is the ordinary consequence of a divergence, since people writing
wikilinks reach for the filename. The cause is named only when it is certain:
if two memories in different subdirectories share a filename, either could be
meant, so the generic warning stands rather than guess one.

**Supersession.** A memory is marked superseded by rewriting its
`description` to start with the literal prefix `superseded by ` followed by a
wikilink, e.g. `superseded by [[coffee-preference]]`. Well formed -- the
wikilink resolves to a different memory that exists -- it is recognized and
raises no finding. Malformed is an ERROR: the prefix with no parseable
wikilink after it, a wikilink pointing at a memory that does not exist, or a
wikilink pointing at the memory itself.

A successor is not allowed to stay pending the way an ordinary wikilink is,
so this gates. That is precisely why it names the cause when the target is a
diverging file, rather than reporting a memory that is plainly there as
missing:

```
ERROR: memory/old-note.md: description: supersession points at
'coffee-preference', which does not resolve by name;
'coffee-preference.md' declares name 'Coffee Preference'
```

Pointing at **this memory's own filename** counts as pointing at itself,
whatever its `name` currently says -- the filename is the identity. A target
that does resolve to another memory is a valid supersession even when it
happens to equal this file's filename, so resolution is settled first.

## Base contract

Every curated-knowledge unit is a Markdown file whose frontmatter carries:

```yaml
id: <stable-unique-id>          # required; letters, digits, '.', '_', '-'
evidence: measured              # required; measured | verifiable | hypothesis
supersedes: []                  # optional; ids this unit supersedes (many-to-one)
anchors:                        # optional; without anchors a unit cannot expire
  - system: <system-name>       # complete envelope: all four fields required
    kind: git_ref               # probe discriminator; no whitespace
    captured_at: 2026-08-11T10:00:00Z   # ISO-8601 date or timestamp
    payload: {}                 # mapping; interpreted by the probe, not here
provenance: []                  # optional; where the native artifact lives
```

The three evidence states say how a claim is backed, and never mix planes:

- **`measured`** -- directly observed or computed by executing something,
  with a way to re-check it.
- **`verifiable`** -- not directly measured, but checkable without executing,
  by someone who follows the provenance.
- **`hypothesis`** -- a claim not yet checked. A unit is never promoted out
  of it by conviction: promotion is a new unit with better evidence that
  supersedes this one.

An unknown top-level field is an ERROR: adopter-specific fields belong to a
declared extension. A unit with no anchors is a WARNING, not an ERROR.

An `id` must be unique and stable. `validate` enforces form and uniqueness
across the validated set; stability is a convention no single run can check,
since nothing records what the id was before. Reuse of an id across time is
caught by supersession, not by the validator: correct a unit by writing a new
one that supersedes it, never by editing its id.

**A supersession chain has to end.** Supersession retires a fact by naming
what replaces it, so a chain that closes on itself -- `kb-0001` superseding
`kb-0002` while `kb-0002` supersedes `kb-0001`, at any length -- leaves every
unit in it superseded and none live. An ERROR, not a note, because the
consequence is silent: the whole group drops out of the index's active view
**and `probe` stops probing it**, since only active units are probed. Nothing
was deleted, yet the knowledge stops being checked, which is the failure this
contract exists to prevent. There is no migration case to protect -- a cycle
is never intentional and never correct.

```
ERROR: knowledge/kb-0001.md: supersedes: supersession cycle: kb-0001 ->
kb-0002 -> kb-0001; every unit in it is superseded, so none is live and none
is probed
```

A unit superseding itself is a cycle of one and has its own rule; it is not
also reported here.

## Adopter configuration

The adopter's configuration is a file named `validated-memory.md`, read from
the working directory. This version declares three fields, each optional:

```yaml
extension:                         # the declared extension (next section)
  schema: knowledge-extension.md
  version: "1"
id_prefix: kb-                     # the id scheme the adopter's units follow
probes:                            # probe registry: kind -> command
  git_ref: run-git-ref-probe
```

`id_prefix` records the id scheme for humans and skills; `validate` does not
enforce it. `probes` maps an anchor `kind` to the command that probes it (the
`probe` subcommand consumes it). An unknown configuration field, an empty
`id_prefix`, or a probe entry whose command is not a non-empty string each
stop every run with an ERROR naming the configuration file: the configuration
is one document, and a malformed key gates even the subcommands that do not
consume it.

## Declared extension

An adopter extends the contract without forking it. The `extension` block of
the configuration names a versioned schema:

```yaml
extension:
  schema: knowledge-extension.md   # path, relative to the configuration file
  version: "1"                     # the schema version this project is on
```

The schema declares the fields the adopter's units may carry:

```yaml
fields:
  - name: domain
    type: enum                     # closed domain: 'values' is required
    values:
      - network
      - storage
  - name: owner
    type: string                   # any non-empty scalar
```

A declared field carrying a valid value passes. A value outside a closed
domain, and a field neither the base contract nor the schema declares, are
ERRORs naming the unit and the field. A declared field is permitted, not
required: v1 has no way to demand one.

Keep the schema outside the curated-knowledge directory. Anything ending in
`.md` under `knowledge/` is read as a unit, and a schema is not one.

With no configuration file, or with one that declares no `extension` block,
only the base contract applies. With an extension declared, loading is
fail-loud: an unreadable or malformed configuration, a schema that does not
exist, an unknown field type, an enum with no values, a field that redeclares a
base contract field -- each stops the run with an ERROR against the offending
document. Nothing here degrades to base-contract-only validation, because an
extension ignored in silence validates nothing while appearing to pass.

### Versioning the schema

`version` records which schema version the project is on. Adding a field, or
adding a value to a closed domain, is additive and does not bump it. Removing
or narrowing anything does. Units already written are never rewritten to match
a newer schema: correct a unit by writing a new one that supersedes it.

### Frontmatter subset

The frontmatter parser is not a YAML parser. It accepts block mappings, block
lists, nested blocks, empty inline collections (`[]`, `{}`) and plain or quoted
scalars. Everything else -- tabs, block scalars (`|`, `>`), anchors and aliases,
non-empty inline collections, duplicate keys, a key with no value -- is an
ERROR. Scalars are always strings; no type is inferred. A unit whose
frontmatter fails to parse is never validated on a best-effort basis: the parse
error is the only finding reported for it.

## Skills

Five skills, under `skills/*/SKILL.md`, make the method invocable from an
agent session using only the CLI surface documented above -- each names the
exact `validated-memory` invocation to run and the data discipline to
follow, never reimplementing a rule the CLI already enforces:

- **`adopt-validated-memory`** -- bootstrap a project (`init`), wire
  `--harness-memory`, verify the result with `validate` and `lint`.
- **`create-knowledge-unit`** -- write a new curated-knowledge unit, base
  contract field by field, with the evidence-state discipline (never
  promote by conviction; anchors are probeable, provenance is not).
- **`supersede-knowledge`** -- correct existing knowledge with a new unit
  and `supersedes`, never by editing or deleting the superseded one.
- **`probe-freshness`** -- run `probe`, then `derive`, and read the ternary
  verdict in `knowledge-index.md`.
- **`maintain-agent-memory`** -- record or supersede an agent-memory fact,
  and verify the memory set with `lint`.

For the full adoption sequence, see `docs/adoption.md`. For a complete,
reproducible run through every layer -- `init` → create a unit → `validate`
→ `derive` → `probe` → supersede → `derive` again -- see
`docs/walkthrough.md`.

## Startup hook

A `SessionStart` hook (`hooks/hooks.json`, running
`hooks/restore-memory-symlink.sh`) restores a project's `--harness-memory`
symlink automatically on every session start -- the wiring the
`--harness-memory` section above defers to it. It computes the harness's
per-project memory location the same way Claude Code lays out
`~/.claude/projects/` -- one directory per project, keyed by the project's
own path with **every character that is not a letter or a digit** replaced by
`-` -- and re-runs `init --harness-memory` against it, with its stdout
silenced. That rule covers `_` and `.`, not only `/`:
`/home/u/Claude/billing_platform/invoice_migration` is keyed
`-home-u-Claude-billing-platform-invoice-migration`. Getting it wrong is the one
failure here that is silent rather than fail-open -- `init` reports success
against a directory the harness never reads, and the memory simply never
shows up -- so the rule is pinned by a test rather than left to the
substitution being "obviously" about slashes.

The hook is fail-open throughout, matching `init`'s own contract: no
`$CLAUDE_PROJECT_DIR`, a project that has not adopted validated-memory (no
`validated-memory.md`, or no `memory/`, at its root), no `python3` on
`PATH`, or any other problem along the way is a clean no-op -- it never
gates or breaks session startup, and it never deletes data.

Because the hook runs unattended, it is also where "Absorbing an existing
harness memory directory" (above) normally happens: the first session after a
project adopts the plugin merges the harness's pre-existing memory into the
project and parks the original as a `.bak`. That merge is deliberately part
of `init` rather than a flag the hook passes, so it happens once, by itself,
on the deployment path -- gated by the recognition rule, which is what keeps
it from touching anything that is not agent memory. See `docs/adoption.md`
("The startup hook") for the adopter-facing summary.

## Development

Runtime code is Python 3, standard library only. pytest is the only
development dependency.

```
python3 -m pytest
```

Tests are end-to-end only: they invoke the CLI as a subprocess over fixture
adopter trees and assert on exit codes, output, and produced files. Tests never
import the package's internals.
