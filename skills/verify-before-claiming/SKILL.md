---
name: verify-before-claiming
description: Use when about to report something as done, working or fixed. Turns "it looks right" into a check that could have failed.
---

# Verify before claiming

**A check that cannot fail is not a check.**

Before the words "done", "fixed", "working" or "deployed" leave you, you have to
be able to answer one question:

> **What did I run that, if this were broken, would have returned something
> different?**

If there is no answer, you have a reading, not a verification. Say so instead.

## When to use this

- You are about to close a task, comment on a ticket, or answer "is it up?"
- You changed a config, restarted a service, edited a file inside a container
- You fixed something visual
- Someone asks you to confirm a state you have not observed since you changed it

## The procedure

**1. Write the claim as one sentence.** Not "the deploy went fine" — *"the API
returns the new schema version on all four nodes"*. A vague claim cannot be
falsified, which is why vague claims are the ones that survive.

**2. Name the failure mode you are ruling out.** "If this were broken, what
exactly would be wrong?" The answer picks your instrument. Ruling out *"the
service did not pick up the config"* needs the process's own view of its config,
not the file on disk.

**3. Pick an instrument that observes the claim, not a neighbour of it.** Most
false verifications are a measurement of something adjacent:

| You measured | You claimed | The gap |
|---|---|---|
| The file parses | The service loaded it | Loading can be rejected after parsing |
| The file on disk changed | The process reads the change | Different inode, different file |
| The port answers | The application works | Anything can answer a port |
| It works in staging | It works in production | Different components, different risk |
| The CSS says `red` | The user sees red | Something else wins the cascade |

**4. Run it and keep the raw output.** Not your summary of it. The count, the
status line, the response body, the screenshot. Summaries are where the
optimism gets in.

**5. Prove the check is live.** Break something on purpose — point it at a
hostname that does not exist, at a node that is down — and confirm it goes red.
A green result from a check you never saw go red tells you nothing about the
system, only about the check.

**6. Report what you did not check.** Always a line, even when empty. "Verified
on nodes 1–3, node 4 unreachable" is worth more than a clean claim covering
four.

## Real cases

> **"The config is valid."** A reverse proxy was handed a syntactically valid
> file containing a duplicated route. It refused the file, kept the previous
> configuration **in memory**, and logged nothing anyone was watching. Every
> request kept working. The failure surfaced days later at the next restart,
> when the old configuration finally left memory — with nobody near a keyboard
> who connected the two events.
>
> Validating the file proved the file was valid. It never proved the process was
> using it. Those are two different claims and only one of them was true.

> **"The site returns 200."** A service was down for **four days** and no one
> noticed. The login page was static and cached, so the health check kept
> getting 200 from a page that no longer needed the backend to exist. The check
> could not have failed — which is exactly why it never did.
>
> The fix was to check something only a working backend can produce: a real
> query, an authenticated call, a value that changes.

> **"The file on disk has the change."** An in-place edit rewrote the file by
> creating a new inode. The running process still held the old one open and went
> on reading it. Disk and process disagreed, and only the disk was inspected.
>
> Compare the disk against **what the process sees** — its open file handles,
> its own config dump, its behaviour. Not against your memory of the edit.

> **"It works in the test environment."** The test environment did not contain
> the legacy component that made the change dangerous in production. It was not
> that the test passed by luck: the test was structurally incapable of
> detecting the risk. Absence of the failing component is not absence of the
> failure.

> **"It looks fine."** Three consecutive fixes to a logo failed, because each
> one was written by reading CSS and reasoning about it. The fourth worked,
> because someone rendered the page and looked at the resulting DOM. The
> cascade had a winner nobody predicted from reading.

## Traps

🔴 **A green check you have never seen go red is decoration.** Break it once,
deliberately, before you trust a single green result from it.

🔴 **"The service is running" is not "the service works."** It can be in a
restart loop and still be reported as running. Read the status detail and the
log, not the one-word state.

⚠️ **Never verify a fleet through the load-balanced name.** Resolve to each
address in turn. A round-robin will cheerfully hand you the one healthy node
every time you ask.

⚠️ **Your own cache lies to you.** If you are looking at a browser, a CDN, or
any client-side store, you may be looking at yesterday. Force the fetch or
version the asset.

⚠️ **Re-reading your own change is not verification.** You will read what you
intended to write. Observe the *effect* somewhere else in the system.

## What a verified claim looks like

```markdown
**Claim:** the workers pick up jobs from the new queue.
**Failure mode ruled out:** workers still bound to the old queue name.
**Check:** enqueued one job, read the consumer's own log line for it.
**Raw output:** <pasted>
**Control:** enqueued to the old queue — nothing consumed it. Check is live.
**Not verified:** behaviour under a queue restart.
```

The last line is mandatory. It can be empty; it is never omitted. It is the
whole difference between *"it works"* and *"I could not check that it works"*.
