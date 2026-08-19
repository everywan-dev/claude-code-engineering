---
name: edit-a-live-config-safely
description: Use when editing a configuration file a running process is reading. Unique anchor, keep the inode, validate before applying, verify every node.
---

# Edit a live config safely

Editing a configuration file that a process is already reading is not the same
as editing a source file. The file is an interface with something that is
running, and three of the four ways it goes wrong leave the file looking
perfectly correct afterwards.

## The four rules

### 1. Substitute by unique anchor. Never rewrite the file

Find an exact string, replace that string. Do not regenerate the file from a
template, do not "clean it up while you are there", do not reorder it.

⚠️ **Check that the anchor appears exactly once, before replacing.** Count it:

```bash
rg -c --fixed-strings 'the exact text you are anchoring on' path/to/config
```

If the count is not `1`, the anchor is wrong. Extend it — take more surrounding
lines until it is unique.

🔴 **This is how latent bombs get in.** A repeated anchor puts the change in the
wrong block, and the file is *still syntactically valid*. Nothing complains. The
process reloads happily. The change simply applies to the wrong service, the
wrong host, the wrong environment — and it is found weeks later by whoever is
debugging something that seems unrelated.

A file that fails to parse is a good outcome. It tells you immediately. The
dangerous edit is the one that parses.

### 2. Keep the inode

Write **in place**. Do not use anything that writes a temporary file and renames
it over the original.

Why: when a single file is mounted into a running process — a common way to
inject one config file without mounting a whole directory — the mount resolves
to the **inode**. Replace the file and the mount still points at the old inode.
The file on disk shows your change. The process is reading the previous
contents. Every tool you use to check agrees with you, and the process disagrees
with all of them.

The same trap catches anything holding an open file descriptor across the edit.

Safe: an in-place edit that opens and writes the existing file.
Unsafe: any "atomic write" helper, any `mv` of a new file over the old one, any
editor configured to write-then-rename.

After editing, confirm the inode did not change:

```bash
stat -c%i path/to/config   # GNU;  BSD/macOS: stat -f%i
# read it before and after the edit — it must be the same number
```

### 3. Validate before applying

If the software has a config check subcommand, a test mode, or a parser you can
run standalone, run it against the edited file **before** telling anything to
reload.

If it has none, parse it yourself with whatever reads that format. A YAML or
JSON file that will not parse is worth knowing about now rather than after the
reload.

⚠️ Validation proves the file is *well formed*. It says nothing about whether
the change landed in the right block — that is rule 1's job, and rule 1 is the
one that actually protects you.

### 4. If it lives on shared storage, touch it from every node and verify one by one

When the file sits on a filesystem shared between several machines, writing it
once is not enough.

The write propagates. **The change notification may not.** Different nodes see
the file at different moments, some caches only refresh on their own schedule,
and some processes only notice a file changed if they were told.

So:

- Touch the file from **every** node, so each one's local cache and each local
  watcher sees an event.
- Then **verify each node individually, by address**, not through whatever
  distributes traffic in front of them. Resolve the name to each address and
  test each one:

```bash
curl -sS --resolve the.name:443:<address-of-node-1> https://the.name/new/path -o /dev/null -w '%{http_code}\n'
# repeat, once per node address
```

If one node answers differently from the others, you have found it. Testing
through the front door would have given you a result that changes depending on
which node you happened to land on.

## Real case — the route only one node in four was serving

A new route was added to a shared configuration file used by four machines. The
file was written once, on the shared storage. The check afterwards was a request
to the public name: it worked. The change was called done.

Reports came back that the new path was intermittently unreachable. From the
outside the symptom looked exactly like a DNS problem — same name, different
answer depending on who asked, works for some people and not others. Time went
into DNS.

It was not DNS. Three of the four nodes had never reloaded. Whoever asked landed
on the one node that had, roughly a quarter of the time, and the request
succeeded. The other three quarters got the old configuration, which had no such
route.

**What this teaches:**

- 🔴 "Intermittent, depends who asks, looks like DNS" in a multi-node system is
  a **per-node state** symptom until proven otherwise.
- A single test through the load-balanced name **cannot** detect this. It has a
  1-in-4 chance of telling you the truth and a 3-in-4 chance of telling you
  nothing, and you have no way to know which one you got.
- The fix is not cleverer testing. It is testing every node by address, every
  time, in a fixed order, and writing down the answer for each.

## Checklist

- [ ] Anchor counted, exactly one occurrence
- [ ] Edited in place — inode unchanged
- [ ] Validated with the software's own check, or parsed
- [ ] Reload triggered from every node that reads the file
- [ ] Every node verified individually by address, and each answer recorded
- [ ] The previous content saved somewhere you can paste back from
