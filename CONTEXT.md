# validated-memory

A Claude Code plugin that keeps an agent project's knowledge trustworthy: what
is recorded, how it is proven, and how it stops being true without ever being
erased.

## Language

### The two layers

**Memory entry**:
One Markdown file recording one fact the agent should carry between sessions.
Its frontmatter is fixed and identical in every project (`name`,
`description`, `metadata.type`). Its identity is its filename; `name` is the
identifier wikilinks resolve against, and gives way to the filename when the
two disagree (ADR 0001).
_Avoid_: memory item, note, record

**Knowledge unit**:
One Markdown document in the curated layer, carrying identity, an evidence
state, and optional anchors separated from provenance. Its frontmatter is the
base contract plus whatever the project's own declared extension adds.
_Avoid_: unit of knowledge, article, doc

There is deliberately **no umbrella term** covering both. They share neither
frontmatter, nor relations, nor the way each stops being true, so a single word
for both would hide three differences at once.

### Ceasing to be true

**Supersession**:
The relation that retires a fact by naming what replaces it. In the memory
layer it is written on the retired entry, by rewriting its `description` to
`superseded by [[name]]`; in the curated layer it is written on the replacing
unit, as `supersedes`, and one unit may supersede several.
_Avoid_: deletion, removal, archiving

**Successor**:
The memory entry or knowledge unit that a superseded one points at. It always
exists and is always a different one: supersession is a relation between two
records, never a flag on one.

Nothing is ever deleted, and there is **no obsolescence state**: this project's
language cannot say "this is no longer true" on its own, only "this is replaced
by that". A fact that simply stopped holding is retired by writing a successor
that records the change, and superseding the old one onto it.

**Repair**:
Correcting a record that was written wrong — a wikilink that resolves to
nothing, an index entry with no file, a duplicate `name`, a field outside its
domain. A repair never changes what a fact says; only what the world says
changes a fact, and that is supersession. The two are not interchangeable, and
the boundary between them is exactly what `lint` can already point at: if `lint`
cannot name it, it is not a repair.
_Avoid_: fix, edit, correction

### Proof

**Evidence state**:
How a knowledge unit is known: `measured`, `verifiable`, or `hypothesis`.
Declared by the author; not inferred.

**Anchor**:
The external thing a knowledge unit's claim depends on, named so it can be
re-checked later. Kept separate from provenance, which records where the claim
came from.

**Verdict**:
What a freshness probe returned for an anchor: `current`, `drifted`, or
`unknown`. Ternary and fail-explicit — a probe that could not answer says so
rather than guessing.

### Where memory lives

**Adopter project**:
A repository that has run `init`: it holds the Markdown data and configuration,
while all code stays in the plugin.

**Harness memory location**:
The fixed path outside the project where Claude Code expects to read a
project's agent memory. The plugin makes it a symlink into the project, so the
data stays versioned in the repo while the harness reads it where it always
did.
