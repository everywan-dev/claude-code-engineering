# Security policy

## Reporting a vulnerability

**Please don't open a public issue.**

Email **security@everywan.com** with:

- what you found
- how to reproduce it
- what an attacker could do with it

You'll get an acknowledgement within **3 working days** and an assessment within
**10**. If it's real we'll agree a disclosure date with you, and you get credit
unless you'd rather not.

## Supported versions

| Version | Supported |
|---|---|
| 1.x | ✅ |
| < 1.0 | ❌ |

## What this tool touches

Worth knowing when you assess the risk:

- **It runs commands you configure.** `probe` executes the command registered for
  an anchor's `kind` in `validated-memory.md`. That file is part of the adopting
  project: **treat it as code, not as data.** Reviewing a pull request that
  changes it is reviewing a command that will run on your machine and in your CI.
- **It reads and writes Markdown** inside the adopting project. It does not phone
  home, and it has no network code of its own.
- **It has no runtime dependencies.** Nothing is pulled at install time, so
  there's no dependency surface beyond the Python standard library.
- **The startup hook** (`hooks/`) touches the agent-memory layout of the project
  that adopts it. What it does is documented in `docs/adoption.md`; read that
  before adopting in a project whose memory you care about.

## What is *not* a vulnerability

- The tool trusting `validated-memory.md`. That's by design, and it's documented
  above — the same way a `Makefile` is trusted.
- A knowledge unit containing a secret. The tool doesn't scan for those; keeping
  secrets out of your documentation is your policy, and worth enforcing in CI.
