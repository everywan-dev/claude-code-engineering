# Demo

`demo.gif` is a **real recording**, not a mock-up: every line in it was executed.

Regenerate it after changing the CLI so the demo never drifts from the tool:

```bash
brew install vhs           # github.com/charmbracelet/vhs
vhs demo.tape
```

`kb-0001-db-failover.md` is the sample unit it uses.

The reason this is recorded rather than illustrated: a project whose entire
argument is *"don't claim what you haven't verified"* has no business shipping a
demo of output it never produced.
