---
name: pick-the-right-skill
description: Use when you do not know which skill fits the situation you are in. A router over every skill in this collection, grouped by what you are actually about to do.
---

# Pick the right skill

**A collection nobody can navigate is a collection nobody uses.**

Grouped by the sentence you would say out loud, not by category. Find your
sentence, take the skill.

## I am about to change something

- [`route-work-to-the-right-model`](../route-work-to-the-right-model/SKILL.md) — Use before starting any change, to decide how much validation it needs and which model and effort to spend on it. Answers "is this a one-review change or a three-review change?" without arguing about it.
- [`write-the-rollback-plan-first`](../write-the-rollback-plan-first/SKILL.md) — Use before applying any change that can break something. The way back is written and tested before the change, not improvised after it.
- [`deploy-to-production-safely`](../deploy-to-production-safely/SKILL.md) — A change is about to touch a running system. Backup, dry run, rollback and per-node verification, in that order.
- [`edit-a-live-config-safely`](../edit-a-live-config-safely/SKILL.md) — Editing a configuration file a running process is reading. Unique anchor, keep the inode, validate before applying, verify every node.
- [`check-if-data-is-safe-to-delete`](../check-if-data-is-safe-to-delete/SKILL.md) — Deciding whether a table, a file, or a service can be deleted because it looks unused. Measure real access, rename before deleting, and check the units of every counter.
- [`block-dangerous-git-commands`](../block-dangerous-git-commands/SKILL.md) — Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
- [`know-what-a-change-costs`](../know-what-a-change-costs/SKILL.md) — Shipping something that runs repeatedly — a job, a query, an agent loop, a pipeline

## Something is broken

- [`diagnose-a-hard-bug`](../diagnose-a-hard-bug/SKILL.md) — Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
- [`root-cause-analysis-first`](../root-cause-analysis-first/SKILL.md) — Something is failing and you are about to change code or config to fix it. Blocks the fix until you can say why it happens, and shows how to hunt a cause instead of confirming a guess.
- [`debug-a-silent-failure`](../debug-a-silent-failure/SKILL.md) — Something did not happen and nothing complained — no error, no alert, an empty log, a change with no effect. Teaches how to read absence as a symptom and where silence gets manufactured.
- [`triage-issues-and-prs`](../triage-issues-and-prs/SKILL.md) — Move issues and external PRs through a state machine of triage-issues-and-prs roles, categorise, verify, grill if needed, and write agent-ready briefs.
- [`survive-someone-elses-breaking-change`](../survive-someone-elses-breaking-change/SKILL.md) — Something that worked yesterday stopped working and you changed nothing, or before upgrading a dependency, runtime or platform
- [`make-the-next-failure-loud`](../make-the-next-failure-loud/SKILL.md) — An incident, or before shipping something whose failure would be invisible

## I am about to say it works

- [`verify-before-saying-done`](../verify-before-saying-done/SKILL.md) — About to report something as done, working or fixed. Turns "it looks right" into a check that could have failed.
- [`validate-your-validator`](../validate-your-validator/SKILL.md) — Writing or trusting anything that decides pass/fail — a test, a linter, a scanner, a health check, a monitor. Makes the checker prove it can fail before you believe a green result.
- [`get-a-second-model-opinion`](../get-a-second-model-opinion/SKILL.md) — A claim needs a second opinion that does not share your blind spots. How to ask a different model, what to send it, and how to settle a disagreement.
- [`review-code-you-did-not-write`](../review-code-you-did-not-write/SKILL.md) — You are about to approve, merge or ship code an agent or another person wrote and you do not fully understand

## I am writing code

- [`tdd`](../tdd/SKILL.md) — Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
- [`implement-from-a-spec`](../implement-from-a-spec/SKILL.md) — Implement a piece of work based on a spec or set of tickets.
- [`build-a-throwaway-prototype`](../build-a-throwaway-prototype/SKILL.md) — Build a throwaway build-a-throwaway-prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
- [`resolve-merge-conflicts`](../resolve-merge-conflicts/SKILL.md) — You need to resolve an in-progress git merge/rebase conflict.
- [`set-up-pre-commit-hooks`](../set-up-pre-commit-hooks/SKILL.md) — Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.
- [`keep-secrets-out-of-the-repository`](../keep-secrets-out-of-the-repository/SKILL.md) — Committing configuration, when a secret has already been committed, or when adding a secret scanner
- [`check-the-licence-before-you-copy`](../check-the-licence-before-you-copy/SKILL.md) — Pulling someone else's code, skills, prompts or configuration into your project, and before publishing anything that contains them

## I am designing something

