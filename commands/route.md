---
allowed-tools: Bash(python3 -m validated_memory route:*), Bash(validated-memory route:*), Bash(git diff --name-only:*), Bash(git status --porcelain:*)
description: Decide how much validation a change needs, and which agents and model
disable-model-invocation: false
---

Decide how much validation the user's change deserves, before they are under
pressure to say "not much".

`$ARGUMENTS` is what they are about to do, in their own words. If it is empty,
describe the current change from the working tree instead.

Follow these steps precisely:

1. **Work out which files the change touches.** If the user named files, use
   those. Otherwise run `git diff --name-only HEAD` and `git status --porcelain`
   and use the paths from both — staged, unstaged and untracked. If the working
   tree is clean and `$ARGUMENTS` is empty, ask what they are about to do and
   stop.

2. **Run the router**, passing every touched file with its own `--path`. Prefer
   the console script; fall back to the module form, which is what works from an
   installed plugin where the CLI is not on the `PATH`:

   ```bash
   validated-memory route "$ARGUMENTS" --path FILE [--path FILE ...]
   # or
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m validated_memory route "$ARGUMENTS" --path FILE [...]
   ```

3. **Report its answer verbatim first.** The level, the matched signals, the
   model, the effort and the agents. Do not paraphrase and do not soften it. The
   value of this command is that the reasoning is visible, so the user can
   disagree with a specific signal rather than with a verdict.

4. **If it reports that no signal matched**, say so plainly and explain that the
   level 2 answer is the safe direction rather than a reading of their change.
   Then ask whether it touches authentication, permissions, money, customer data,
   migrations, network rules or certificates — and if it does, re-run with that
   said explicitly in the description.

5. **Do not argue the level down.** If the user thinks it is too high, the way to
   change the answer is to change the description or the signal list, both of
   which are visible and editable. Negotiating the number in conversation is the
   exact failure this command exists to prevent.

6. **Then say what happens next**, concretely:
   - **Level 1** — one review. Name which of the two agents fits.
   - **Level 2** — two independent reviews. State plainly that the agent or
     person who implemented it is not one of the two, and that reviewing one's
     own work a second time does not count.
   - **Level 3** — three, and one of them has to actively try to break the
     change. Approving is not the devil's advocate's job.

7. **Offer the matching skill** for what they are about to do, using
   `pick-the-right-skill` if nothing obvious fits. For level 3 specifically,
   `map-the-attack-surface` and `write-the-rollback-plan-first` are almost always
   worth reading before starting.

Keep the whole response short. This command answers one question; it is not a
review, and it never gates anything — it exits 0 by design.
