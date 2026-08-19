---
name: write-the-rollback-plan-first
description: Use before applying any change that can break something. The way back is written and tested before the change, not improvised after it.
---

# Write the rollback plan first

**The moment you need the rollback is the moment you are least able to write
one.** Something is down, people are asking, and the person who understood the
change is the one now typing under pressure. Whatever gets improvised then will
be worse than what you could have written calmly ten minutes earlier.

So it gets written earlier. Before the change, not after. And it gets checked,
because an untested rollback is a belief, not a plan.

> **No written way back, no change.** That is the rule, and it holds even when
> the change is small — especially then, because small changes are the ones that
> skip the step.

## When to use this

- Any change to a running system
- Anything touching stored data
- Anything you reach *through* the thing you are changing
- A migration, a version bump, a config replacement, a credential rotation
- Whenever you catch yourself thinking "we can always put it back"

## Step 1 — Classify the change before you write anything

Three categories, and they demand different amounts of preparation.

| Category | Meaning | What it needs |
|---|---|---|
| **Reversible** | You can return to the previous state completely | A written undo, and proof the thing it depends on exists |
| **Partial** | Service comes back, but something is gone for good | The undo, **plus** an explicit list of what is not coming back |
| **Irreversible** | There is no return | A different plan shape entirely — see step 6 |

⚠️ **Most changes people call reversible are partial**, and the difference is
discovered during the incident. Restoring a database from a copy taken this
morning is not a return to the previous state — it is a return to this morning,
and everything since is gone. Restarting a service to load an old configuration
loses in-flight work and open sessions. Rolling back a schema change may restore
the structure and not the rows.

**Ask directly: what does this undo NOT bring back?** Sessions? Queued jobs?
Audit history? Anything written between the change and the rollback? Write the
answer down. It is the single most useful line in the whole plan, because it is
what someone has to accept before pressing the button.

Irreversible in practice: deletions, one-way data transformations, sending
messages to real people, moving money, publishing something, rotating a
credential you need in order to get back in.

## Step 2 — Write it as commands, with real values

"Restore the backup and restart" is not a rollback. It is an intention. It
contains no path, no name, no order, and it will be read by someone tired.

A rollback is:

- The exact commands, in order
- The exact path to the copy — the one you verified in step 3
- The service actions that follow, and in which order
- The check that tells you the rollback worked, which must be able to fail

If it fits in one command, make it one command. Ten steps at three in the
morning is nine opportunities to skip one.

## Step 3 — Verify what the undo depends on

🔴 **A copy nobody has opened is not a copy.** It is a file of unknown content
that makes everyone feel safer than they are.

Verifying means reading back **from the copy itself**: list the objects inside
the export and count them; open the saved configuration and confirm the section
you are about to change is present in it; count the entries in the archive rather
than on disk.

The same applies to every other dependency of the undo:

- ⚠️ **"We can redeploy the previous version"** assumes the previous artefact
  still exists somewhere and is still retrievable. Mutable version labels get
  overwritten; storage gets cleaned up; a build that succeeded last month may not
  succeed today. Confirm you can actually obtain it — now, not then.
- ⚠️ **"We can put the old config back"** assumes you have the old config.
  Capture it first, as a file, not as scrollback.

## Step 4 — Check the undo can run at all

You are not applying it. You are confirming it is not broken:

- Run whatever syntax or dry-run mode exists for it
- Confirm every path in it resolves
- Confirm the credentials it uses still work
- Read it out loud once, in order, as if the system were down

⚠️ **A rollback script whose first execution ever is during the incident is not a
rollback.** It is a script, and you are about to find out whether it works at the
worst possible time.

## Step 5 — Time it, and compare against the outage

If restoring takes four hours and the failure it protects against causes a
thirty-minute outage, the rollback is not available to you in practice. Nobody
starts a four-hour restore while a service is down; they improvise instead, which
is the situation the plan existed to prevent.

An undo that is too slow to use means the **change** needs a different shape:
smaller scope, one node first, a version that can run alongside the old one, a
switch that flips back instantly.

## Step 6 — Put the irreversible part last, and smallest

If a sequence contains an irreversible step, everything reversible goes before
it. That way each stage can be abandoned cheaply and the point of no return
arrives once, late, with everything else already proven.

And at that point, the plan is no longer "how do we undo this". It is:

- What is the **forward** recovery? If we cannot go back, what do we do instead?
- Who decides to proceed, and against what evidence?
- What is the smallest version of the irreversible act that still moves us
  forward — one tenant, one table, one record?

## Real case — the rollback that was never used and was the point anyway

A change to how stored credentials were validated. Total failure mode: if
migrated credentials stopped validating, **nobody could log in** — including the
people who would have to fix it. There is no more locked-out shape than that.

Before anything was applied, three things existed:

1. A **single-command** way back. Not a procedure. One command.
2. A copy whose contents had been **listed and counted**, not merely taken.
3. Confirmation that the rollback command was syntactically sound and every path
   in it resolved.

The change was then rehearsed cold against a copy, and the rehearsal turned up a
side effect that was not on the risk list. The change was stopped. It was never
applied, so the rollback was never used.

The rollback was still the thing that produced the outcome. With a way back
prepared, the rehearsal could be read for what it actually showed instead of for
permission to proceed — and the discussion about stopping was a calm one, because
stopping cost nothing and continuing had a known floor. **The value of a written
undo is mostly delivered before anything goes wrong: it is what lets you make the
decision on the evidence rather than on the fear.**

## Real case — the rollback that pointed at nothing

A change plan had a rollback section. It named a restore command and a path to
the nightly copy. It had been reviewed and it read as complete.

Reviewed properly — by opening the path — the newest copy at that location was
**eleven days old**. The job producing it had been failing, and its failures went
somewhere nobody read. The plan was correct in form and empty in substance: the
command was right, and the thing it restored from did not exist.

⚠️ **A rollback is only as real as the artefact behind it, and the artefact is
only real if you looked at it today.** Reviewing a rollback means resolving every
path in it, not reading it for plausibility.

## The shape

```markdown
## Undo plan — <the change>

**Category:** reversible / partial / irreversible
**Does NOT restore:** <sessions, in-flight jobs, anything written since, nothing>

**Commands, in order:**
1. `<exact command with real paths>`
2. `<service action>`

**Depends on:** <copy at <path>, listed <date>, N objects>
**Rehearsed:** <syntax check / dry run> → <output pasted>
**Takes:** ~<minutes>
**Rollback worked when:** <a check that could fail>
**Second way in if this locks me out:** <console, out-of-band path, timed auto-revert>
```

## Traps

🔴 **No written undo, no change.** Including for the small one. Including under
time pressure — pressure is when improvisation is worst.

🔴 **Never let the undo path run through the thing you are changing.** If you are
changing authentication, routing, the firewall, or the proxy carrying your own
session, the way back must not depend on any of them. Arrange a second route
*before* you type the command: a console, an out-of-band path, or a mode that
reverts automatically unless you confirm within N seconds.

⚠️ **"It's just a config change" is where this gets skipped**, and config changes
are the most common cause of the outage you cannot log in to fix.

⚠️ **The undo is part of the handoff.** If you stop mid-sequence, the next person
must be able to go back without reconstructing anything — see `write-a-handover-that-works`.

⚠️ **Do not confuse a rollback with a fix.** Going back is how you buy time to
understand. Understanding first, while the system is down, is how a
thirty-minute outage becomes a four-hour one.

---

See `deploy-to-production-safely` for the full sequence the undo plan sits inside.
