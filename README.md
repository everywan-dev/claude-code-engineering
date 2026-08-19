# everywan-agents

**Agent engineering that proves what it claims.**

Nineteen skills, eight review agents, and a knowledge layer
(`validated-memory`) where nothing is asserted without a check that could
have failed.

---

**Your agent's notes lie to you — not on purpose, but because Markdown can't tell
the difference between *"I checked this"*, *"here's how to check it"*, and *"I
think so"*.**

Six months later all three read the same. That's where the bad decisions come
from.

`validated-memory` makes an agent project's knowledge carry its own proof:

```yaml
---
id: kb-0004
evidence: measured        # ← the whole point
anchors:
  - system: production
    kind: command
    captured_at: 2026-08-19
    payload:
      command: kubectl get nodes -o wide
---
```

![validated-memory catching a malformed unit](docs/media/demo.gif)

*A real recording — every line was executed. Regenerate with `vhs docs/media/demo.tape`.*

Three states, and they never blur:

| | |
|---|---|
| **`measured`** | Someone ran it and **the output is in the anchor**. |
| **`verifiable`** | Not captured, but the anchor says **how to check it in a minute**. |
| **`hypothesis`** | Believed. Not checked. **And it says so.** |

A tool that can't distinguish these will happily tell you a guess with the same
confidence as a measurement. This one won't.

---

## Install

```bash
claude plugin marketplace add everywan-dev/everywan-agents
claude plugin install validated-memory
```

Then, in the project you want to document:

```
> adopt validated-memory
```

That's it. Five skills become available and the CLI is on your path. No Python
environment to manage — the enforcement code lives in the plugin, your project
keeps only Markdown.

<details>
<summary>Without Claude Code (CLI only)</summary>

```bash
git clone https://github.com/everywan-dev/everywan-agents
cd validated-memory && python3 -m validated_memory init
```

Python 3.9+. No runtime dependencies.
</details>

## What you get

```bash
validated-memory validate   # every unit conforms to the contract
validated-memory lint       # index in sync, links resolve, supersession well-formed
validated-memory probe      # is what we captured still true?
validated-memory derive     # regenerate indexes from the units
```

Run them in CI and knowledge that doesn't hold up **stops being able to merge**.

### Nothing is ever deleted

When a fact stops being true, the new unit **supersedes** the old one and the old
one stays. Six months later you can still see *why* the previous answer looked
right — which is usually the thing you actually need.

Deleting it throws that away and leaves no trace that anyone ever believed it.

### Freshness has three answers, not two

`probe` re-runs what an anchor recorded and returns **same**, **changed**, or
**could not check**.

That third one matters more than it looks. A tool that folds "couldn't reach the
host" into "still fine" is worse than no tool at all: it manufactures confidence
out of a network timeout.

## Why this exists

It came out of running production infrastructure where the documentation was the
only thing standing between a change and an outage — and where the docs
confidently described a server that had been decommissioned months earlier.

The fix wasn't more documentation. It was making documentation **say how it knows
what it says**.

## Where it fits

| | |
|---|---|
| Documenting infrastructure an agent operates | ✅ what it's for |
| Runbooks that must not rot | ✅ |
| Onboarding — "what do we actually know here?" | ✅ |
| A personal notes app | ❌ overkill |
| Replacing your wiki | ❌ this is the layer *under* the wiki |

## Documentation

- **[Reference](docs/reference.md)** — the CLI, the base contract, the memory
  layer, the frontmatter subset, every flag
- **[Adoption](docs/adoption.md)** — bringing it into an existing project
- **[Walkthrough](docs/walkthrough.md)** — a full example end to end
- **[ADR 0001](docs/adr/0001-filename-is-the-canonical-memory-identity.md)** — why
  the filename is the identity

## The skills

**Nineteen.** Five drive the method; fourteen are practice — and every one of
those carries at least one real incident, because a checklist nobody paid for is
just an opinion with bullet points.

### The method

| Skill | When |
|---|---|
| `adopt-validated-memory` | Bootstrapping a project |
| `create-knowledge-unit` | Recording something new |
| `supersede-knowledge` | Something stopped being true |
| `probe-freshness` | Checking whether it still holds |
| `maintain-agent-memory` | Working the memory layer |

