---
name: detect-stale-documentation
description: Use when checking whether curated knowledge is still fresh, reading freshness verdicts, or investigating why a unit shows drifted or unknown. Triggers on requests like "check freshness", "run the probes", "is this knowledge still current", "why does kb-0002 say unknown", or "read the knowledge index".
---

# Detect stale documentation

## Run the probes

```
python3 -m validated_memory probe
```

Runs every anchor of every *active* unit (one superseded within the
validated set is excluded) through the probe registered for its `kind` in
`validated-memory.md`'s `probes:` map, and appends one record per anchor to
`verdicts.jsonl` -- append-only, never rewritten. A summary goes to stdout:

```
probe: 3 anchor(s) probed across 1 unit(s): 1 current, 1 drifted, 1 unknown
```

A `drifted` or `unknown` verdict is data, not a finding: it never gates
`probe`. Only a source-validation ERROR, or the log failing to write, does.

## Read the verdicts

```
python3 -m validated_memory derive
```

`probe` only records; `derive` is what turns the recorded verdicts into the
`verdict` column of `knowledge-index.md`. Run `derive` after `probe` to see
the update -- the index does not refresh itself.

## The ternary, fail-explicit

Every verdict is one of three values, and the framework never guesses a
fourth:

- **`current`** -- the probe re-checked the anchor and it still holds.
- **`drifted`** -- the probe re-checked the anchor and it no longer holds.
- **`unknown`** -- the probe could not tell, *or the anchor was never probed
  at all*. An anchor that has simply not been checked yet reads exactly the
  same as one a probe failed to resolve: fail-explicit means "we don't know"
  is never silently folded into "current."

A unit's verdict is the worst of its anchors' verdicts (`drifted` >
`unknown` > `current`), read from the `knowledge-index.md` table. The exact
cell format -- including how systems behind an unknown anchor are listed --
is `derive`'s algorithm, documented once in the README's `derive` section;
read the cell there, do not re-derive it by hand.

## Register a probe for a new anchor `kind`

Add an entry to the `probes:` map in `validated-memory.md`:
`<kind>: <command>`. The command is run without a shell, receiving the
anchor's envelope as JSON on stdin and answering
`{"verdict": ..., "detail": ...}` as JSON on stdout, exit 0 -- see the
README's "Probe contract" (under `probe`) for the exact shape. The plugin
ships one probe, `git_ref` (freshness of a git ref), already registered by
`init`; see the README's "The bundled `git_ref` probe".
