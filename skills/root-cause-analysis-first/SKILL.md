---
name: root-cause-analysis-first
description: Use when something is failing and you are about to change code or config to fix it. Blocks the fix until you can say why it happens, and shows how to hunt a cause instead of confirming a guess.
---

# Root cause analysis first

Before you touch anything, finish this sentence with a mechanism:

> **This happens because ______.**

If the honest ending is *"I don't know, but this makes it go away"*, **you do not
have a fix.** You have a change that coincides with the symptom disappearing,
which is a different and much worse thing: the failure is still there, now
without its warning light.

## When to use this

- A service crashes, restarts, hangs, or returns the wrong thing
- A test is flaky
- Someone says "just bump the timeout / add a retry / restart it nightly"
- You are on your second attempted fix for the same symptom

## The failure this prevents

> A reverse proxy was restarting every 45 seconds. Three explanations were put
> forward, each plausible, each acted on:
>
> 1. **Memory** — it must be getting killed for using too much.
> 2. **A startup timer** — something must be tearing it down before it settles.
> 3. **The restart policy** — the policy must be misconfigured.
>
> **All three were wrong.** Not unlucky: wrong in the same way. Every one of
> them started from a suspect and went looking for evidence that fit. Evidence
> that fits is always available.
>
> The cause showed up only when someone stopped proposing and started
> collecting: follow the process tree upward from the thing being killed, and
> keep following it. It ended at a container that was talking to the runtime
> socket and stopping the proxy on a loop. Nothing to do with memory, timers, or
> policy — and nothing that any of those three lines of investigation could ever
> have found, however long they ran.

The lesson is not "look at process trees". It is that **a hypothesis you are
trying to confirm cannot be disproved by you.** You have to go at it the other
way round.

## The procedure

**1. Collect facts before you allow yourself a theory.** Timestamps, exit codes,
signal numbers, the last 200 log lines *before* the event and not after, what
changed in the last 24 hours, who else has access.

**2. Write down three candidate causes.** Three, not one. One candidate is a
conviction and you will spend the day defending it.

**3. For each candidate, write the observation that would KILL it.** Not the one
that would support it. This is the whole technique.

| Candidate | What would kill it |
|---|---|
| Out of memory | The process got a clean shutdown signal and had time to log |
| Config regression | The failure predates the config change |
| Bad input | It fails identically with input we know is good |

**4. Run the killing observations first**, cheapest first. You are trying to get
down to one survivor. If all three die, good — you have learned that the cause
is somewhere you were not looking, which is exactly what happened above.

**5. Confirm the survivor by making the failure happen on demand.** A cause you
cannot trigger is still a guess. Trigger it, fix it, then trigger it again and
watch it *not* happen.

**6. Only now write the fix** — and write it against the mechanism, not against
the symptom.

## Signals worth knowing

**A clean shutdown signal and an unconditional kill mean different things.** A
process asked politely to stop has time to write a final log line, flush, close
sockets. A process killed outright does not — so **an empty log at the moment of
death is itself the evidence**, and it points away from anything that would have
gone through the graceful path. If a crash left no trace, stop looking for the
trace and start asking who kills without asking.

**Frozen timestamps are loud.** A state file whose modification time had not
moved in two months exposed a loop that had been silently re-running the same
stale work the whole time. Nothing in any log said so. The file's date did.
Whenever you can, compare *when* something was last written against when you
believe it was last written.

**Ask who else writes here.** Not "what did I change" — *who or what else has
this path, this socket, this table, this queue*. Another agent, a cron job, a
sidecar, a second replica, an operator's shell. In the case above, the answer to
"who else can stop this process?" was the entire investigation.

**Look for the second explanation.** When you have one that fits, ask what else
would produce the exact same symptoms. If you cannot name a second candidate,
you have not understood the symptom well enough to be confident about the first.

## Traps

🔴 **A fix that works is not proof of the diagnosis.** Restarting fixes almost
everything, briefly. Correlation between your change and the symptom stopping is
the weakest evidence in the building.

🔴 **Retries and timeout bumps convert a hard failure into a slow one.** They are
sometimes the right call — but only *after* the cause is known and written down,
never as a way of not finding it.

⚠️ **Check the control.** Apply your diagnostic method to something you know is
healthy. If it flags that too, the method proves nothing. This is how it came out
that searching a codebase for references cannot tell you whether a database table
is still in use: the method flagged tables that were demonstrably live.

⚠️ **"It only happens in production" is a fact about your test environment**, not
about the bug. Find the component production has and the other place does not.

## When you genuinely have to ship without the cause

Sometimes the system is down and the cause will take a day. That is allowed —
under conditions:

1. The mitigation is written down **as a mitigation**, not as a fix.
2. It has an owner and a date to come back to it.
3. The unexplained part is recorded explicitly: *"we do not know why X, we only
   know that Y stops it."*

A knowledge unit recording this is a `hypothesis`, and it says so. Silently
filing a mitigation as a fix is how a system ends up with a dozen load-bearing
workarounds nobody can remove because nobody knows what they are holding up.
