---
name: know-what-a-change-costs
description: Use before shipping something that runs repeatedly — a job, a query, an agent loop, a pipeline. Estimates the recurring cost of a change while it is still cheap to change, and decides where spending less is safe.
---

# Know what a change costs

A change that runs once has a price you can ignore. A change that runs on every
request, every commit or every hour has a price that compounds, and nobody
notices until the invoice or the quota arrives.

The failure is rarely a big expensive decision. It is a small one **multiplied by
a frequency nobody wrote down.**

🔴 **Cost is a property of the change, and it is knowable before you ship.**
Frequency × unit cost. Both numbers are usually available in under a minute, and
almost nobody looks them up.

## When to use this

- Adding anything that runs on a schedule, per request, or per commit
- Putting a model call inside a loop
- Adding a query to a hot path
- Choosing between a fast/expensive and a slow/cheap option
- Anything with retries — the interesting number is the retry cost
- After a bill or a quota surprises you

## The procedure

**1. Write down the frequency, explicitly.** Per commit, per user action, per
hour, per item in a list that grows. This is the number that gets skipped, and it
is the one that decides everything.

**2. Multiply by the unit cost.** Tokens, queries, requests, seconds of compute,
gigabytes egressed. An order of magnitude is enough; you are looking for surprises,
not accounting.

**3. Then compute the failure cost, which is the one that bites.** Retries,
back-off loops, a job that reruns because the previous one did not record success,
a queue that reprocesses from the start. **The expensive scenario is almost never
the happy path.** Ask what this costs on the worst day, not the average one.

**4. Check the ceiling as well as the price.** Quotas, rate limits and weekly
caps fail differently from money: they stop the work. A cost you can pay is a
budget problem; a limit you hit is an outage.

**5. Spend where being wrong is expensive; save everywhere else.** This is the
same rule the validation router uses, and it is the whole of cost discipline in
one line. The large model on a security review is cheap insurance. The large
model on a changelog entry is waste, three times a day, forever.

**6. Record the number where the next person will find it.** Cost that lives in
someone's head gets re-derived badly or not at all.

## The distinctions that matter

| | Looks like | Actually is |
|---|---|---|
| One expensive call | The problem | Usually irrelevant |
| A cheap call in a loop | Fine | The bill |
| Retries | An edge case | The worst-day multiplier |
| A quota | A cost | An availability limit |
| Idle capacity | Waste | Often the cheapest insurance you have |

## Anti-patterns

- **Optimising before measuring.** Profile, then decide. The slow part is rarely
  where you think, and rewriting the wrong part costs twice.
- **Treating tokens as free because they are not invoiced to you.** Quotas are a
  cost denominated in outages.
- **Cutting cost where being wrong is expensive.** Saving on the review of a
  payment path is not a saving.
- **A cost estimate with no frequency in it.** That is a price, not a cost.

## The incident

An automated pipeline was configured to use the largest available model for every
run, three times a day, on a subscription with a weekly cap. Each individual run
was reasonable. The cap was reached mid-week, and from that point every scheduled
run failed — not slowly, not degraded: it stopped.

Two things made it worse than a bill would have been. The failure was a **quota**,
so no amount of willingness to pay fixed it that week. And the retry logic, built
for transient errors, kept re-attempting against an exhausted quota, which is the
retry cost from step 3 arriving exactly when there was no capacity to absorb it.

The fix was not a cheaper model everywhere. It was deciding, per stage, where the
large model was actually buying something — and letting the cheap stages be
cheap.

## Related

- [`route-work-to-the-right-model`](../route-work-to-the-right-model/SKILL.md) —
  the same rule, applied to validation effort, as a command
- [`make-the-next-failure-loud`](../make-the-next-failure-loud/SKILL.md) — a
  quota approaching its limit should page you before it stops the work
- [`write-the-rollback-plan-first`](../write-the-rollback-plan-first/SKILL.md) —
  including how to turn the expensive thing off in a hurry
