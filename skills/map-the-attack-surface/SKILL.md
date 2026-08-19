---
name: map-the-attack-surface
description: Use before exposing something, after inheriting a system you did not build, or when a security review says "looks fine". Finds who can reach what, and the authorisation gaps that scanners never report.
---

# Map the attack surface

Most security work in ordinary projects is not cryptography. It is answering one
question honestly:

**Who can reach what, and what stops them from reaching more?**

The bugs that actually hurt are rarely exotic. They are an endpoint that checks
you are *logged in* but not that the record is *yours*, a test environment
sharing production credentials, an admin panel reachable from the internet
because a proxy rule was broader than intended.

🔴 **Automated scanners find injection. They do not find authorisation.** A
scanner cannot know that record 41 belongs to a different customer than record
42. That gap is where the expensive findings live, and it is found by asking, not
by tooling.

## When to use this

- Before exposing anything to the internet, or widening who can reach it
- After inheriting a system nobody can fully explain
- When a scan came back clean and you want to know what it could not see
- Before handling customer data, money or credentials
- After any credential leak, to work out what it could reach

## The procedure

**1. List the entrances.** Every way in: public endpoints, admin interfaces, APIs,
webhooks, file uploads, scheduled jobs that fetch from outside, database ports,
management planes, SSH. Include the ones you assume are internal — then check
whether they are.

**2. For each entrance, name what is on the other side and who is allowed.**
Write it as a sentence. Vagueness here is the finding: if nobody can state the
rule, nobody is enforcing it.

**3. Test authorisation with two accounts, not one.** This is the step that finds
the real bugs. Log in as tenant A, take an identifier belonging to tenant B, and
ask for it. Do it for every object type that has an owner. A scanner will never
do this for you.

| Question | What it finds |
|---|---|
| Can A read B's record by changing an id? | Broken object-level authorisation |
| Can a normal user reach an admin action directly? | Missing function-level checks |
| Does the list endpoint filter by owner, or the detail one only? | The most common variant |
| Do the test and production systems share a credential? | One breach becoming two |
| Does an error message differ for "not yours" and "does not exist"? | Enumeration |

**4. Follow every credential to everything it opens.** A key is not a secret, it
is a set of permissions. Write down what each one can do, and whether it is
shared between environments.

**5. Ask what a compromise would let someone do, not whether it is likely.**
Likelihood is a guess; blast radius is a fact you can establish today.

**6. Write down what you did not check.** An attack-surface map that implies
completeness is worse than a partial one that is honest about its edges.

## Anti-patterns

- **"It's behind a VPN."** So is everyone who is already inside, including
  anything compromised.
- **"Nobody knows the URL."** Obscurity is not a control. Certificate transparency
  logs, referrers, browser history and crawlers all know the URL.
- **"The scanner is clean."** It tested for the classes it knows. Authorisation is
  not one of them.
- **"Test data is not real."** Check. Test environments are frequently refreshed
  from production, and often with weaker access controls.
- **Threat-modelling the exotic attacker** while an unauthenticated admin path
  sits open.

## The incident

A security review of a multi-tenant panel came back clean on the automated axes:
no injection, credentials handled correctly, dependencies current.

Asking the two-account question found that a customer could read another
customer's records by changing an identifier in the URL. The list endpoint
filtered correctly by owner; the detail endpoint did not check at all. Every
automated tool had passed it, because from the outside the request looked exactly
like a legitimate one — which is precisely what it was, except for who was making
it.

The same review found the test environment authenticating to a third-party
service with the **same key as production**. Individually a housekeeping note;
combined with any weakness in the less-guarded environment, it is a path into the
real one.

## Related

- [`keep-secrets-out-of-the-repository`](../keep-secrets-out-of-the-repository/SKILL.md)
  — where credentials leak from, and what to do the moment one does
- [`route-work-to-the-right-model`](../route-work-to-the-right-model/SKILL.md) —
  anything on this page is level 3: three validations, one trying to break it
- [`map-an-undocumented-system`](../map-an-undocumented-system/SKILL.md) — you
  cannot secure what nobody can describe
- [`review-code-you-did-not-write`](../review-code-you-did-not-write/SKILL.md) —
  authorisation checks are exactly what a plausible-looking diff omits
