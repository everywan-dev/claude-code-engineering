---
name: keep-secrets-out-of-the-repository
description: Use before committing configuration, when a secret has already been committed, or when adding a secret scanner. Covers why rotation beats scrubbing and why most scanners get switched off.
---

# Keep secrets out of the repository

Two facts do most of the work here.

**A secret that reached a repository is compromised, not "at risk".** Clones,
forks, CI caches, backups, editor histories and mirrors all copied it while you
were deciding what to do.

**Rewriting history does not undo that.** It makes the repository look clean,
which is a different thing, and an actively dangerous one if it lets you skip the
step that matters.

🔴 **Rotate first. Scrub second, if at all.** The scrub is cosmetic; the rotation
is the fix. Doing them in the other order means the credential is still valid
while you are busy tidying.

## When to use this

- You are about to commit a config file, an `.env`, a compose file, a notebook
- A secret is already committed, in history, or was pasted into an issue or chat
- You are adding or fixing a secret scanner
- A token was shared to unblock someone and never revoked
- A test fixture contains "a fake key" that is not fake

## If one is already committed

**1. Rotate it. Now, before anything else.** New credential issued, old one
revoked at the source. Until that is done, everything else is theatre.

**2. Check whether it was used.** Access logs at the provider, not guesses. A
rotation without a look at the logs answers "can they still get in?" but not
"did they?".

**3. Only then decide about history.** Rewriting is expensive: it changes every
commit id, breaks every open branch and fork, and requires a force-push that
everyone must recover from. It is worth it for a public repository. It is often
not worth it for a private one where the credential is already dead.

**4. If you do rewrite, say so.** People with clones need to know their history
diverged and how to recover. A silent force-push turns one incident into several.

## Preventing the next one

**Keep the shape of a secret out of the file, not just the value.** A
`config.example` with `PASSWORD=changeme` teaches the pattern; a real file
committed once teaches nothing but costs everything.

**Environment or a manager, never the repository.** If the deployment needs it,
the deployment supplies it. The repository holds the *name* of the variable, and
that is all.

**Add a scanner — and read the next section before you do.**

## Why most scanners get switched off

A scanner that fires on things that are not secrets gets disabled within a week,
and then you have no scanner and a false sense of having one.

Three failure modes, in the order they actually happen:

| Failure | Why it happens | Fix |
|---|---|---|
| **It reports itself** | Its own pattern list contains example secrets | Build the patterns at runtime from parts; never store a literal example |
| **It flags every long string** | Entropy heuristics on code, not config | Restrict entropy rules to config files; require a recognisable prefix elsewhere |
| **It flags the code that reads the secret** | `TOKEN = os.environ.get("TOKEN")` looks like an assignment | Require plausible secret *material*, not just the word |

The first one is the one to watch for, because it fails permanently and looks
like a bug in the scanner rather than in its design.

## Anti-patterns

- **"It's only in a private repo."** Private today. Contractors, forks, an
  accidental visibility change, an acquisition.
- **"It's a low-value key."** Then it is cheap to rotate. Rotate it.
- **Scrubbing and calling it fixed.** The credential is what matters, not the
  file.
- **A test fixture with a real value** because "the test needs a realistic one".
  It needs a *well-formed* one, which is not the same thing.

## The incident

A repository received a routine commit that included configuration with live
credentials. It was caught, the history was rewritten with a history-rewriting
tool and force-pushed, and the repository was clean afterwards.

The part worth remembering is what the clean repository did **not** change: for
the entire window between commit and rotation, the credentials were valid and had
been distributed to every clone and CI cache. The scrub made the evidence
disappear, not the exposure.

Separately, a secret scanner added to the same organisation failed on its very
first run — on itself. Its pattern list contained example prefixes, so it
detected its own source. Fixed by requiring plausible material after a prefix,
restricting entropy checks to configuration files, and assembling the control
strings at runtime so the file never contains one.

## Related

- [`validate-your-validator`](../validate-your-validator/SKILL.md) — the scanner
  that incriminated itself, in full
- [`write-the-rollback-plan-first`](../write-the-rollback-plan-first/SKILL.md) —
  a history rewrite needs a recovery path written before the force-push
- [`map-the-attack-surface`](../map-the-attack-surface/SKILL.md) — where the
  credential could be used, once you know it leaked
- [`review-code-you-did-not-write`](../review-code-you-did-not-write/SKILL.md) —
  generated config files are a common way secrets arrive
