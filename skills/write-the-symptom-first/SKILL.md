---
name: write-the-symptom-first
description: Use when writing up an incident, a fix, or anything that took real time to understand. The reader six months from now searches by symptom, not by cause.
---

# Write the symptom first

You are not writing for yourself today. You are writing for **the person who
hits this in six months and remembers nothing** — and that person is usually
you.

That person has one thing: what they can see. An error string, a restart loop, a
number that looks wrong. They search for **that**. They cannot search for the
cause, because finding the cause is the entire problem they are trying to solve.

So the cause never goes in the title.

## The rule

> **Bad:** *"Fixed the certificate dumper hook."*
> **Good:** *"The reverse proxy restarted every 45 seconds"* — and the cause
> underneath.

Nobody searches for "certificate dumper hook". They search for "proxy keeps
restarting".

The first line is the symptom, phrased the way it looked from outside, using the
words the reader will actually have in their head. Everything else goes below
it.

## Structure

```markdown
## <The symptom, exactly as it appears>

**Where it bites:** service, file, host, environment.

**Symptom:** what you see. Paste the literal error message, unedited —
including the parts that look like noise. That string is the search key.

**How to diagnose it:** the commands, in the order you would run them, with
what each one tells you. Ordered so the cheapest, most discriminating check
comes first.

**What was tried and did not work:** each wrong theory, and what ruled it out.

**Root cause:** why it happens. If you do not know, write "not established" —
never fill this in with something plausible.

**Fix applied:** what was changed, and where.

**How to prevent it:** what to check next time, or what would have caught it.

**Left unverified:** what you did not get to confirm.
```

## What goes in, no exceptions

- **Anything that cost more than half an hour of confusion.** That is the
  threshold. Not "anything important" — importance is judged after the fact and
  always underestimates this.
- 🔴 **The failed attempts, and why they failed.** This is the part people cut
  first and the part that saves the most time. "Three theories were proposed and
  all three were wrong, here is what ruled each one out" is real information: it
  stops the next person walking the same three roads.
- **Your own wrong turns.** Documentation that records only successes teaches
  nobody how to diagnose. It reads like the answer was obvious, which makes the
  next person feel slow instead of informed.
- **The literal error text**, even if it is ugly, even if it is long, even if it
  contains a hash that will be different next time. It is what gets searched.
- ⚠️ **What was left unverified**, marked as such. An unverified claim presented
  as fact is worse than a gap, because the gap gets investigated and the false
  fact gets built on.

## What stays out

| Out | Why |
|---|---|
| Anything the code already says | It will drift, and then it lies |
| Anything the version history gives you | Who and when are already recorded |
| Adjectives | "A robust and elegant solution" tells the reader nothing about what it does |
| Narrative of your afternoon | The reader wants the sequence of checks, not the sequence of your feelings about them |
| A cause you are guessing at, written as fact | Write "not established" |

## Real case — the note nobody could find

A service was restarting roughly every 45 seconds. It took most of a day to
work out that a hook responsible for exporting certificate material was failing
and taking the process down with it.

The fix went in. The write-up was one line: *"Fixed the certificate dumper
hook."*

Months later the same restart loop appeared on a different host. The person
looking at it searched the documentation for "restart", for "restarting", for
"restart loop", for the exact interval. Nothing. The note existed, was accurate,
was in the right repository — and was invisible, because the only words in it
were words describing the cause, which is precisely the thing the searcher did
not yet know.

The day was spent again.

**What this teaches:** an accurate note filed under the cause is, for search
purposes, not a note. Indexing by symptom is not a stylistic preference — it is
the difference between a document that gets found and one that does not.

## Real case — the ruled-out theory that was the useful part

A machine kept rebooting on its own. The write-up recorded the root cause, and
also recorded a line that felt like clutter at the time: *"the physical error
counter on the link was zero, so this is not a bad cable — do not spend time
there."*

When a similar symptom appeared elsewhere, that one sentence removed the most
expensive and most tempting hypothesis in under a minute. It was worth more than
the root cause section, because the root cause the second time was different and
the elimination still held.

**What this teaches:** record what you ruled out **and the observation that
ruled it out**. "It was not the cable" is an opinion. "The error counter read
zero, so it was not the cable" is a reusable test.

## Where it goes

| What | Where |
|---|---|
| A trap that will recur | The runbook for that topic |
| A one-off deployment | The notes for that service |
| What was done and when | A dated history file, newest at the top |
| Credentials and access | Your secret store — **never** in a repository |
| Still open | The project README, where people actually look |

Then check the internal links point at files that exist.

## Before you call the write-up done

- [ ] The title is the symptom, in the words someone would search for
- [ ] The literal error text is pasted, unedited
- [ ] The diagnosis is a sequence of commands, in order, each with what it shows
- [ ] Failed theories are listed with what ruled them out
- [ ] The root cause is stated, or explicitly marked as not established
- [ ] Unverified parts are marked
- [ ] No adjectives doing the work of a fact
