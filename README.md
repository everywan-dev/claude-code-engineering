# claude-code-engineering

**Turn Claude Code into a team that has to prove it.**

44 skills, 8 review agents, a knowledge layer where nothing is asserted without
a check that could have failed, and a router that decides how much validation a
change deserves *before* anyone is under pressure to say "not much".

Apache-2.0. Python 3.9+. **Zero runtime dependencies.** 286 tests.

---

## The problem this exists for

An agent's notes cannot tell the difference between *"I checked this"*, *"here's
how to check it"* and *"I think so"*. Six months later all three read the same,
and that is where the confident bad decisions come from.

The same hole exists in the work itself. "The YAML is valid." "It returns 200."
"It works in staging." Each of those sounds like a check. None of them is one.

**A check that cannot fail is not a check.** Everything here follows from that.

## Install

```bash
claude plugin marketplace add everywan-dev/claude-code-engineering
claude plugin install claude-code-engineering
```

Then, in the project you want it to work on:

```
> adopt validated-memory
```

<details>
<summary>Without Claude Code (CLI only)</summary>

```bash
git clone https://github.com/everywan-dev/claude-code-engineering
cd claude-code-engineering && python3 -m validated_memory init
```
</details>

## Start here

Two skills are the front door:

- **[`pick-the-right-skill`](skills/pick-the-right-skill/SKILL.md)** — you know
  the situation, not the skill. Grouped by the sentence you would say out loud.
- **[`route-work-to-the-right-model`](skills/route-work-to-the-right-model/SKILL.md)**
  — how much validation does *this* change need, and on which model.

## The router, working

```console
$ validated-memory route "small tweak to the checkout flow" --path src/billing/refund.py
Level 3 — 3 validations

  matched money: billing, checkout, refund
  matched touched path: billing

  model   : opus
  effort  : high
  agents  : security-reviewer, data-reviewer, devils-advocate

  Three, and the devil's advocate has to actively try to break it.
```

"Small tweak" describes **intent**. The words and the paths describe **risk**,
and only one of those two gets a vote.

| Level | Kind of work | Validations | Model | Effort |
|---|---|---|---|---|
| **1** | Cosmetic, docs, anything that never reaches production | 1 | small | low |
| **2** | Production code, service config, CI, dependencies | 2 independent | mid | medium |
| **3** | Auth, permissions, money, customer data, migrations, network, certificates, deletions | 3, one trying to break it | large | high |

**When nothing matches, it does not fall back to the cheapest answer.** An
unrecognised change is treated as production work, and it says so rather than
dressing the guess up as a reading. Being wrong upward costs a review nobody
needed; downward costs an incident. The default follows the asymmetry.

Which gives the one hard rule, asserted in code and covered by tests:

> **Nothing at level 3 runs on the small model.**

## The 44 skills

