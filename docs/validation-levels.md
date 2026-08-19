# Validation levels by type of work

> **This is not a judgement call in the moment.** The type of work decides how many
> validations are required, and of what kind. This table is mandatory.

---

## The principle

A validation only counts if it **could have gone wrong**. Reading the code and
saying "looks fine" is not a validation: it's a reading. The question you have to be
able to answer is always the same:

> **What check did I run that, if the change were broken, would have failed?**

If there is no answer, the work is not validated — however many reviews it went
through.

## Independence

When the table asks for two or three **independent** validations, this is what that
means:

- Whoever validates **does not receive the reasoning** of whoever implemented. They
  receive the result and the acceptance criteria.
- The same agent reviewing itself in a later turn doesn't count. Same blind spots.
- At level 3, **one of the validations has to actively try to break it**, not
  confirm it. The reviewer's goal is to find the failure, not to sign off.

> **Why this matters.** A reverse proxy was restarting every 45 seconds. Three
> explanations were proposed — memory, a monitoring sidecar, the restart policy —
> and **all three were wrong**. Each one confirmed a hypothesis instead of trying to
> knock it down. The real cause appeared only when someone followed the process
> tree, which is to say when someone went looking for facts instead of support.

---

## The table

| Level | When | Validations | Who |
|---|---|---|---|
| **1** | Cosmetic, documentation, changes that never reach production | 1 | `frontend-reviewer` or `documenter` |
| **2** | Code in production, service configuration, CI, dependencies | 2 independent | `tests` + the reviewer for that area |
| **3** | Authentication, permissions, money, customer data, database migrations, network and firewall, deletions | 3, and **one of them trying to break it** | `tests` + the area reviewer + `devils-advocate` |

### Level 1 — cosmetic

A logo, a string, a colour, a document.

**Mandatory:** a screenshot of the rendered result. Reading the CSS doesn't count.

```bash
CHROME="${CHROME:-google-chrome}"
"$CHROME" --headless=new --disable-gpu --no-sandbox --window-size=1100,700 \
  --virtual-time-budget=12000 --screenshot=x.png https://the.domain/
```

> Three attempts at fixing a logo failed because each one wrote CSS without looking
> at the rendered DOM. The fourth worked, because it looked first.

### Level 2 — production

Services, CI, configuration, dependencies.

**Mandatory, all four:**

1. **Before**: baseline recorded — process list, image version, endpoint response.
   Without a picture of the "before" you cannot demonstrate an improvement.
2. **A check that can fail**: not "the config parses", but the service up and its
   log.
3. **Distributed verification**: if there are several nodes, go **node by node**,
   resolving the name to each address. Never through the domain — DNS can keep
   handing you the one node that works.
4. **Rollback written down and dry-run.** No rollback, no deploy.

### Level 3 — authentication, money, data, network

**Everything from level 2, plus:**

5. **A verified backup**, not merely a backup that was taken. A dump nobody has
   opened is not a backup:
   ```bash
   pg_restore --list backup.dump | rg -c 'TABLE DATA'
   ```
6. **A dry run** if the tool allows one (`--dry-run`, `--check`, `--noop`), with its
   output pasted.
7. **`devils-advocate`**: an agent whose only goal is to **break the change**. It
   gets the change and the criteria, and is asked to find the case where it fails.
   Its report is attached.
8. **Secrets and their rotation** reviewed: what is exposed, who can read it, what
   happens if it leaks.

> Real level 3 examples: migrating to a new authentication backend (if passwords
> stop validating, **nobody gets in**); rolling out a new job orchestrator next to
> the legacy one (both would have split the same work queue across hundreds of
> sites); a refund bug in a reporting panel that understated the liability.

---

## How it gets classified, without debate

If the change touches **any** of these, it is **level 3**:

- login, passwords, tokens, permissions, roles
- amounts, prices, refunds, balances, invoicing
- customer or patient data
- schema migrations, deletions, `TRUNCATE`, `DROP`
- network rules, firewall, NAT, routing
- certificates and their renewal
- anything that runs on every site in the fleet

If it touches production but none of the above: **level 2**.
If it never reaches production: **level 1**.

**When in doubt, go up a level.** Being wrong upwards costs half an hour. Being
wrong downwards once cost four days of a database being down in silence.

---

## What disqualifies a validation

| Doesn't count | Why |
|---|---|
| "The config file is valid" | A file can be valid and still be rejected by the process that reads it. A reverse proxy accepted a valid file containing a duplicate route, kept the **previous configuration in memory**, and said nothing. Everything worked until the next restart, when it all failed at once. |
| "The file on disk has the change" | `sed -i` creates a new inode, so the container went on reading the old file. You have to compare the disk **against what the container sees**. |
| "The site returns 200" | A service was down for four days without anyone noticing: the site returned 200 because the login page was a cached static page. |
| "It works in the test environment" | The test environment didn't contain the legacy component that made production dangerous, so it **could not** have detected the risk. |
| "The service is `running`" | It can be in a restart loop. You have to look at the status detail and the log. |
| "I deployed it and it looks fine" | The browser cache is lying to you. Cache header plus versioned filename, or you're looking at yesterday. |
| "I reviewed it myself a second time" | Same blind spots. Independence is the requirement, not the number. |

---

## The record

Every level 2 or level 3 job leaves a record in the project's `SESSION.md`:

```markdown
## <date> — <what was done>

**Level:** 2
**Baseline:** <the "before" output>
**Check that could have failed:** <command and output>
**Per-node verification:** node1 200 · node2 200 · node3 200 · node4 200
**Rollback:** <exact command>
**Validated by:** tests (✅) · infra-reviewer (✅)
**Not verified:** <whatever was left unchecked, if anything>
```

The **"Not verified"** field is mandatory. It may be empty, but it is **never
omitted**. It's the difference between "it works" and "I couldn't check that it
works".


---

## Which model runs which agent

Cost matters, and most review work does not need the largest model. But the
place to save is **not** the place where being wrong is expensive.

| Agent | Model | Why |
|---|---|---|
| `documenter` | `haiku` | Turning existing material into clear prose. Most of the volume, least of the risk. |
| `frontend-reviewer` | `haiku` | Take the screenshot, compare against the checklist. The evidence is an image either way. |
| `programmer` | `sonnet` | Writes against a spec someone else reviews. The reviewers are the safety net. |
| `tests` | `sonnet` | Bounded reasoning against a written criterion. |
| `infra-reviewer` | `sonnet` | Works through a checklist of known traps. The list does the hard part. |
| `security-reviewer` | `opus` | Imagining attack paths nobody wrote down. There is no checklist for the one you have not thought of. |
| `data-reviewer` | `opus` | Migrations, deletions, money. Expensive and often irreversible. |
| `devils-advocate` | `opus` | Its whole job is finding what everyone else missed. |

### The rule that overrides the table

🔴 **Nothing at level 3 runs on `haiku`.** Not the documenter, not the frontend
reviewer, not anything. If a change touches authentication, money, customer
data, schema migrations or networking, every agent in its chain moves up at
least one tier.

The table is the default for levels 1 and 2. Level 3 is where you stop
optimising for cost.

### Why this split and not "the cheapest that works"

Because "works" is measured after the fact, and the failures you are trying to
prevent are the ones nobody predicted. A cheaper model reviewing a migration
will usually be fine — and the one time it is not, it costs more than every
token you saved.

Set it in the agent's frontmatter:

```yaml
---
name: data-reviewer
description: ...
model: opus
---
```
