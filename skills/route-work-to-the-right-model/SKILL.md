---
name: route-work-to-the-right-model
description: Use before starting any change, to decide how much validation it needs and which model and effort to spend on it. Answers "is this a one-review change or a three-review change?" without arguing about it.
---

# Route work to the right model

**Deciding how much validation a change needs, per change, in the moment, is how
teams end up validating nothing.**

The decision always gets made under pressure, by the person who most wants the
answer to be "not much". So it is made in advance, from the kind of work, by a
table you can read and argue with when nothing is on fire.

## Ask it

```bash
validated-memory route "what you are about to do" [--path FILE ...] [--json]
```

It answers with a level, the number of validations, which agents, which model,
and which effort. It exits 0 always: this advises, it does not gate.

```
$ validated-memory route "small tweak to the checkout flow" --path src/billing/refund.py
Level 3 — 3 validations

  matched money: billing, checkout, refund
  matched touched path: billing

  model   : opus
  effort  : high
  agents  : security-reviewer, data-reviewer, devils-advocate

  Three, and the devil's advocate has to actively try to break it.
```

"Small tweak" is a description of **intent**. The paths and the words are a
description of **risk**, and only one of those two decides.

## The three levels

| Level | Kind of work | Validations | Model | Effort |
|---|---|---|---|---|
| **1** | Cosmetic, documentation, anything that never reaches production | 1 | small | low |
| **2** | Production code, service config, CI, dependencies | 2 independent | mid | medium |
| **3** | Auth, permissions, money, customer data, migrations, network, certificates, deletions | 3, one trying to break it | large | high |

## The one hard rule

**Nothing at level 3 runs on the small model.**

Saving tokens is worth it exactly where being wrong is cheap. It is never worth
it where being wrong means an outage, a breach, or someone's money. That rule is
asserted in code, not left to good intentions — see
[`route.py`](../../validated_memory/route.py) and the tests that pair every
level-3 phrase against the model it was given.

## When nothing matches

It does **not** fall back to the cheapest answer. An unrecognised change is
treated as production work, and the output says plainly that no signal matched:

> No signal matched, so this is treated as production work.
> That is the safe direction, not a measurement of your change.

Being wrong upward costs a review nobody needed. Being wrong downward costs an
incident. Those are not symmetric, so the default is not symmetric either.

If you know it touches something on the level-3 list, say so in the description
and re-run. The tool cannot see your change; it can only read what you tell it.

## What the level actually buys you

The number is worthless without the definition behind it:

- **Independent** means the validator **does not receive the implementer's
  reasoning**. Handing over your reasoning turns a check into an expensive echo.
- **Reviewing your own work again is not a second validation.** The blind spots
  travel with you.
- At level 3, one of the three has to **actively try to break it**. That is the
  [`devils-advocate`](../../agents/devils-advocate.md), and approving is not its
  job.

## Related

- [`docs/validation-levels.md`](../../docs/validation-levels.md) — the prose form
  of the same table, plus the list of what **disqualifies** a validation
- [`choose-the-right-code-review`](../choose-the-right-code-review/SKILL.md) —
  once you know the level, who reviews what
- [`verify-before-saying-done`](../verify-before-saying-done/SKILL.md) — the
  check that has to be able to fail before you call it done
