---
name: get-a-second-model-opinion
description: Use when a claim needs a second opinion that does not share your blind spots. How to ask a different model, what to send it, and how to settle a disagreement.
---

# Get a second model opinion

Asking yourself again is not a second opinion. Whatever made the first answer
wrong is still in place for the second one: the same priors, the same reading of
the same evidence, the same thing you failed to consider. People have this
problem too, which is why review is done by somebody else.

So when a claim needs checking and no command can settle it, take it to a
**different model** — a different family, a different provider, something with a
different training history. Not the same one in a fresh session.

## When to use this

- A conclusion is load-bearing and nothing you can execute will confirm it
- You are about to write something into long-lived documentation
- A design decision hinges on a fact you are confident about but never verified
- You have been reasoning about the same problem long enough to be attached to
  your explanation
- Two of your own hypotheses fit the evidence equally well

## What this can and cannot answer

The second model has **no access to your systems**. It cannot see your files, run
your commands, reach your hosts or read your logs. That single fact decides the
whole question taxonomy.

| Ask it | Do not ask it |
|---|---|
| Is this general claim true? | Is this service running? |
| What is wrong with this reasoning? | Does this file contain X? |
| What does this design assume that nobody stated? | Did the change apply? |
| What is a second explanation for these symptoms? | Which version is deployed? |
| Which of these two readings of this specification is right? | Is this host reachable? |
| What is the failure mode nobody listed here? | Why did this command fail on my machine? |

🔴 **Anything whose answer lives inside your environment is not a cross-check
question.** Sent anyway, you will get a confident, fluent, entirely invented
answer — because a plausible answer is the only thing that can be produced when
the real one is unreachable.

The rule of thumb: **if the answer could be obtained by running something, run
it.** A cross-check is for the questions no command settles.

## How to ask

### Send the fact and the criterion. Do not send your reasoning.

This is the whole technique, and it is the part that gets skipped.

Given your explanation, the second model will evaluate whether the explanation
hangs together — and it will, because you built it that way. You get agreement
that means nothing, and the wrong premise passes through untouched, exactly as it
does with a human reviewer handed the author's write-up.

| Send | Withhold |
|---|---|
| The observation, raw | Your diagnosis |
| The configuration or the specification, as written | Why you believe it means what you think |
| What must be true for this to be correct | Which parts you already ruled out |
| The concrete question | The answer you are hoping for |

### Ask for the failure, not the verdict

"Is this right?" invites a yes. Better shapes:

- *"What would have to be true for this to be wrong?"*
- *"What is this assuming that nobody stated?"*
- *"Give me a second explanation for the same symptoms."*
- *"What would you check first if you were told this conclusion is wrong?"*

### Ask what it cannot know

A useful second model tells you which parts of its answer are inference. Ask it
directly: *"which of these statements would you need to observe to be sure of?"*
That list is your list of things to go and check — and it is often more valuable
than the answer.

## Settling a disagreement

The two answers differ. Now what?

🔴 **The larger, newer or more expensive model does not win by default.** Neither
does yours, on grounds of having thought about it longer. Model prestige is not
evidence.

The rule:

> **Whoever can show the check, wins.**

A check is something that could have come back the other way: an output, a
minimal example that reproduces, a line in a specification, a measurement.

And the case everyone wants to skip:

> **If neither can show a check, the claim's state is not "true" and not "false".
> It is _unchecked_ — and it gets written down as unchecked.**

Two models agreeing is a weak signal, not a proof. They can share a wrong prior
for the same reason two people educated the same way can: the error is upstream
of both of them. Recording "both models agreed" as if it were verification is how
a confident guess enters the documentation with a citation attached.

Disagreement, by contrast, is genuinely useful. It has located a place where the
answer is not obvious, which is exactly where you should now spend the effort of
constructing a real check.

## Real case — the second explanation nobody had looked for

A pool of shared desktops failed to be available at the start of the working day.
Every morning, same window, then fine for the rest of the day. The first analysis
was coherent and complete: it identified a distribution setting that concentrates
users onto the fewest possible hosts, explained the mechanism clearly, and
proposed a change.

The same symptoms were then given to a different model — timestamps, the
configuration as written, no diagnosis attached, and one question: *"what else
could produce this pattern?"*

It asked what else ran on that schedule.

There was an automatic power-down policy, and its idle timer was expiring on the
reserve capacity a few minutes before the morning arrivals. The distribution
setting was real and was part of the picture, but on its own it was never going
to be the fix — and the proposed change would have been applied, would have
appeared to help slightly, and would have left the actual mechanism in place.

The second model did not know anything the first did not. **What it did not have
was the first model's explanation**, which is precisely why it went looking for
another one.

## Real case — the disagreement that was correctly left unresolved

A claim: *"this table is unused, it can be dropped."* The evidence: a search of
the codebase for the table name, no results.

Cross-checked, with the claim and the evidence but not the reasoning, the second
model asked a single question: *how would that search distinguish "unused" from
"used through a name built at runtime"?*

It would not. Neither model could produce a check that separated the two, because
the only instrument that could — observing actual access at the storage layer —
was not something either of them could reach.

So nothing was dropped, and the record said: *"believed unused; the only evidence
is a code search, which cannot see dynamically built names. Unchecked. To settle
it: observe access over a full billing cycle."*

**That is a successful cross-check.** It produced no answer. It produced the
correct status, and the specific check that would change it — which is worth
considerably more than a confident deletion. (`check-if-data-is-safe-to-delete` covers
what that check has to look like.)

## Traps

🔴 **Never paste credentials, customer data, or anything you would not publish
into a second system.** A cross-check is a copy of your material into somewhere
else's logs. Rewrite the question in the abstract: the mechanism is almost always
the part that needs checking, and the mechanism does not need the real values.

⚠️ **Do not send it your conclusion "just for context".** It is not context, it
is the answer key.

⚠️ **Two models agreeing is not verification.** It is two guesses that rhyme.

⚠️ **Do not shop for the answer you wanted.** Asking a third and a fourth until
one agrees with you is not cross-checking; it is sampling until the noise says
what you like.

⚠️ **A confident tone is not an instrument.** Both answers will sound certain.
Certainty is free, and cheapest exactly where knowledge is thinnest.

---

Once a cross-check gives you a check you can run, run it — see
`verify-before-saying-done`. If it gives you a question nobody can answer, it
belongs in the gap list — see `map-an-undocumented-system`.
