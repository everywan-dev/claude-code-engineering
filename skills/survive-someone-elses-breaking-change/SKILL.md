---
name: survive-someone-elses-breaking-change
description: Use when something that worked yesterday stopped working and you changed nothing, or before upgrading a dependency, runtime or platform. Also covers not doing this to your own consumers.
---

# Survive someone else's breaking change

"We changed nothing" is usually true and never relevant. You are standing on a
stack of other people's decisions, and any of them can move.

The distinctive feature of this failure class is that **the error message
describes your side, not theirs.** You get a 404, a cryptic code, an empty
result — symptoms of your own request being wrong, when what changed is what the
other side accepts.

🔴 **When something breaks with no change on your side, stop debugging your code
and start dating the change.** What moved, and when? That question resolves this
class of incident faster than any amount of reading your own diff.

## When to use this

- It worked yesterday, nothing was deployed, it fails today
- After any upgrade: dependency, runtime, base image, platform, browser
- An error code you have never seen and cannot find documented
- A vendor announced a deprecation and you are not sure it affects you
- You are about to change something other people consume

## Diagnosing it

**1. Establish what moved, with a timestamp.** Deployment logs, image digests,
package lockfile diffs, the vendor's changelog and status page, an auto-update
you forgot was enabled. Something has a new date on it.

**2. Suspect the negotiated layer.** Most of these live where two sides agree on
a version at runtime: API versions, protocol versions, TLS versions, feature
flags, image tags that moved. Both sides are individually correct; the
*negotiation* is what broke.

**3. Reproduce with the old and new version side by side.** One variable. If you
cannot pin the old version to compare, that is the first thing to fix, and it is
also the answer to how you avoid the next one.

**4. Search for the symptom, not the cause, and expand the search.** If there is
nothing on the internet about your error, consider that you may be in a rare
configuration — an old setting, a fossil default, something inherited from a
migration. Rare configurations are where undocumented breakage lives.

**5. Fix at the boundary, not everywhere.** Pin, adapt or shim at the one place
the two systems meet. Spreading the workaround through the codebase turns one
vendor's decision into your permanent architecture.

## Preventing it

- **Pin what you depend on**, and know how to unpin. Floating tags are how "we
  changed nothing" becomes literally false.
- **Read the deprecation notice when it arrives**, not when it fires. Write the
  date somewhere that will page you before it.
- **Test the upgrade path**, not just the current state.
- **Keep a recorded snapshot of the working negotiation** — the versions both
  sides agreed on when it last worked. That capture is what makes the comparison
  in step 3 possible at all.

## Not doing it to others

The same failure, seen from the other side:

- **Additive changes are safe; removals and redefinitions are not.** New optional
  field, fine. Same field meaning something else, not fine.
- **Version the contract, not just the code.** Consumers need a way to say which
  behaviour they were built against.
- **Deprecate loudly and long.** Announce, warn in the response, then remove.
- **Assume your consumers include one you have never heard of**, running a
  configuration you would not have predicted, who will find out by breaking.

## Two incidents

**A reverse proxy started returning 404 for everything.** Nothing on either side
had been redeployed. The proxy required a minimum container-API version to read
its service definitions; a platform upgrade had moved the negotiated version
below that line. The proxy was correct, the platform was correct, and the
routing table it built was empty. The error surfaced as "route not found" —
perfectly describing the symptom and pointing nowhere near the cause.

**A vendor changed an authentication feed and clients broke with an opaque error
code.** There was almost nothing about it online, which was itself the clue: the
break only affected an option that had been the default years earlier and was
still set on machines whose profiles predated the change. Everyone on a current
default was unaffected. **"No search results" was evidence of a fossil
configuration, not of a unique problem.**

## Related

- [`root-cause-analysis-first`](../root-cause-analysis-first/SKILL.md) — resist
  the first explanation that fits; this class attracts them
- [`debug-a-silent-failure`](../debug-a-silent-failure/SKILL.md) — when the
  breaking change produces no error at all
- [`document-with-evidence`](../document-with-evidence/SKILL.md) — capture the
  working versions now, so the comparison exists later
- [`detect-stale-documentation`](../detect-stale-documentation/SKILL.md) — a
  probe that re-runs the check tells you the platform moved before a user does
