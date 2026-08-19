---
name: check-the-licence-before-you-copy
description: Use before pulling someone else's code, skills, prompts or configuration into your project, and before publishing anything that contains them. Turns "it was on GitHub" into an obligation you can actually meet.
---

# Check the licence before you copy

Most permissive licences ask for one thing in return: **say where it came from.**
That is a small price, and it is broken constantly — not out of bad faith, but
because attribution is added once and then quietly erased by the next rename,
refactor or repackaging.

🔴 **Attribution is not a courtesy. It is the condition under which you were
allowed to have the code.** Publish MIT-licensed work without its notice and you
are distributing it without a licence.

## When to use this

- Copying a file, a skill, a prompt, a config or a snippet from another project
- Vendoring a dependency instead of installing it
- Publishing something that contains any of the above
- Renaming, moving or repackaging a project that already carries third-party work
- An agent produced code that looks suspiciously like a known library

## The procedure

**1. Find the licence before you copy, not after.** If there is no `LICENSE`
file, no SPDX header and nothing in the README, you have **no** licence — not a
permissive one. "Public repository" is not a licence. Ask, or do not copy.

**2. Read what it actually requires.** For the common permissive ones it is short:

| Licence | What you must do to redistribute |
|---|---|
| MIT / BSD / ISC | Keep the licence text **and** the copyright line |
| Apache-2.0 | The above, plus keep `NOTICE` if there is one, and state changes |
| MPL / LGPL | Above, plus keep the covered files' source available |
| GPL / AGPL | The whole work becomes copyleft — think before, not after |
| CC BY / CC BY-SA | Credit the author; SA also forces the same licence onward |
| No licence at all | You have no right to redistribute. None. |

**3. Put the attribution in three places, because one is not survivable.**

- The **licence text**, verbatim, in a `LICENSES/` directory. Never summarised.
- A **third-party section in `NOTICE`**, saying what came from where.
- A **line in each file** you took, naming the origin and the copyright holder.

One place is enough legally and useless practically. The file-level line is the
one that survives a rename; the `NOTICE` is the one a lawyer reads; the licence
text is the one the licence actually demands.

**4. Write a test that fails if the attribution disappears.** This is the step
everyone skips, and it is the only one that holds. Assert that the licence file
still exists, that the notice still names the origin, and that every adapted file
still carries its copyright line.

**5. Say what you changed.** If you renamed, adapted or trimmed, say so in the
same breath as the credit. "Adapted from X, renamed for searchability; the method
is theirs" costs one sentence and removes any question of passing it off.

**6. When in doubt, leave it out.** Material tied to someone's personal workflow,
their own products or their identity should not be genericised into your project.
Omitting it is respectful; laundering it is not.

## Anti-patterns

- **Attribution only in the commit message.** Nobody reads git history to find
  out who owns what, and a squash erases it.
- **"We rewrote it enough."** If you started from their file, you adapted it. The
  test is where you started, not how much is left.
- **A licence summary instead of the text.** The licence says *this text*. Your
  paraphrase is not it.
- **Adding the notice at publication time.** By then the file has been renamed
  twice and nobody remembers which parts were foreign.

## The incident

A collection of 44 skills was published where 23 came from an MIT-licensed
project. The attribution went into all three places, and a test was added that
fails if any adapted file loses its copyright line.

That test was not paranoia. Between adding the attribution and publishing, the
project was renamed twice, every skill was renamed once, and the files were moved
with `git mv`. Each of those steps rewrites paths and touches file contents. A
single-place attribution would have had several chances to be lost silently, and
nobody would have noticed until the original author did.

The README also states, in writing, that the material comes out the same day if
the original author would rather it were not redistributed. **An offer to remove
it costs nothing and changes the conversation from a dispute into a request.**

## Related

- [`review-code-you-did-not-write`](../review-code-you-did-not-write/SKILL.md) —
  the code arrived from outside; the licence is only half of what to check
- [`verify-before-saying-done`](../verify-before-saying-done/SKILL.md) — an
  attribution nobody tested is an attribution that will be gone
- [`document-with-evidence`](../document-with-evidence/SKILL.md) — record where
  it came from as a fact with a source, not as a memory
