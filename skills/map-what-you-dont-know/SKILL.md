---
name: map-what-you-dont-know
description: Use when documenting a system or auditing what is already documented. Records the edge of what is known, so that silence stops reading as "nothing there".
---

# Map what you don't know

A body of documentation that only states what it knows produces a specific,
expensive illusion:

> **Everything not written down is either unimportant or does not exist.**

Neither is true. What is not written down is usually the part nobody understood
well enough to write. The gaps are not the leftovers of the documentation
effort — they are its most actionable output.

So record them. Deliberately, in the repository, with the same care as the
facts.

## When to use this

- Documenting a system for the first time
- Migrating loose notes into a structured knowledge base
- Onboarding onto something someone else built
- Answering "what do we actually know here?" before a risky change
- Any time you catch yourself writing "presumably" or "I assume this is"

## The procedure

### 1. Give the gaps a home

A list of unknowns kept in your head, or in a session that ends, is not a map.
It needs a file that lives with the documentation and is read at the same time.

### 2. Write each gap as a question, not as a feeling

🔴 **If you cannot phrase it as a question with a possible answer, it is not a
gap — it is unease.** Unease belongs in prose; gaps belong in the list.

| Not a gap | A gap |
|---|---|
| "The networking side is murky" | "Which component terminates inbound connections before they reach the application?" |
| "Storage worries me" | "What is the retention policy on the archive volume, and who set it?" |
| "Nobody understands the scheduler" | "What triggers the nightly run, and where is its schedule defined?" |

### 3. Say what the gap blocks

A gap with no consequence attached will never be closed, and should not be.
Write the decision that is waiting on it: *"blocks: whether this can be
restarted during business hours."*

Gaps that block nothing go in a low-priority section, or nowhere. A gap list
that grows without bound stops being read, which makes it worse than no list.

### 4. Prove the gap — searching and **not finding** is the evidence

This is the part that turns a gap list into something with the same standing as
the rest of the documentation. Record what you looked at and came back
empty-handed from:

```
Searched: the runbook directory, the configuration repository, the ticket
history for the last two years, the service's own inline comments.
Found: no description of what consumes this endpoint.
```

⚠️ **A negative result only counts if the search could have returned a
positive.** Before trusting "not found", run the same search for something you
know is documented. If that also comes back empty, you have measured your search,
not the documentation. See `read-an-unfamiliar-system` for how this fails
silently.

### 5. Name who could answer it

Most real gaps do not close by reading harder. They close by asking a person —
whoever built it, whoever operates it, whoever pays for it. Recording *who* turns
a gap from a research task into a five-minute conversation someone can actually
have.

If the honest answer is "the person who knew has left", write that. It is one of
the most decision-relevant facts a system can carry.

### 6. Close a gap only by covering it

A gap leaves the list in exactly two ways:

1. **It is answered** — and the answer becomes a normal documented fact, with its
   own evidence, linked from where the gap used to be.
2. **It is declared unanswerable** — "nobody knows; here is the decision we made
   anyway, and here is what we will do if that decision turns out wrong."

🔴 **It never leaves because it got old, or because the list got long, or because
nobody enjoyed looking at it.** A gap list is only worth reading if it is true,
and silently dropping entries is how it stops being true.

### 7. Re-check the list on a schedule

Gaps close by accident. Someone documents the thing in passing, a system is
retired, an owner is finally identified. A stale gap list sends people to
research questions that were answered months ago, and they stop trusting it after
the second time.

## Real case — seven services nobody could account for

A body of documentation of roughly 4,700 lines was being converted into a
structured knowledge base. The work was expected to be mechanical: read, split,
classify, cross-link.

The conversion produced something nobody had asked for. Once every claim had to
declare what it applied to, **seven services running in production had no source
describing them at all.** Not badly described — absent. No note said what they
were, what they did, or who they served. They had simply never been written down,
and in 4,700 lines of confident prose their absence was invisible.

They could not be resolved by reading. They needed someone to be asked.

**What this teaches:** the gaps were always there. What the structure did was
make the *silence* visible. Prose hides absence perfectly — nothing in a document
signals the paragraph that was never written. A list of open questions is the
only place absence can show up as an item.

## Real case — the fossil that never said it was a fossil

Two documents in the same repository described the same subsystem and disagreed
about which component handled a job. Both were internally consistent. Both were
written with total confidence. Neither carried a date, so there was no way to
tell which one was older, let alone which was current.

One of them described a system that had been switched off. It was not wrong when
it was written. It became wrong afterwards, and there is no mechanism by which a
document notices that.

**A fossil document is worse than a missing one.** A missing document sends you
to ask someone. A fossil answers your question, confidently, with the wrong
answer, and stops you asking.

Two rules came out of it:

- ⚠️ **Every document records when it was last confirmed true**, not when it was
  written. Those are different dates and only one of them is useful.
- ⚠️ **Contradictions are recorded, not resolved by picking the nicer one.** Two
  sources disagree, both are cited, the verdict is *unresolved*, and it goes in
  the gap list with the question that would settle it.

## The entry shape

```markdown
### GAP — <the question, as a question>

**Blocks:** <the decision that is waiting on this>
**Searched:** <where you looked>
**Found:** nothing / <the partial thing you found and why it is not enough>
**Could answer this:** <role, team, or "the person who knew has left">
**Opened:** <date> · **Last re-checked:** <date>
```

And for a conflict:

```markdown
### CONFLICT — <what the two sources disagree about>

**Source A says:** <claim> (<where>, last confirmed <date or "never">)
**Source B says:** <claim> (<where>, last confirmed <date or "never">)
**Verdict:** unresolved
**Would settle it:** <the observation that decides it>
```

## Traps

🔴 **Do not fill a gap with a plausible answer.** The moment a guess is written
in the same voice as the facts, the gap is gone and the guess is permanent. If
you must record a belief, record it as a belief, clearly labelled, with what
would confirm it.

🔴 **"Undocumented" and "unimportant" are unrelated.** The seven unaccounted-for
services above were in production, serving something, costing something.

⚠️ **Do not let the gap list become a wish list.** "It would be nice to have a
diagram" is not a gap. A gap is a question whose answer changes a decision.

⚠️ **The uncomfortable gaps are the valuable ones.** Whatever you would rather
not write down because it makes the documentation look incomplete is exactly the
entry someone needs before a risky change.

⚠️ **Do not close a gap with a link to somewhere the answer *should* be.** Either
the answer is there and you read it, or the gap is open.
