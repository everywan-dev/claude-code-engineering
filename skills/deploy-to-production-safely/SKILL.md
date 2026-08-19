---
name: deploy-to-production-safely
description: Use when a change is about to touch a running system. Backup, dry run, rollback and per-node verification, in that order.
---

# Deploy to production safely

A production change is not a command. It is a sequence, and the sequence has an
order. Skipping a step does not make the change faster — it moves the cost to
the moment you can least afford it.

## The order

Do these in this order. Not in the order that feels natural.

| # | Step | Done when |
|---|---|---|
| 1 | **Photograph the starting state** | You have the output of the commands that describe the system *before*, pasted somewhere you can read later |
| 2 | **Take a copy — and verify it** | You have *listed the contents of the copy*, not just seen the file exist |
| 3 | **Write the rollback** | The exact commands that undo this are written down, before anything is applied |
| 4 | **Rehearse cold** | The tool's dry-run mode has been run and its output pasted |
| 5 | **Apply** | — |
| 6 | **Verify with a check that can fail** | You ran something that would have gone red if the change had not worked |

Step 3 comes before step 5 for one reason: the moment you need the rollback is
the moment you are least able to write it.

## Step 1 — Photograph the starting state

Whatever the change touches, capture it first: the list of processes, the
current configuration, the row counts, the routing table, the version in use.

You are not doing this for the change. You are doing it for the argument three
days later about whether the change caused the thing that broke.

## Step 2 — A copy you have not read is not a copy

🔴 **A dump nobody has opened is not a backup.** It is a file of unknown size and
unknown content that makes everyone feel safer than they are.

Verifying a copy means reading back from *the copy itself*:

- A database export → list the objects inside it and count them.
- A configuration file → open the saved copy and confirm the section you are
  about to change is present in it.
- A whole directory → count the entries in the archive, not on disk.

If the copy cannot be listed, it is not a backup and the change does not
proceed.

## Step 3 — The rollback, written down, before

Write the undo procedure as commands, not as intent. "Restore the backup" is
not a rollback. The rollback is the actual restore command, with the actual
path to the actual verified copy, and the actual restart afterwards.

Then answer these two out loud:

- ⚠️ **How long does the rollback take?** If restoring takes four hours, the
  rollback is not really available to you during an incident, and the change
  needs a different shape.
- ⚠️ **Does the rollback restore the data, or only the structure?** Those are
  very different promises and people confuse them constantly.

## Step 4 — Rehearse cold

If the tool has `--dry-run`, `--check`, `--noop`, a `try` mode, or a
transaction you can roll back — it gets used, and the output gets pasted, not
summarised.

⚠️ **A dry run that passes is not permission to proceed.** It is one input. Read
what it actually printed, especially the counts. An operation that reports it
will touch 40,000 records when you expected 40 has just told you the filter is
wrong.

## Step 5 — Apply

Smallest scope that is still a real test. One node, one tenant, one table.

## Step 6 — Verification that can fail

The check has to be capable of coming back red. These do not count:

| Not a verification | Why |
|---|---|
| "The configuration is valid" | Valid and correct are unrelated |
| "The service is running" | It was running before too |
| "It returns a success code" | Cached responses return success codes |
| "It works in the test environment" | The test environment is missing whatever makes production dangerous |

A verification that can fail looks like: query the thing that changed and
compare against the number you wrote down in step 1. Request the new path and
read the body, not the status. Log in as a real user.

And if the system has several nodes, **verify each node individually**, by
address, not through whatever balances traffic in front of them. See
`edit-a-live-config-safely` for why one node in four can be wrong for hours without
anyone seeing it.

## Real case — the authentication migration that was stopped after passing

A migration changed how stored credentials were verified. The failure mode was
total: if the migrated credentials did not validate, **nobody could log in**,
including the people who would have to fix it.

So it was rehearsed cold first, against a copy: 7 users, 13 registered devices,
0 errors. Everything the risk list mentioned was green.

It was stopped anyway.

The cold rehearsal surfaced a side effect nobody had listed — a behaviour change
that was harmless in the rehearsal and would not have been harmless with the
full user base behind it. The rehearsal did not just confirm the plan. It
produced a fact that was not in the plan.

**What this teaches:** the point of the rehearsal is not to collect a pass. It
is to look at what happens. A rehearsal you only read the exit code of has been
wasted.

## Real case — never apply network configuration on a remote machine

🔴 **The command that applies a new network configuration on a machine you reach
over the network can end the session and the machine's reachability in the same
instant.** There is no rollback, because there is no longer a way in.

The safe shape has three parts:

1. **Write the file.** Writing it changes nothing yet.
2. **Validate without applying.** Use the configuration checker, or the mode
   that reverts automatically if you do not confirm within N seconds.
3. **Bring the change up live with an operation that does not restart the
   network stack** — add the address, add the route. The file is there so the
   next boot agrees with the running state; it is not what you use to get
   there.

The same principle generalises: **never make the mechanism you are standing on
the mechanism you are changing.** Firewall rules, authentication, the routing
that carries your own session. If the change can lock you out, arrange to have a
second way in — a console, an out-of-band path, a scheduled automatic revert —
*before* you type it.

## When to stop

Stop and escalate, do not improvise, if:

- The copy cannot be verified.
- The dry run reports different numbers from the ones you expected.
- The rollback takes longer than the outage would.
- Something appeared that was not on the risk list. **That is a reason to stop,
  not a detail to note.**
