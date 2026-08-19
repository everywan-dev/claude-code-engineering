---
name: hand-off-work
description: Use when work has to survive a break in continuity — end of a session, end of a day, passing a task to someone else. Writes the handoff that carries the evidence and names what was never checked.
---

# Hand off work

The next session starts blind. It gets your files and none of your head. Whatever
you did not write down was not saved — it was forgotten, in a way that looks
exactly like it never happened.

So the handoff has one job:

> **Let the next session act without re-deriving anything, and without trusting
> anything you did not check.**

Those are two separate promises. Most handoffs keep the first and quietly break
the second.

## When to use this

- A task will not finish before the session ends
- You are stopping mid-sequence — applied, not yet verified
- Someone else is picking this up
- You are about to hit a context limit and the work is long

## The five sections

Everything else is optional. These five are not.

### 1. Starting state — captured, not remembered

The output you took **before** you touched anything: the process list, the
version in use, the row count, the routing table. Raw, pasted.

This is not for the change. It is for the argument three days later about
whether the change caused the thing that broke. Without it, that argument has no
winner.

### 2. Verified — each claim with the check and its output

One line per claim, and each line carries the command and what it printed.

```
- New route answers on all three nodes — `<per-node request>` → 200, body contains the new build id (pasted below)
```

If you cannot attach an output, the claim does not belong in this section. Move
it down one.

### 3. NOT verified — the section everyone skips

🔴 **This is the most important part of the handoff and it is the one that gets
left out.** It is also the only section whose absence is invisible: a handoff
with no "not verified" list reads like a handoff where everything was checked.

Every claim you believe but did not observe goes here, with **how to check it**:

```
- I believe the workers reconnected after the restart — not observed.
  Check: enqueue one job and read the consumer's own log line.
```

An empty "not verified" section is a claim in itself, and it is almost always
false. If yours is empty, you have not sorted the list yet.

**The sorting test.** For each sentence you are about to write, ask:

> What did I run that, if this were false, would have printed something
> different?

- There is an answer → section 2, and paste the answer.
- There is no answer → section 3, and write the check you did not run.

"It should work", "it looked fine", "the config is valid", "nothing errored" —
all of these are section 3. They describe your expectations, not the system.

### 4. The rollback, ready right now

Not "restore the backup". The exact commands, the exact path to the copy you
**listed the contents of**, and the restart that follows. Plus how long it takes
and what it does not restore.

If you stopped mid-sequence, the next session's most likely first decision is
whether to go forward or back. Make both options equally available.

### 5. Traps found on the way

The things that cost you time and would cost the next person the same time
again. A tool that has to be run from a particular working directory. A flag
that is silently ignored. A name that resolves to the wrong host from inside the
network. A step that must be repeated because it does not take on the first
attempt.

This is the highest-value content in the whole document, per word.

## What to leave out

⚠️ **Your reasoning.** How you narrowed it down, what you ruled out first, the
three hypotheses that were wrong. It feels valuable because it was expensive.
It is not valuable to the reader: reasoning is the cheapest thing to regenerate
and the most expensive thing to read.

Keep the **conclusions**, the **evidence**, and the **traps**. Drop the path you
walked to get there. The exception is a hypothesis someone is likely to re-try:
then one line — *"not the disk; checked, ruled out"* — which is a fact, not a
narrative.

⚠️ **Raw scrollback.** A dump of everything that scrolled past is not a handoff.
It shifts your reading work onto the next person and adds nothing.

## Real case — "pushed to all nodes"

A fleet-wide change was handed over half-finished. The note said: *"config pushed
to all nodes."* The next session, reasonably, treated that as done and moved on
to the dependent step, which failed in a way that pointed nowhere useful. Half a
day later: two nodes had rejected the push, and the per-node result had scrolled
past unread in the previous session.

Nobody lied. The push **had** been issued to all nodes. It had not been
**confirmed applied** on any of them. Those are two different sentences, and the
handoff contained the wrong one.

With a "not verified" section, the same author would have written: *"pushed to
all three nodes; confirmed applied on none — check with `<per-node query>`."*
That is a different handoff, and it produces a different next action in the first
minute.

## Real case — two thousand words, one missing line

A handoff for a long-running migration ran to about two thousand words of
careful reasoning: why this approach, what was considered, the shape of the data.
The next session read all of it, then spent forty minutes rediscovering the one
thing that decided the outcome — the tool writes to the wrong location unless it
is invoked from a specific directory.

That line was in nobody's notes because it did not feel like knowledge. It felt
like an annoyance. **Annoyances are the highest-yield thing in a handoff;
reasoning is the lowest.**

## The template

```markdown
# Handoff — <task>

**Goal:** <one sentence: what "done" looks like>
**Where I stopped:** <which step of the sequence, and whether it was applied>

## Starting state (captured before touching anything)
<raw output>

## Verified
- <claim> — `<command>` → <output>
- <claim> — `<command>` → <output>

## NOT verified
- <claim I believe but did not observe> — check with: `<command>`
- <claim I believe but did not observe> — check with: `<command>`

## Rollback, available right now
<exact commands · path to the verified copy · how long it takes>
**Does not restore:** <sessions / in-flight work / history / nothing>

## Traps found
- <the thing that will cost an hour if rediscovered>

## Next action
<the single next command or decision, not a list of options>
```

## Traps

🔴 **A handoff with no "not verified" section is not a short handoff, it is a
wrong one.** The reader will treat every sentence in it as observed.

🔴 **Do not upgrade a belief on the way out.** Under time pressure, "I think the
service came back" becomes "service restored" in the write-up. That single word
change is how an unchecked claim enters the record as a fact and stays there for
months.

⚠️ **Say where things are.** The copy, the branch, the file you edited, the
window still holding an open session. A handoff that describes work but not its
location makes the next session re-find everything.

⚠️ **One next action, not a menu.** If you leave three options, the next session
spends its first stretch re-deciding what you already decided.

⚠️ **The handoff is written while you still have the outputs.** Written from
memory afterwards, section 2 collapses into section 3 — which is correct, but
you have thrown away evidence you actually had.
