---
name: make-the-next-failure-loud
description: Use after an incident, or before shipping something whose failure would be invisible. Decides what to log, measure and alert on so the next failure announces itself instead of being discovered by a customer.
---

# Make the next failure loud

Debugging a silent failure is a skill. Not needing it is better.

Every outage that took days to notice had the same root: **nothing was watching
the thing that broke, and something else was cheerfully reporting success.**
Adding observability afterwards feels like paperwork, which is why it is skipped,
which is why the next one is silent too.

🔴 **The question is never "what should we log?" It is "what would have told us,
and how long would it have taken?"** Answer that about the failure you just had,
and you will know exactly what to add.

## When to use this

- You have just finished an incident and are about to close it
- You are shipping something whose failure would produce no error
- Something is "monitored" but you cannot say what would page you
- A dashboard is green and you do not trust it
- Anything scheduled: jobs, syncs, backups, reports, certificate renewals

## The procedure

**1. Write the failure you just had as a sentence.** "The export did not run for
four days and nobody noticed." Keep it; every step below is measured against it.

**2. Ask what signal would have contradicted the green.** Not what would have
shown the error — there was no error. What would have shown the **absence**:

| Instead of watching | Watch |
|---|---|
| "The process is running" | It finished, and when it last finished |
| "The endpoint returns 200" | The response contains what only a live system produces |
| "No errors in the log" | The log is still being written to at all |
| "The queue is healthy" | The queue is *moving*, and its oldest item's age |
| "Backups are configured" | A backup exists, is recent, and restores |
| "The certificate is valid" | Days remaining, alerting well before zero |

The pattern: **watch for the expected thing happening, not for the unexpected
thing failing.** Absence is the failure mode that survives every other check.

**3. Alert on the symptom a person would notice, at the threshold they would
notice it.** If a customer would care after one missed run, alert after one. An
alert nobody acts on is worse than no alert, because it teaches people that
alerts are noise.

**4. Delete or fix every alert that is already noise.** This is not optional
housekeeping. One permanently-firing alert makes the whole channel unreadable,
and the real alert arrives into a place nobody looks. If it cannot be made
actionable, it should not fire.

**5. Make the check itself fail loudly.** A health check that returns "unknown"
must not be counted as "healthy". A probe that could not reach the host reports
*could not check* — never *fine*.

**6. Test it by breaking the thing.** Stop the job, expire the certificate in a
staging copy, empty the queue's consumer. If nothing fires, you have added
paperwork, not observability. This step is the whole skill; the rest is design.

## Anti-patterns

- **Logging more.** Volume is not visibility. A silent failure in a system that
  logs a million lines an hour is still silent.
- **Dashboards instead of alerts.** A dashboard requires someone to look. The
  failures that hurt happen when nobody is looking.
- **Alerting on causes.** You cannot enumerate the causes. Alert on the symptom —
  the export is missing — and let the investigation find the cause.
- **Counting an alert as done when it fires in a test you wrote to make it
  fire.** Break the real thing.

## Two incidents

**A service was down for four days and the site returned 200 the whole time.**
The front page was a cached static page, so every check that asked "does it
respond?" got a yes. Nothing asked "does the response contain something only a
working backend can produce?" That single question, asked once a minute, would
have cut four days to four minutes.

**A restart policy scoped to failures never restarted a clean exit.** The process
exited with status zero, the supervisor concluded it had finished its work, and
it stayed down. Nothing was wrong, according to everything watching. What was
missing was a check that it was still *running an hour later* — liveness, not
launch success.

Both had monitoring. Both had the wrong question wired to it.

## Related

- [`debug-a-silent-failure`](../debug-a-silent-failure/SKILL.md) — the reactive
  half: you are already inside one
- [`verify-before-saying-done`](../verify-before-saying-done/SKILL.md) — a check
  that cannot fail is not a check, and that includes health checks
- [`detect-stale-documentation`](../detect-stale-documentation/SKILL.md) — the
  same principle applied to what you wrote down
- [`write-docs-people-can-find`](../write-docs-people-can-find/SKILL.md) — when
  the alert fires at 3am, the runbook has to be findable by the symptom
