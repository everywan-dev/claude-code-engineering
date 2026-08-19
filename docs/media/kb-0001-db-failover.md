---
id: kb-0001
evidence: hypothesis
anchors:
  - system: postgres
    kind: command
    captured_at: 2026-08-19
    payload:
      command: pg_isready -h replica-01
provenance: >-
  - Overheard in standup. Nobody has actually tested the failover.
---

# The replica takes over automatically

We think.
