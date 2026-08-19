# The filename is a memory entry's canonical identity

`lint` resolves a `[[wikilink]]` by a memory's `name` frontmatter field, while
people writing wikilinks reach for the filename. When the two disagree, the
knowledge manager treats the filename (without `.md`) as canonical and repairs
`name` to match, rather than renaming the file to match `name`.

## Considered options

Measured on the largest real corpus available (110 entries, 202 wikilinks,
62 entries whose `name` differs from their filename):

- **Filename canonical, rewrite `name`** — resolving links go from 83 to 160.
  90 broken links are fixed, 13 working ones break (repairable in the same
  pass), and 29 stay broken because the target genuinely does not exist yet,
  which is the case the WARNING already exists for.
- **`name` canonical, rename the file** — preserves the 83 links that work
  today, but 36 of the 110 `name` values contain spaces, dots or capitals.
  They are shaped like `'Release owner — restriction LIFTED (approved
  2026-08-03)'`: a sentence with punctuation and a date, not an identifier.
  (Shape reproduced from the corpus, not quoted from it: the originals name
  people.) They are titles, so for a third of the corpus there is no rename
  to perform.

## Consequences

The human-readable title is not lost: it lives in the index, whose entry format
is already `- [Title](file.md)`. `name` becomes an identifier rather than a
label, which is what wikilink resolution needs it to be.

This does not change the contract `lint` enforces — resolution is still by
`name`. It fixes which of the two fields gives way when they disagree.