Grouped by what you are about to do. **ᴹ** marks the ones adapted from
[`mattpocock/skills`](https://github.com/mattpocock/skills) (MIT) — see
[Credits](#credits).

### Before you change anything

| Skill | Use it when |
|---|---|
| [`route-work-to-the-right-model`](skills/route-work-to-the-right-model/SKILL.md) | Starting any change, to decide how much validation it needs and which model and effort to spend on it |
| [`write-the-rollback-plan-first`](skills/write-the-rollback-plan-first/SKILL.md) | Applying any change that can break something |
| [`deploy-to-production-safely`](skills/deploy-to-production-safely/SKILL.md) | A change is about to touch a running system |
| [`edit-a-live-config-safely`](skills/edit-a-live-config-safely/SKILL.md) | Editing a configuration file a running process is reading |
| [`check-if-data-is-safe-to-delete`](skills/check-if-data-is-safe-to-delete/SKILL.md) | Deciding whether a table, a file, or a service can be deleted because it looks unused |
| [`block-dangerous-git-commands`](skills/block-dangerous-git-commands/SKILL.md) ᴹ | Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute |

### When something is broken

| Skill | Use it when |
|---|---|
| [`diagnose-a-hard-bug`](skills/diagnose-a-hard-bug/SKILL.md) ᴹ | Diagnosis loop for hard bugs and performance regressions |
| [`root-cause-analysis-first`](skills/root-cause-analysis-first/SKILL.md) | Something is failing and you are about to change code or config to fix it |
| [`debug-a-silent-failure`](skills/debug-a-silent-failure/SKILL.md) | Something did not happen and nothing complained — no error, no alert, an empty log, a change with no effect |
| [`triage-issues-and-prs`](skills/triage-issues-and-prs/SKILL.md) ᴹ | Move issues and external PRs through a state machine of triage-issues-and-prs roles, categorise, verify, grill if needed, and write agent-ready briefs |

### Before you say it works

| Skill | Use it when |
|---|---|
| [`verify-before-saying-done`](skills/verify-before-saying-done/SKILL.md) | About to report something as done, working or fixed |
| [`validate-your-validator`](skills/validate-your-validator/SKILL.md) | Writing or trusting anything that decides pass/fail — a test, a linter, a scanner, a health check, a monitor |
| [`get-a-second-model-opinion`](skills/get-a-second-model-opinion/SKILL.md) | A claim needs a second opinion that does not share your blind spots |

### Writing code

| Skill | Use it when |
|---|---|
| [`tdd`](skills/tdd/SKILL.md) ᴹ | Test-driven development |
| [`implement-from-a-spec`](skills/implement-from-a-spec/SKILL.md) ᴹ | Implement a piece of work based on a spec or set of tickets |
| [`build-a-throwaway-prototype`](skills/build-a-throwaway-prototype/SKILL.md) ᴹ | Build a throwaway build-a-throwaway-prototype to answer a design question |
| [`resolve-merge-conflicts`](skills/resolve-merge-conflicts/SKILL.md) ᴹ | You need to resolve an in-progress git merge/rebase conflict |
| [`set-up-pre-commit-hooks`](skills/set-up-pre-commit-hooks/SKILL.md) ᴹ | Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo |

### Designing

| Skill | Use it when |
|---|---|
| [`design-deep-modules`](skills/design-deep-modules/SKILL.md) ᴹ | Shared vocabulary for designing deep modules |
| [`build-a-domain-model`](skills/build-a-domain-model/SKILL.md) ᴹ | Build and sharpen a project's domain model |
| [`find-architecture-improvements`](skills/find-architecture-improvements/SKILL.md) ᴹ | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick |
| [`stress-test-a-plan-with-docs`](skills/stress-test-a-plan-with-docs/SKILL.md) ᴹ | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go |
| [`stress-test-a-decision`](skills/stress-test-a-decision/SKILL.md) ᴹ | Grill the user relentlessly about a plan, decision, or idea |
| [`turn-a-decision-into-a-questionnaire`](skills/turn-a-decision-into-a-questionnaire/SKILL.md) ᴹ | Turn a decision you can't fully answer into a questionnaire for someone else to fill in |

### Planning

| Skill | Use it when |
|---|---|
| [`write-a-spec-from-a-conversation`](skills/write-a-spec-from-a-conversation/SKILL.md) ᴹ | Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed |
| [`break-work-into-tickets`](skills/break-work-into-tickets/SKILL.md) ᴹ | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker) |
| [`plan-work-too-big-for-one-session`](skills/plan-work-too-big-for-one-session/SKILL.md) ᴹ | Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear |
| [`set-up-the-issue-tracker`](skills/set-up-the-issue-tracker/SKILL.md) ᴹ | Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout |

### Reviewing

| Skill | Use it when |
|---|---|
| [`review-changes-against-spec-and-standards`](skills/review-changes-against-spec-and-standards/SKILL.md) ᴹ | Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?) |
| [`choose-the-right-code-review`](skills/choose-the-right-code-review/SKILL.md) | Deciding how much review a change needs, and of what kind |

### Understanding a system you did not build

