---
name: supersede-outdated-docs
description: Use when a curated-knowledge unit turns out to be wrong, outdated, or replaced by better evidence. Triggers on requests like "correct kb-0003", "update this finding, it changed", "this knowledge unit is no longer true", or "supersede X with Y". Never use this to justify editing a unit's frontmatter or body in place.
---

# Supersede outdated docs

Correcting curated knowledge is never an edit. It is always a new unit.

## The rule

1. Write a **new** unit file with its own new `id`, never reusing the old one.
2. Its frontmatter declares `supersedes: [<old-id>]` (a list -- one unit may
   supersede several at once, many-to-one).
3. The superseded unit is **never** edited and **never** deleted. Its file,
   its `evidence`, its `anchors` -- all of it stays exactly as written.
   History is not rewritten.
4. If the correction is itself a chain (kb-0001 was already superseded by
   kb-0002, and kb-0002 also needs correcting), the new unit supersedes the
   *latest* unit in the chain, not the original.

## Why

`derive` computes each unit's effective state from `supersedes` across the
whole validated set -- it is never stored on the unit itself. A superseded
unit still appears in `knowledge-index.md`, marked `superseded by <ids>`,
never omitted and never mutated. Editing a unit in place would destroy the
record of what was believed and when; superseding preserves it.

## Steps

```
python3 -m validated_memory validate
```

Validate the whole `knowledge/` directory (not just the new file) so the
`supersedes` reference resolves against the unit it points at.

```
python3 -m validated_memory derive
```

Re-derive `knowledge-index.md` afterwards, so its `state` column reflects
the new supersession. If the project gates on a versioned index
(`derive --check` in CI), re-deriving is required before that gate passes
again.

If the new unit carries its own anchors, its freshness verdict starts at
`unknown` until `detect-stale-documentation` runs against it -- the superseded unit
keeps whatever verdict it last had recorded, since `probe` only probes
active units.
