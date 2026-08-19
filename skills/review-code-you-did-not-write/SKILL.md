---
name: review-code-you-did-not-write
description: Use when you are about to approve, merge or ship code an agent or another person wrote and you do not fully understand. Turns "it looks right and the tests pass" into a review that could have rejected it.
---

# Review code you did not write

Reviewing your own code is hard because you know what you meant. Reviewing code
you did **not** write is hard for the opposite reason: you have no intent to
compare against, so the only thing left to judge is whether it *looks* right.

**Looking right is what generated code is best at.** It has the shape of correct
code, the naming of correct code and the confidence of correct code. That is not
a criticism of the generator; it is the job description.

🔴 **You are not reviewing whether the code is plausible. You are reviewing
whether you could have caught it being wrong.** If nothing in your review could
have produced a rejection, you did not review it — you accompanied it.

## When to use this

- An agent produced a diff and you are about to merge it
- A dependency, snippet or template arrived from outside and is now yours
- You are approving a pull request in an area you do not own
- Something works and you cannot explain *why* it works
- You are about to write "LGTM" on more lines than you have read

## The procedure

**1. Read the diff, not the summary.** The summary is written by the same party
that wrote the code and shares its blind spots. If the summary and the diff
disagree, the diff is the truth — and the disagreement is itself the finding.

**2. For each change, ask what it would look like if it were wrong.** Not "is
this right?" — that question has an easy yes. Ask what a broken version of this
would look like, then check whether you would be able to tell the difference.
Where you cannot tell, you have found the part that needs a real check.

**3. Run the thing the change claims to fix, in the state a user would.** Not the
test suite: the actual claim. A change that "fixes the install" is verified by
installing, from a clean state, using the documented command, and nothing else
counts.

**4. Hunt for the confident no-op.** The most dangerous generated change is the
one that runs cleanly and does nothing:

| Shape | How it reads | What it does |
|---|---|---|
| A guard that never triggers | Defensive | Dead code that hides the real path |
| A check comparing a value to itself | Thorough | Passes by construction |
| An exception handler that swallows | Robust | Turns a failure into silence |
| A config written where nothing reads it | Configurable | No effect at all |
| A test asserting on data it just built | Well tested | Cannot disagree with the code |

**5. Verify the boring parts, because that is where it drifts.** Names of files
and commands, paths, versions, flags, and anything the change *claims* about the
rest of the repository. Generated text is fluent about things that do not exist.

**6. Say what you did not check.** A review that lists only findings implies
everything else was examined. Name the parts you took on trust; the next person
needs to know where the floor is.

## Anti-patterns

- **"The tests pass."** They were very likely written by the same author, in the
  same sitting, from the same misunderstanding. Passing tests raise your
  confidence in the code exactly as much as the tests deserve, which you have not
  assessed yet. Assess them: call the Skill tool with `verify-before-saying-done`.
- **"It's a small diff."** Size measures typing, not risk. Run
  `validated-memory route` on it instead of estimating.
- **"I'll catch it in QA."** Nothing downstream is looking for this. You are the
  check.
- **Reviewing the second version.** Once you have read the author's explanation,
  you are no longer independent — you are auditing their reasoning instead of the
  code. Read the diff first, the explanation after.

## Two incidents, both this shape

**An installer reported `✔ Successfully installed` and nothing usable arrived.**
The command was right, the exit code was zero, the message was green. The
verification that followed looked in the wrong directory and reported an empty
result — so for a few minutes the conclusion was "the package is broken" when the
broken thing was the check. Both the install and the check looked right. Only
comparing them against a known-good package settled it.

**A rule written in the contributing guide was violated in the code for hours.**
The guide required one language throughout; the code shipped with identifiers in
another. Tests were green, CI was green, review was done. It was caught by a
human reading the published diff on the website. The rule had no check behind it,
so nothing in the process could ever have rejected it.

The lesson from both is the same: **a rule with no check is a preference, and a
check you have not tested is decoration.**

## Related

- [`verify-before-saying-done`](../verify-before-saying-done/SKILL.md) — the
  check that has to be able to fail
- [`validate-your-validator`](../validate-your-validator/SKILL.md) — when the
  reviewer is the thing that is broken
- [`route-work-to-the-right-model`](../route-work-to-the-right-model/SKILL.md) —
  how many independent reviews this change actually needs
- [`review-changes-against-spec-and-standards`](../review-changes-against-spec-and-standards/SKILL.md)
  — the two-axis review, once you know the change deserves one