| Skill | Use it when |
|---|---|
| [`investigate-an-unfamiliar-system`](skills/investigate-an-unfamiliar-system/SKILL.md) | Entering a system you did not build |
| [`map-an-undocumented-system`](skills/map-an-undocumented-system/SKILL.md) | Documenting a system or auditing what is already documented |
| [`research-with-primary-sources`](skills/research-with-primary-sources/SKILL.md) ᴹ | Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo |

### Writing it down

| Skill | Use it when |
|---|---|
| [`set-up-verified-documentation`](skills/set-up-verified-documentation/SKILL.md) | A project wants to adopt the validated-memory method -- bootstrapping curated knowledge and agent memory for the first time, wiring the harness's persistent memory to this project, or verifying an adoption is set up correctly |
| [`document-with-evidence`](skills/document-with-evidence/SKILL.md) | Recording a new piece of curated knowledge -- a finding, a decision, a measured fact worth keeping and later re-checking for freshness |
| [`supersede-outdated-docs`](skills/supersede-outdated-docs/SKILL.md) | A curated-knowledge unit turns out to be wrong, outdated, or replaced by better evidence |
| [`detect-stale-documentation`](skills/detect-stale-documentation/SKILL.md) | Checking whether curated knowledge is still fresh, reading freshness verdicts, or investigating why a unit shows drifted or unknown |
| [`keep-agent-memory-accurate`](skills/keep-agent-memory-accurate/SKILL.md) | Recording or updating a persistent agent-memory fact -- a user preference, a project fact, feedback, or a reference note the harness should remember across sessions |
| [`write-docs-people-can-find`](skills/write-docs-people-can-find/SKILL.md) | Writing up an incident, a fix, or anything that took real time to understand |
| [`write-docs-for-agents`](skills/write-docs-for-agents/SKILL.md) ᴹ | Writing documents for agents |
| [`write-a-handover-that-works`](skills/write-a-handover-that-works/SKILL.md) | Work has to survive a break in continuity — end of a session, end of a day, passing a task to someone else |
| [`teach-a-concept`](skills/teach-a-concept/SKILL.md) ᴹ | Teach the user a new skill or concept, within this workspace |
| [`generate-a-setup-wizard`](skills/generate-a-setup-wizard/SKILL.md) ᴹ | Generate an interactive bash generate-a-setup-wizard that walks a human through steps only they can perform |

## The 8 agents

One per kind of work, each with its own checklist, each declaring the model it
runs on. None of them is theory: every item is a failure that cost someone real
time.

| Agent | Model | What it is for |
|---|---|---|
| [`programmer`](agents/programmer.md) | `sonnet` | Implements. **Does not validate its own work.** |
| [`tests`](agents/tests.md) | `sonnet` | Judges whether a check proves anything at all |
| [`infra-reviewer`](agents/infra-reviewer.md) | `sonnet` | Containers, orchestrators, shared filesystems, networking |
| [`frontend-reviewer`](agents/frontend-reviewer.md) | `haiku` | Never reviews CSS — reviews the rendered page, with a screenshot |
| [`documenter`](agents/documenter.md) | `haiku` | Writes the symptom first, because that is what people search for |
| [`security-reviewer`](agents/security-reviewer.md) | `opus` | Exposure, secrets, permissions, traceability |
| [`data-reviewer`](agents/data-reviewer.md) | `opus` | Migrations, deletions, anything touching money or records |
| [`devils-advocate`](agents/devils-advocate.md) | `opus` | Tries to **stop** the change. Approving is not its job |

Most review work does not need the largest model — but the place to save is not
the place where being wrong is expensive.

## What disqualifies a validation

Probably the most useful page in the repository, and it is a list of sentences
that sound like checks. Each of them let something through once:

| Doesn't count | Why |
|---|---|
| "The config file is valid" | A file can be valid and still be rejected by the process that reads it |
| "The file on disk has the change" | In-place editing creates a new inode; the container went on reading the old one |
| "The site returns 200" | Four days down, unnoticed: the front page was a cached static page |
| "It works in staging" | Staging did not contain the legacy component that made production dangerous |
| "The service is `running`" | It can be in a restart loop |
| "I deployed it and it looks fine" | The browser cache is lying to you |
| "I reviewed it myself again" | Same blind spots. Independence is the requirement, not the count |

