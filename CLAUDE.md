# validated-memory — development conventions

- Runtime code is Python 3, **standard library only**. pytest is the only
  development dependency.
- All content in this repo (code, comments, CLI messages, docs, skills) is
  written in **English**.
- This repo is self-contained: no references to internal company projects.
- Exit code convention: `0` = clean or WARNING-only findings; `1` = ERROR
  (gates); `2` = usage error.
- Testing seam: the CLI invoked as a subprocess over fixture adopter trees,
  asserting on exit codes, output, and produced files. Tests never import the
  package's internals.
- Work on `feature/*` branches; never force-push `main`.