### The practice

| Skill | The lesson behind it |
|---|---|
| `verify-before-claiming` | "The YAML is valid" proved nothing. Neither did the 200. |
| `find-the-root-cause` | Three explanations, all confirmation-shaped, all wrong |
| `check-your-checker` | A secret scanner that incriminated itself three times |
| `trace-a-silent-failure` | Four days down. Nothing logged. The front end said 200. |
| `change-production-safely` | A rehearsal that passed, and the change stopped anyway |
| `edit-a-live-config` | A new inode the running process never read |
| `plan-the-undo-first` | The way back is written before the change, or there isn't one |
| `decide-if-data-is-dead` | Zero code references on tables with billions of reads |
| `write-the-symptom-first` | Nobody searches for the cause. They search for the symptom. |
| `route-the-review` | What "independent" actually costs, and what it means |
| `hand-off-work` | The section everyone drops: what was **not** verified |
| `map-what-you-dont-know` | Seven services in production nobody could explain |
| `cross-check-with-another-model` | A model reviewing itself shares its own blind spots |
| `read-an-unfamiliar-system` | The instrument that wasn't installed, printing "none" |

## The probes

`probe` re-checks anchors. Two ship with it:

- **`git_ref`** — resolves a repository ref and compares it with what was captured.
- **`second_opinion`** — asks a **different** model whether a claim still holds.
  Provider-agnostic: any endpoint speaking the common chat-completions shape,
  including one you run yourself. No dependencies, no key stored anywhere but
  the environment.

  🔴 **Its answer is an opinion, never a measurement.** `drifted` means another
  model disagrees — a reason to go and check, not proof. It can never be the
  basis for calling a unit `measured`. If it is your only evidence, the honest
  state is `hypothesis`.

  Unconfigured, it answers `unknown`, which is the honest answer.

## The agents

The same principle, applied to work instead of documentation: **a check that
cannot fail is not a check.**

`agents/` holds eight roles, one per kind of work, each with its own checklist.
None of them is theory — every item is a failure that cost someone real time.

| Agent | What it is for |
|---|---|
| `programmer` | Implements. **Does not validate its own work.** |
| `tests` | Judges whether a check proves anything at all |
| `infra-reviewer` | Containers, orchestrators, shared filesystems, networking |
| `security-reviewer` | Exposure, secrets, permissions, traceability |
| `data-reviewer` | Migrations, deletions, anything touching money or records |
| `frontend-reviewer` | Never reviews CSS — reviews the rendered page, with a screenshot |
| `devils-advocate` | Tries to **stop** the change. Approving is not its job. |
| `documenter` | Writes the symptom first, because that is what people search for |

Each agent declares which model it runs on, because most review work does not
need the largest one — but the place to save is not the place where being wrong
is expensive. `documenter` and `frontend-reviewer` run on `haiku`, the reviewers
on `sonnet`, and anything touching security, data or the devil's advocate on
`opus`. **Nothing at level 3 runs on `haiku`.**

**[`docs/validation-levels.md`](docs/validation-levels.md)** decides how many of
them a change needs. Cosmetic → one review. Production → two independent ones.
Authentication, money, data or networking → three, and one of them must actively
try to break it.

The most useful part of that document is the list of what **disqualifies** a
validation: "the YAML is valid", "the endpoint returns 200", "it works in
staging". Each of those let something through once.

## Contributing

Issues and pull requests welcome — see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

The one rule that matters: **253 tests pass, or it doesn't merge.** Not because
tests are sacred, but because a tool that enforces evidence has no business
shipping unverified.

## Security

Found something? **[SECURITY.md](SECURITY.md)** — please don't open a public
issue for a vulnerability.

## Licence

Apache-2.0. See **[LICENSE](LICENSE)** and **[NOTICE](NOTICE)**.

Built at [everyWAN](https://everywan.com). Originally written by Juan Carlos
Vázquez. Reviewed and validated for release by Oriol Centelles.
