---
name: route-the-review
description: Use when deciding how much review a change needs, and of what kind. What the change touches decides the level — not how big it looks, not how confident you feel.
---

# Route the review

How much review a change needs is **not** a judgement made in the moment by the
person who wrote it. It is decided by what the change touches, before the change
is written, by a table.

The reason is simple: the author is the worst-placed person in the building to
estimate the risk of their own change. Everything they thought of is already
handled. The risk lives entirely in what they did not think of.

## When to use this

- A change is finished and you are about to ask for review
- You are deciding whether "this is tiny, just merge it" is true
- You are assembling reviewers and need to know how many and which
- A change has grown since it started and may have crossed a line

## The routing table

| Level | The change touches | Reviews | One of them must |
|---|---|---|---|
| **1** | Cosmetic, documentation, anything that never reaches production | **1** | Look at the rendered result, not the source |
| **2** | Code in production, service configuration, build pipelines, dependencies | **2, independent** | Judge whether the evidence could have failed |
| **3** | Authentication, permissions, money, customer data, schema migrations, deletions, network and firewall rules, certificates, anything that runs everywhere at once | **3, independent** | **Actively try to break it** |

### Classifying without debate

If the change touches **any** of these, it is level 3. No discussion, no
weighing:

- login, passwords, tokens, sessions, permissions, roles
- amounts, prices, refunds, balances, invoicing
- customer or personal data
- schema changes, deletions, table drops, bulk updates
- network rules, firewall, address translation, routing
- certificates and their renewal
- anything applied to every site, tenant or node in one action

Touches production but none of the above → **level 2**. Never reaches production
→ **level 1**.

⚠️ **The size of the diff does not appear anywhere in this table.** A one-line
change to a permission check is level 3. A two-thousand-line documentation
rewrite is level 1.

⚠️ **Re-classify when the change grows.** A change that starts as a config tidy
and ends up touching the routing rules is not a config tidy any more, however it
was announced.

## What "independent" actually means

This is where most review processes quietly become theatre.

🔴 **The reviewer does not receive the implementer's reasoning.** They receive
the change and the acceptance criteria. Nothing else.

Reasoning is contagious. Handed a well-argued explanation, a reviewer starts from
inside it and checks whether the pieces are consistent with each other — which
they always are, because the author made them so. The one wrong assumption is
never in the parts being checked. It is in the premise the explanation opens
with.

🔴 **The same reviewer, a second time, is one review.** Whether it is the same
person on a different day or the same agent in a later turn, the blind spots
travel with them. Independence is the requirement; the count is only how it is
measured.

⚠️ **A reviewer who helped design the change is not independent of it.** They
will verify their own decisions and find them sound.

### What each reviewer receives

```
- The change itself (diff, config, commands)
- The acceptance criteria: what must be true afterwards
- The evidence presented as proof
- The rollback
```

Not the narrative. Not "the tricky bit is X, but it's handled because Y" — that
sentence removes X from the review.

## Level 3 needs an adversary, not a third opinion

At level 3, one of the three is not reviewing to approve. Its goal is for the
change **not** to ship. It passes only by failing to break it after genuinely
trying.

A third agreeable reviewer adds very little: three people looking for
confirmation find three confirmations. The value comes from somebody whose
success condition is finding the failure.

Give the adversary the same package everyone else got, and one instruction:
find the case where this is wrong.

## What does not count as one of the reviews

| Presented as review | Why it isn't |
|---|---|
| "I read it again carefully" | Same reader, same blind spots |
| "The pipeline is green" | The pipeline checks what someone thought to check before this change existed |
| "It parses / it compiles / the config is valid" | Valid and correct are unrelated properties |
| "It works in the test environment" | The test environment is missing whatever makes production dangerous |
| "It's been running for an hour with no errors" | Absence of noise from a system nobody is observing |
| "The author walked me through it" | That is the reasoning being transferred — see above |

## Real case — the cost is asymmetric, and badly

A service was mis-classified downwards. It looked like a routine restart policy
tweak, so it got one quick look instead of two independent ones. The subtlety it
carried was that the policy in use would not restart a process that exited
**cleanly** — only one that crashed.

A dependency then exited cleanly. Nothing restarted it. Nothing alerted, because
the front end still answered with a cached page and the health check was
satisfied by the status code.

**Four days.** That is how long the component stayed down before anyone noticed,
and most of the recovery cost was in reconstructing what had been happening
during those four days, not in restarting anything.

Being wrong upwards on that change would have cost one extra review: half an
hour, and it would have been described afterwards as unnecessary. That is what
being wrong upwards always looks like, and it is why the table exists instead of
a judgement call. **When in doubt, go up a level.**

## Real case — the sentence the reviewer did not review

A reviewer was handed a change together with the implementer's write-up. The
write-up opened with: *"the queue name is unchanged, so consumers are
unaffected."* The reviewer checked the routing, the error handling, the retries
and the metrics. All correct. Approved.

The queue name **was** unchanged. The consumers were affected anyway, because
they filtered on a message attribute the change had renamed.

The sentence was never reviewed, because it did not arrive as a claim. It
arrived as a premise — the frame the rest of the review happened inside.

The same change, reviewed later from the diff and the criteria alone with no
write-up attached, produced the question *"what identifies a message to a
consumer here?"* in the first minute.

**That is the entire argument for withholding the reasoning**, and it is why
"the author explained it to me" makes a review worse, not better.

## Traps

🔴 **Nobody classifies their own change downwards on purpose.** They classify it
by how well they understand it, which is precisely the wrong instrument.

🔴 **Urgency is not a level.** "It's a hotfix" changes the deadline, not what the
change touches. A hotfix to an authentication path is a level-3 change being
made badly.

⚠️ **Reverting is also a change.** A revert to a production system touching any
level-3 area is a level-3 change. Reverts are routinely treated as free because
they restore a state that once worked — on a system that has moved since.

⚠️ **Do not let one reviewer cover two roles.** "I checked the tests and I also
tried to break it" is one review wearing two labels.

⚠️ **Record the routing decision with the change.** Which level, and why. Six
months later the useful question is not whether it was reviewed but what it was
reviewed *as*.

---

See `verify-before-claiming` for what makes any single check count, and
`plan-the-undo-first` for the rollback every level-2 and level-3 review is
supposed to read.
