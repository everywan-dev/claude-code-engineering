# validated-memory

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
claude plugin marketplace add everywan-dev/validated-memory
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
git clone https://github.com/everywan-dev/validated-memory
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

Installing the plugin makes five skills invocable:

| Skill | When |
|---|---|
| `adopt-validated-memory` | Bootstrapping a project |
| `create-knowledge-unit` | Recording something new |
| `supersede-knowledge` | Something stopped being true |
| `probe-freshness` | Checking whether it still holds |
| `maintain-agent-memory` | Working the memory layer |

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
