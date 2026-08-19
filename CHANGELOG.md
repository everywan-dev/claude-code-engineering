# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-08-19

First public release.

### The contract

- Three evidence states — `measured`, `verifiable`, `hypothesis` — that never
  blur into each other
- Anchors with a complete envelope: `system`, `kind`, `captured_at`, `payload`
- `provenance` kept separate from anchors: where the artifact lives is not the
  same as how the claim was checked
- Supersession **without deletion**: a retired unit stays, so you can still see
  why the previous answer looked right
- Adopter-declared schema extensions on top of the base contract, versioned
  independently

### The CLI

- `init` — scaffold the layout in a project. Idempotent; never overwrites.
- `validate` — units against the base contract plus the declared extension
- `lint` — the agent-memory layer: index sync, frontmatter, wikilinks, supersession
- `derive` — regenerate indexes and summaries from the units
- `probe` — re-check anchors, **ternary verdict**: same, changed, or could not
  check. "Could not check" is never folded into "still fine".

### The skills

`set-up-verified-documentation`, `document-with-evidence`, `supersede-outdated-docs`,
`detect-stale-documentation`, `keep-agent-memory-accurate`.

### Notes

- Python 3.9+, **standard library only**
- 252 tests
- Frontmatter is a deliberate YAML *subset*: no folded scalars, no anchors, no
  nested quoting. Readable without a parser, and impossible to be clever in.
