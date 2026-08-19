---
name: validate-your-validator
description: Use when writing or trusting anything that decides pass/fail — a test, a linter, a scanner, a health check, a monitor. Makes the checker prove it can fail before you believe a green result.
---

# Validate your validator

**A checker that cannot fail is not checking anything.** It is a green light
wired to nothing, and it is worse than no checker at all, because now everyone
has stopped looking.

The test is simple and non-negotiable: **plant the failure it exists to catch,
and confirm it catches it.** Until you have watched it go red on purpose, a
green result carries no information.

## When to use this

- You are writing a test, a lint rule, a scanner, a validator, a probe
- You are adding a health check or an alert
- You are about to trust a green CI run on something important
- A checker has been green for a suspiciously long time
- Someone says "the scan found nothing"

## The procedure

**1. Write the checker.**

**2. Plant a failure.** Introduce, in a fixture or a scratch copy, exactly the
thing the checker exists to detect. A real one, not a simplified one.

**3. Run it. It must go red.** If it does not, the checker is the bug — fix it
before you fix anything else.

**4. Plant a control: something you know is fine.** Run it. It must go green.
A checker that flags everything is as useless as one that flags nothing, and it
is more expensive, because people learn to ignore it and then ignore the true
positive too.

**5. Keep both as permanent fixtures inside the checker.** This is the part
everyone skips. The planted failure and the control become cases the checker
runs against itself, every time. The day someone refactors the pattern and it
stops detecting anything, the suite goes red instead of going quiet.

**6. Write down what it cannot catch.** Every checker has a blind spot. An
unwritten blind spot gets read as full coverage by the next person.

## The case that earns this skill its place

> A secret-detection step was added to a CI pipeline. It **incriminated itself
> three times** before it was fit to run.
>
> **First**, it searched for bare credential prefixes. Those prefixes were
> written in its own rule list, in its own source file, which the scan walked.
> It reported itself as a leak. Excluding its own file made it green — and would
> have made it green forever, because there was no case proving it could still
> detect a real one.
>
> **Second**, the sentinel string used as its own control appeared verbatim in
> the file. So the "proof it works" and the "thing it found" were the same
> bytes. It was detecting its own test data and reporting a pass.
>
> **Third**, and worst, it flagged `TOKEN = os.environ.get("X")` as a hardcoded
> secret. That line is the **correct** pattern — it is a secret being read from
> the environment, the exact thing you want people to write. The checker was
> punishing the good behaviour and, by symmetry, had never been shown a real
> hardcoded value to see whether it would fire on one.
>
> What fixed it was not a better pattern. It was two fixtures: a file containing
> a genuine-shaped credential that the suite asserts **is** flagged, and a file
> containing environment reads and placeholders that the suite asserts is
> **not**. Both live next to the scanner. Break the scanner now and the suite
> tells you.

Three separate ways to be green while proving nothing, in one small tool. Assume
yours has at least one.

## The two ways a checker dies

| Failure | What it looks like | How you catch it |
|---|---|---|
| **Cannot fail** | Always green. Nobody remembers it ever going red. | Plant a real failure. If still green, it is dead. |
| **Always fails** | Noisy, so everyone adds exclusions until it is silent again | Plant a known-good control. If it flags that, the rule is wrong, not the code. |

🔴 **The exclusion is where checkers go to die.** Every `# noqa`, every ignore
path, every skipped file is a place the checker was switched off to make the
build pass. Adding one is fine. Adding one *without a case proving the checker
still fires elsewhere* is how you end up with a scanner that only scans an empty
directory.

## Apply it to diagnostic methods too

Not only to automated checkers — to any method you are using to reach a
conclusion.

**Run your method against something you already know the answer for.**

> The question was whether a database table was still in use. The method
> proposed was searching the codebase for references to its name. Applied as a
> control to tables that were demonstrably live — being written to right then —
> the search found nothing for those either. Names get built dynamically, come
> from config, live in a migration.
>
> The method could not distinguish "unused" from "not referenced by a literal
> string". It would have authorised dropping live tables, and the search would
> have looked like diligence.

If your method flags the healthy control, throw the method away. Do not adjust
it until the control passes — that is fitting the method to the answer you
wanted.

## Traps

⚠️ **A checker that scans files must handle its own file honestly.** Excluding
itself is often correct. Excluding itself *as the fix for it reporting itself*,
with no other case, means you have never seen it detect anything.

⚠️ **A test that passes the first time you run it deserves suspicion.** Break the
code it covers and watch it fail, once. Especially for anything asserting an
absence.

⚠️ **An alert nobody has ever received is not an alert.** Fire it deliberately.
Confirm it arrives, at the destination, in a form someone would act on.

⚠️ **Do not measure the checker by how much it finds.** A scanner reporting 400
issues is usually a scanner about to be muted. Precision is what keeps it alive
long enough to catch the one that counts.

## The record

When you record that a checker is in place, record what proved it:

```markdown
**Checker:** credential scan in CI
**Proved it can fail:** fixture with a real-shaped credential → flagged (exit 1)
**Proved it is not noisy:** fixture with environment reads → clean (exit 0)
**Both fixtures live in:** the scanner's own test suite
**Known blind spot:** credentials assembled at runtime from parts
```

Without the two middle lines, "we have a secret scanner" is a claim about a file
existing, not about anything being scanned.
