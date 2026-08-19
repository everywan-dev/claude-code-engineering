---
name: trace-a-silent-failure
description: Use when something did not happen and nothing complained — no error, no alert, an empty log, a change with no effect. Teaches how to read absence as a symptom and where silence gets manufactured.
---

# Trace a silent failure

Most outages announce themselves. The expensive ones do not.

The signature is always the same shape: **the thing that should have happened
did not happen, and no layer said anything.** No stack trace, no non-zero exit,
no alert. Just an absence — and absence does not page anyone.

🔴 **In this class of failure, the silence IS the symptom.** Stop waiting for an
error to appear. Start asking which component should have complained, and why it
did not.

## When to use this

- "It should be running" and it is not
- A change was applied and had no visible effect
- A log stopped — not errors, everything
- A job, a report, a sync did not produce output and nothing failed
- Something was broken for days and nobody noticed
- A count is zero and nobody knows if zero is correct

## The procedure

**1. State the missing event precisely.** "The nightly export did not appear."
Not "exports are broken". You are about to walk a chain, and you need to know
what you are looking for at each link.

**2. Walk the chain backwards, from the missing output to the trigger.** At each
link ask two questions:

- Did this link run at all?
- If it ran and failed, **would anything have recorded that?**

The second question is the one that finds it. Silent failures live at the link
where the answer is *no*.

**3. Look for the layer that swallows.** Something is converting a failure into a
non-event. Usual suspects, in order of how often they are the answer:

| Swallower | What it turns into silence |
|---|---|
| A success exit code on a failed operation | The supervisor sees a clean finish and does nothing |
| A restart policy scoped to failures only | A process exiting cleanly is never brought back |
| A cache in front of the broken thing | Health checks keep passing off stale content |
| A transformation applied in the wrong order | The later step matches nothing and reports success |
| An event that never crosses a boundary | One node acts, the others never hear |
| Configuration that produces zero work | Nothing runs, nothing fails, nothing is reported |

**4. Count things. Do not eyeball them.** How many jobs ran? How many rows
changed? How many nodes reloaded? Silent failures survive on unexamined zeroes.
`0` looks exactly like `0` whether it is correct or catastrophic.

**5. Check every replica individually.** Not through the shared name. Compare
them against each other — divergence between identical nodes is the cheapest
silent-failure detector there is.

**6. Fix the silence as well as the fault.** If you only fix the fault, the next
one of these is also invisible. Add the check that would have caught it, and
make it assert a **positive quantity**: "at least one export exists, newer than
24 hours", not "the export step exited 0".

## Real cases

> **The restart policy that respects a clean exit.** A supervisor was configured
> to restart containers *on failure*. A database container hit a condition where
> it shut itself down and exited with code **0** — a clean, deliberate,
> successful-looking exit. The policy read that as "the work is finished" and did
> exactly what it was told: nothing.
>
> The service stayed down for **four days**. The front end kept returning 200
> the whole time, because the page people checked was static and cached. Two
> silences stacked on top of each other, and each one alone would have been
> enough.

> **The transformation in the wrong order.** A pipeline compressed its output
> before a later step rewrote content inside it. The rewrite ran against
> compressed bytes, matched nothing, changed nothing, and reported success —
> there is no error condition for "your pattern did not appear". Everything was
> green. The content was simply never rewritten, for months.
>
> A rewrite that matches nothing should be loud. Assert the number of
> replacements, and fail on zero.

> **The event that did not cross the boundary.** Configuration lived on a shared
> filesystem mounted by four nodes. A change written from one node was picked up
> by that node immediately. The other three never noticed: the shared filesystem
> did not propagate change notifications to other clients, and the watchers were
> waiting for a notification that would never arrive.
>
> One node in four had the new config. Nothing errored. Requests were served
> correctly or incorrectly depending on which node received them, which is the
> hardest kind of bug to reproduce and the easiest to dismiss as a fluke.
>
> ⚠️ **Never assume a file watcher works across a network filesystem.** Poll, or
> reload explicitly, and verify **per node**.

> **The build that failed before it started.** A CI job began failing with
> nothing useful in the output. The runner had two replicas on the same host,
> both using the same build directory. They stepped on each other while
> preparing the workspace, so the failure happened *before any of the pipeline's
> own commands ran* — which is precisely why the log had nothing in it about the
> pipeline.
>
> When a log is empty, ask whether the thing that writes it ever got to run.

> **The pipeline with zero jobs.** A CI configuration produced **no jobs at
> all** — every job's conditions excluded it. The run reported no failures,
> because there was nothing to fail. It was read as a pass for two weeks.
>
> Zero jobs is a configuration error, not a runner problem, and it should be
> treated as red. Any "success" that involved doing nothing is not a success.

## How to make silence loud

Turn each of these into a habit and this whole class of failure gets much
smaller:

- **Assert quantities, never just exit codes.** *N* files produced, *N*
  replacements made, *N* rows updated. Fail on zero unless zero is explicitly
  expected.
- **Give every recurring job a freshness check.** Not "did it fail" — *"is the
  output newer than the interval"*. Absence of a failure is not presence of a
  result.
- **Health-check something only the working system can produce.** A real query,
  a computed value, an authenticated call. Never a page that can be served from
  a cache.
- **Alert on the disappearance of a signal**, not only on bad values. A metric
  going flat and a metric going to zero look identical on most dashboards and
  mean completely different things.
- **Compare replicas.** Identical nodes that disagree are telling you something
  before any user does.

## Traps

🔴 **A clean exit code is not a completed job.** Plenty of software exits 0 on
its way out of a fatal condition. Check what it produced, not how it left.

🔴 **"No errors in the log" is not evidence of health** when the process writing
that log may not have started. Check the log's own last-write time first.

⚠️ **A cache anywhere in the path invalidates your health check.** Content
delivery, proxy, browser, application cache — any of them can keep a corpse
warm for days.

⚠️ **When something has been broken for a long time without anyone noticing, the
monitoring gap is the more serious of the two bugs.** Fix the service, then go
find why nothing said so, and record that as a separate finding. Otherwise you
have restored the system to the state where the next one is also invisible.
