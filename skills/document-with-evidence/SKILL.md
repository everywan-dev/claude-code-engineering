---
name: document-with-evidence
description: Use when recording a new piece of curated knowledge -- a finding, a decision, a measured fact worth keeping and later re-checking for freshness. Triggers on requests like "record this as knowledge", "write a knowledge unit for X", "capture this finding with evidence", or "add this to curated knowledge". Do not use for a quick personal or project preference; that belongs to the keep-agent-memory-accurate skill instead.
---

# Document with evidence

A curated-knowledge unit is one Markdown file under `knowledge/`, with
frontmatter carrying the base contract. Write the file directly (or via your
usual editing tools) -- there is no `validated_memory` subcommand that
creates one; `validate` only checks what you wrote.

## The base contract, field by field

```yaml
---
id: kb-0001                    # required; stable, unique; matches the adopter's id_prefix
evidence: measured              # required; measured | verifiable | hypothesis
supersedes: []                  # optional; ids this unit supersedes (see supersede-outdated-docs)
anchors:                        # optional; without anchors a unit cannot expire
  - system: <system-name>
    kind: <probe-kind>          # must match a kind registered in validated-memory.md
    captured_at: 2026-08-12T00:00:00Z
    payload: {}                 # interpreted by the probe, not by validate
provenance: []                  # optional; where the native artifact lives
---
```

- **`id`** -- check `id_prefix` in `validated-memory.md` for the scheme this
  project follows. Never reuse an id once written; a correction is a new
  unit (see `supersede-outdated-docs`).
- **`evidence`** -- pick the state the knowledge actually has *right now*,
  not the state you hope to reach (canonical definitions: the README's
  "Base contract" section):
  - `measured` -- directly observed or computed, with a way to re-check it.
  - `verifiable` -- not directly measured, but checkable by someone who
    follows the provenance.
  - `hypothesis` -- a claim not yet checked.

  Never promote a unit's evidence state by editing it in place because you
  have grown more confident. Promotion is not a state change on the same
  file; it is a new unit with better evidence that supersedes this one
  (`supersede-outdated-docs`). Evidence state moves forward only by writing new
  knowledge, never by conviction.
- **`anchors`** vs **`provenance`** -- do not mix the two planes:
  - An anchor is a *probeable* claim: "system X, of kind K, was true as of
    `captured_at`, described by this payload" -- exactly what
    `detect-stale-documentation` re-checks later. A unit with no anchors can never be
    checked for freshness (a WARNING, not an ERROR).
  - Provenance is *not* probed: it records where the native artifact (a
    query, a document, a conversation) lives, for a human to go look. Put a
    link or a citation there, not something you expect a probe to check.

## Verify

```
python3 -m validated_memory validate
```

Run it over the whole `knowledge/` directory, not a single file:
`supersedes` resolves against the validated set, so validating one file in
isolation reports a real `supersedes` target as missing. See the README's
"Base contract" section for the exact rules `validate` enforces (required
fields, id form, anchor envelope shape, and so on) -- this skill only covers
the data discipline, not the validator's error conditions.

If the project declares an extension (`knowledge-extension.md`), your unit
may also carry the fields it declares, on top of the base contract; an
undeclared field is an ERROR. See the README's "Declared extension" section.
