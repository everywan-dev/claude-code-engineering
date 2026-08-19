---
name: check-if-data-is-safe-to-delete
description: Use when deciding whether a table, a file, or a service can be deleted because it looks unused. Measure real access, rename before deleting, and check the units of every counter.
---

# Check if data is safe to delete

Something looks unused. A table nobody mentions, a file with an old timestamp, a
service nobody remembers deploying. The question is whether it can go.

The answer is almost never obtainable by looking. It has to be measured, and the
usual way of measuring it is wrong.

## The rule

**Absence of evidence is not evidence of absence.** Every method below tells you
"this thing is used". None of them tells you "this thing is unused" — they only
fail to find a user, which is a different statement.

So the procedure is not "prove it is dead". It is: measure real access, then
make deletion reversible, then wait, then delete.

## What does not work

| Method | Why it fails |
|---|---|
| 🔴 Searching the codebase for the name | Access can be built at runtime, come from another repository, from a scheduled job, from a stored procedure, from a report tool, from a person with a client open |
| Last modified time | A read-heavy object is never modified. Old mtime is the normal state of something critical |
| "Nobody on the team knows what it is" | This describes the team's memory, not the system |
| Nothing broke in the test environment | The test environment is missing whichever caller is the dangerous one |
| A traffic graph that is flat | Check the window. Flat over 24 hours says nothing about a monthly job |

## What does work

**What the engine reports about actual access.** Almost every system that stores
things keeps its own access counters, and those counters see callers you cannot
find any other way:

- A database engine → its per-table access statistics: scans, index lookups,
  rows fetched, last-accessed timestamp.
- A filesystem → access times, if `atime` is not disabled. Verify that it is not
  before trusting a reading.
- A service → its own request log or metrics, and the connection table on the
  host.

Take the reading over a window long enough to include the slowest cycle you know
about: nightly, weekly, monthly, and — for anything financial or regulatory —
annual.

⚠️ **Also check what the reading does not cover.** A counter that resets on
restart tells you about the time since the last restart, not about the year.
Find out when it was last reset before you read a zero as meaningful.

## Read the units of every counter

🔴 **A number is not a measurement until you know what it counts.**

"Reads" can mean queries, rows, blocks, or bytes, depending on the system and
sometimes on the column. These differ by orders of magnitude, and every one of
them is called "reads" by somebody.

Before drawing any conclusion from a counter:

1. Find the documented unit of that exact field. Do not infer it from the name.
2. Sanity-check the magnitude against something you already know. If a table of
   200 million rows reports 2 billion "reads", ten full passes explains it
   completely and heavy usage does not.
3. Ask what the measurement itself contributed. Diagnostic queries are access.

## Rename before you delete

Deletion is not a decision you make once. It is a decision you make in two
steps, with a wait in between.

1. **Make it unavailable without destroying it.** Rename the table, move the file
   to a quarantine directory, stop the service without removing it. Whatever
   fails now, fails loudly and immediately, and is fixed by renaming it back.
2. **Wait through a full cycle.** Long enough to cover monthly work. For anything
   touching accounting or compliance, longer.
3. **Count before, and count after.** Rows, size, file count, request rate. Write
   both numbers down. "It looked the same" is not a count.
4. **Then take a verified copy** — one whose contents you have listed, see
   `deploy-to-production-safely` — and only then delete.

⚠️ If the rename itself is what breaks something, you have your answer, and you
got it in the cheapest possible way.

## Real case — zero references, billions of reads

A cleanup was proposed for several database tables that looked abandoned. The
evidence offered was a search of the entire codebase for the table names:
**zero references**. Nothing in the application mentioned them. On that basis
the recommendation was to drop them.

The engine's own access statistics were pulled before acting. Those same tables
showed reads in the **billions**.

The tables were in constant use. The search had found nothing because the
callers were not in the searched codebase — and it would have found nothing
regardless of how carefully the search was written, because a text search cannot
observe access.

**What this teaches:** the method was invalid, not the execution. A clean result
from an invalid method is more dangerous than a messy result from a valid one,
because it reads as confirmation. The only thing that counts is what the engine
reports about real access.

## Real case — a billion reads that were a dozen scans

A different table on the same system showed a spectacular read count and was
about to be treated as a hot path deserving an index and an optimisation effort.

The counter was in **rows**, not queries. Divided by the table's row count, the
number resolved to roughly a dozen full passes over the table — total, for the
whole period.

And several of those passes had been caused by the **diagnostic queries run
during the investigation itself**. The measurement had produced a meaningful
fraction of the thing being measured.

**What this teaches:**

- Always divide the counter by the row count. If the result is a small integer,
  you are looking at full scans, not traffic.
- ⚠️ **Your own queries are access.** Take the reading *before* you start
  exploring, or note which part of it you caused.
- The conclusion was one step away from being exactly backwards: "extremely hot,
  optimise it" versus "twelve scans, ignore it".

## Before you say it can be deleted

- [ ] Real access measured from the engine, not searched for in text
- [ ] The observation window covers the slowest known cycle
- [ ] Every counter's unit confirmed against documentation
- [ ] The reading corrected for access you caused yourself
- [ ] Made unavailable by rename or move, not by deletion
- [ ] A full cycle waited out with nothing breaking
- [ ] Counts recorded before and after
- [ ] A copy taken and its contents listed