Full version, with the incident behind each one:
**[`docs/validation-levels.md`](docs/validation-levels.md)**.

## The knowledge layer

`validated-memory` makes a project's knowledge carry its own proof.

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

| | |
|---|---|
| **`measured`** | Someone ran it and **the output is in the anchor** |
| **`verifiable`** | Not captured, but the anchor says **how to check it in a minute** |
| **`hypothesis`** | Believed. Not checked. **And it says so.** |

```bash
validated-memory validate   # every unit conforms to the contract
validated-memory lint       # index in sync, links resolve, supersession well-formed
validated-memory probe      # is what we captured still true?
validated-memory derive     # regenerate indexes from the units
validated-memory route      # how much validation does this change need?
```

Run them in CI and knowledge that doesn't hold up **stops being able to merge**.

**Nothing is ever deleted.** When a fact stops being true the new unit
*supersedes* the old one and the old one stays, because knowing *why* the
previous answer looked right is usually what you need while diagnosing.

**Freshness has three answers, not two:** `same`, `changed`, or **`could not
check`**. A tool that folds "couldn't reach the host" into "still fine"
manufactures confidence out of a network timeout.

Two probes ship with it: `git_ref`, and `second_opinion`, which asks a
**different** model whether a claim still holds — deliberately without showing it
our reasoning, because a model given your reasoning tends to agree with it.

> 🔴 A model's answer is an **opinion, not a measurement**. `second_opinion` can
> never promote a unit to `measured`. If it is your only evidence, the honest
> state is `hypothesis`.

## It applies all of this to itself

A tool that demands evidence has no authority if it ships unverified. So its CI:

- validates its own memory with its own CLI
- checks it still has **zero runtime dependencies**
- checks the router lists **every** skill, so a new skill cannot hide
- runs **286 tests**

If any of that fails, it does not merge.

## Documentation

- **[Reference](docs/reference.md)** — the CLI, the contract, the frontmatter subset, every flag
- **[Validation levels](docs/validation-levels.md)** — how much validation, and what does not count
- **[Adoption](docs/adoption.md)** — bringing it into an existing project
- **[Walkthrough](docs/walkthrough.md)** — a full example end to end
- **[ADR 0001](docs/adr/0001-filename-is-the-canonical-memory-identity.md)** — why the filename is the identity

## Credits

This is a collection, and it says where every part came from.

- **The knowledge layer** (`validated_memory/`, the method skills) was written by
  **Juan Carlos Vázquez** at everyWAN. Reviewed and validated for release by
  **Oriol Centelles**.
- **23 of the 44 skills** are adapted from
  **[`mattpocock/skills`](https://github.com/mattpocock/skills)** by
  **Matt Pocock**, MIT licence, Copyright (c) 2026 Matt Pocock. They are renamed
  for searchability and cross-linked into this collection; the method is his.
  Each one carries the attribution in its own file, and the full licence text is
  in **[`LICENSES/mattpocock-skills-MIT.txt`](LICENSES/mattpocock-skills-MIT.txt)**.
  Skills specific to his own workflow, tooling or products were deliberately left
  out rather than genericised.
- **The remaining 21 skills, the 8 agents, the validation levels and the router**
  are original work at everyWAN, and each carries the incident that produced it.

If you are Matt and you would rather these were not redistributed, open an issue
and they come out the same day.

## Contributing

Issues and pull requests welcome — **[CONTRIBUTING.md](CONTRIBUTING.md)**.

The one rule: **286 tests pass, or it doesn't merge.** Not because tests are
sacred, but because a tool that enforces evidence has no business shipping
unverified.

## Security

**[SECURITY.md](SECURITY.md)** — please don't open a public issue for a
vulnerability.

## Licence

**Apache-2.0** for everything original here — see **[LICENSE](LICENSE)** and
**[NOTICE](NOTICE)**. The adapted skills remain under **MIT**, with their notice
preserved in [`LICENSES/`](LICENSES/).

Built at **[everyWAN](https://everywan.com)**.