- [`design-deep-modules`](../design-deep-modules/SKILL.md) — Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
- [`build-a-domain-model`](../build-a-domain-model/SKILL.md) — Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a CONTEXT.md, or recording or editing an ADR.
- [`find-architecture-improvements`](../find-architecture-improvements/SKILL.md) — Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
- [`stress-test-a-plan-with-docs`](../stress-test-a-plan-with-docs/SKILL.md) — A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
- [`stress-test-a-decision`](../stress-test-a-decision/SKILL.md) — Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
- [`turn-a-decision-into-a-questionnaire`](../turn-a-decision-into-a-questionnaire/SKILL.md) — Turn a decision you can't fully answer into a questionnaire for someone else to fill in.

## I am planning work

- [`write-a-spec-from-a-conversation`](../write-a-spec-from-a-conversation/SKILL.md) — Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed.
- [`break-work-into-tickets`](../break-work-into-tickets/SKILL.md) — Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
- [`plan-work-too-big-for-one-session`](../plan-work-too-big-for-one-session/SKILL.md) — Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
- [`set-up-the-issue-tracker`](../set-up-the-issue-tracker/SKILL.md) — Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills.

## I am reviewing

- [`review-changes-against-spec-and-standards`](../review-changes-against-spec-and-standards/SKILL.md) — Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\".
- [`choose-the-right-code-review`](../choose-the-right-code-review/SKILL.md) — Deciding how much review a change needs, and of what kind. What the change touches decides the level — not how big it looks, not how confident you feel.

## I do not understand this system

- [`investigate-an-unfamiliar-system`](../investigate-an-unfamiliar-system/SKILL.md) — Entering a system you did not build. The reading order that gets you oriented without breaking anything, and the false negatives that will fool you on the way.
- [`map-an-undocumented-system`](../map-an-undocumented-system/SKILL.md) — Documenting a system or auditing what is already documented. Records the edge of what is known, so that silence stops reading as "nothing there".
- [`research-with-primary-sources`](../research-with-primary-sources/SKILL.md) — Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
- [`map-the-attack-surface`](../map-the-attack-surface/SKILL.md) — Exposing something, after inheriting a system you did not build, or when a security review says "looks fine"

## I am writing it down

- [`set-up-verified-documentation`](../set-up-verified-documentation/SKILL.md) — A project wants to adopt the validated-memory method -- bootstrapping curated knowledge and agent memory for the first time, wiring the harness's persistent memory to this project, or verifying an adoption is set up correctly. Triggers on requests like "adopt validated-memory here", "set up curated knowledge for this project", "bootstrap the memory layer", or "wire the harness memory symlink".
- [`document-with-evidence`](../document-with-evidence/SKILL.md) — Recording a new piece of curated knowledge -- a finding, a decision, a measured fact worth keeping and later re-checking for freshness. Triggers on requests like "record this as knowledge", "write a knowledge unit for X", "capture this finding with evidence", or "add this to curated knowledge". Do not use for a quick personal or project preference; that belongs to the keep-agent-memory-accurate skill instead.
- [`supersede-outdated-docs`](../supersede-outdated-docs/SKILL.md) — A curated-knowledge unit turns out to be wrong, outdated, or replaced by better evidence. Triggers on requests like "correct kb-0003", "update this finding, it changed", "this knowledge unit is no longer true", or "supersede X with Y". Never use this to justify editing a unit's frontmatter or body in place.
- [`detect-stale-documentation`](../detect-stale-documentation/SKILL.md) — Checking whether curated knowledge is still fresh, reading freshness verdicts, or investigating why a unit shows drifted or unknown. Triggers on requests like "check freshness", "run the probes", "is this knowledge still current", "why does kb-0002 say unknown", or "read the knowledge index".
- [`keep-agent-memory-accurate`](../keep-agent-memory-accurate/SKILL.md) — Recording or updating a persistent agent-memory fact -- a user preference, a project fact, feedback, or a reference note the harness should remember across sessions. Triggers on requests like "remember that I prefer X", "note this project fact", "update this memory", or "this preference changed". Do not use for curated knowledge with evidence and freshness tracking; that belongs to document-with-evidence.
- [`write-docs-people-can-find`](../write-docs-people-can-find/SKILL.md) — Writing up an incident, a fix, or anything that took real time to understand. The reader six months from now searches by symptom, not by cause.
- [`write-docs-for-agents`](../write-docs-for-agents/SKILL.md) — Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.
- [`write-a-handover-that-works`](../write-a-handover-that-works/SKILL.md) — Work has to survive a break in continuity — end of a session, end of a day, passing a task to someone else. Writes the handoff that carries the evidence and names what was never checked.
- [`teach-a-concept`](../teach-a-concept/SKILL.md) — Teach the user a new skill or concept, within this workspace.
- [`generate-a-setup-wizard`](../generate-a-setup-wizard/SKILL.md) — Generate an interactive bash generate-a-setup-wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or running a one-off migration or cutover. Don't invoke this for steps the agent can perform itself.

## Still not sure

Start with [`route-work-to-the-right-model`](../route-work-to-the-right-model/SKILL.md).
It will not tell you which skill to read, but it will tell you how much this
change deserves to be second-guessed, which is usually the question underneath
the question.
