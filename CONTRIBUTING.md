# Contributing

Thanks for looking. This is a small, opinionated tool — contributions are
welcome, and so is telling us it's wrong.

## The one hard rule

**The tests pass, or it doesn't merge.**

```bash
python3 -m pytest -q     # 252 tests, no runtime dependencies
```

Not because tests are sacred. Because a tool whose whole point is *"don't claim
what you haven't verified"* has no business shipping unverified.

If you change behaviour, the pull request adds a test that **would have failed
before**. A test that passes either way proves nothing.

## Before opening a pull request

1. `python3 -m pytest -q` — green
2. New behaviour has a test that fails without your change
3. The docs match what the code does now
4. One change per pull request. If the description needs the word "and", it's two.

## What we're looking for

**Good fits**

- New probe kinds (a probe re-checks an anchor and returns a ternary verdict)
- Better error messages — especially ones that say *what to do next*, not just
  what went wrong
- Bugs, with a reproduction

**Please open an issue first**

- New frontmatter fields in the base contract. The contract is deliberately
  small; extensions go in the adopter's own declared schema, not here.
- Anything that would make an existing project's units invalid

**Out of scope**

- Turning this into a wiki, a search engine, or a database. It's the layer
  *under* those.
- Evidence states beyond the three. Three is the point: adding a fourth is how
  you get back to everything looking the same.

## Style

Python 3.9+, standard library only. **No runtime dependencies** — that's a
feature, not an oversight: it means `python3` is the entire install story.

Write comments that explain *why*, not *what*. The code says what.

## Reporting something that isn't a bug

If the tool is confidently wrong about something, that's the most interesting
kind of issue. Open it with the unit that triggered it.
