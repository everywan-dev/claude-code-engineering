# Walkthrough

A complete, reproducible run through validated-memory: adopt a project,
write a curated-knowledge unit, validate it, derive the index, probe its
freshness, correct it by superseding, and derive again. Every command below
is exactly what [`tests/test_walkthrough.py`](../tests/test_walkthrough.py)
runs; that test is the source of truth -- if this page and the test ever
disagree, the test is right and this page gets corrected.

Run every command from the adopter project's root. Values that are
generated fresh on each run -- the `Derived:` timestamp, the git commit sha
-- are shown here as they looked on one real run; expect different ones,
same shape, on yours.

## 1. Adopt the project

```
python3 -m validated_memory init
```

```
init: created knowledge
init: created memory
init: created memory/MEMORY.md
init: created validated-memory.md
init: created knowledge-extension.md
init: 5 created, 0 kept, 0 error(s), 0 warning(s)
```

`init` already registers the bundled `git_ref` probe in
`validated-memory.md` (see [the README's `init` section](../README.md#init)),
so the unit below can be probed without any extra configuration.

## 2. Create a curated-knowledge unit

This walkthrough anchors its unit to a small git repository at `repo/`
(any repository `git` can reach works the same way -- see
[The bundled `git_ref` probe](../README.md#the-bundled-git_ref-probe)).
Capture the commit its default branch is at:

```
git init -q -b main repo
echo hello > repo/file.txt
git -C repo add file.txt
git -C repo -c user.name=you -c user.email=you@example.com commit -q -m "first commit"
git -C repo rev-parse HEAD
```

Write `knowledge/kb-0001.md`, using that commit as `payload.commit`:

```markdown
---
id: kb-0001
evidence: measured
anchors:
  - system: sample-repo
    kind: git_ref
    captured_at: 2026-08-12T00:00:00Z
    payload:
      repo: repo
      ref: refs/heads/main
      commit: <the sha `rev-parse` printed>
---

The sample repository's default branch is at this commit.
```

See the `document-with-evidence` skill and the README's
[Base contract](../README.md#base-contract) for what each field means.

## 3. Validate

```
python3 -m validated_memory validate
```

```
validate: 1 unit(s) checked, 0 error(s), 0 warning(s)
```

## 4. Derive the index

```
python3 -m validated_memory derive
```

```
derive: 1 unit(s) indexed
```

`knowledge-index.md` now exists, with the anchor still unprobed:

```markdown
| id | state | evidence | verdict |
|----|-------|----------|---------|
| kb-0001 | active | measured | unknown (sample-repo) |
```

`unknown (sample-repo)` names the system behind the anchor that has never
been checked -- fail-explicit, per the README's [`probe` section](../README.md#probe):
an anchor nobody has probed yet reads the same as one a probe failed to
resolve, never as a silent pass.

## 5. Probe

```
python3 -m validated_memory probe
```

```
probe: 1 anchor(s) probed across 1 unit(s): 1 current, 0 drifted, 0 unknown
```

The ref has not moved since capture, so the recorded verdict is `current`
(appended to `verdicts.jsonl`; see the README's
[Probe contract](../README.md#probe)). The index on disk does not update by
itself -- see the next `derive` below.

## 6. Supersede: correct the unit, never edit it

New evidence justifies upgrading this fact from `measured` to `verifiable`.
Per the `supersede-outdated-docs` skill, that is never an edit: write a new unit,
`knowledge/kb-0002.md`, that supersedes the first one. `kb-0001.md` is left
byte-for-byte untouched.

```markdown
---
id: kb-0002
evidence: verifiable
supersedes:
  - kb-0001
anchors:
  - system: sample-repo
    kind: git_ref
    captured_at: 2026-08-12T00:05:00Z
    payload:
      repo: repo
      ref: refs/heads/main
      commit: <the same sha as above>
---

Re-checked and confirmed: same commit, upgraded to verifiable.
```

## 7. Derive again

```
python3 -m validated_memory derive
```

```
derive: 2 unit(s) indexed
```

```markdown
| id | state | evidence | verdict |
|----|-------|----------|---------|
| kb-0001 | superseded by kb-0002 | measured | current |
| kb-0002 | active | verifiable | unknown (sample-repo) |
```

`kb-0001` is now marked `superseded by kb-0002` -- computed, never written
onto the unit itself -- but it keeps the `current` verdict `probe` already
recorded for it: `derive` never mutates a unit and never re-probes on its
own. `kb-0002` is active with its own anchor, not yet probed, so it starts
at `unknown` again. Running `probe` once more would pick it up; see the
`detect-stale-documentation` skill.
