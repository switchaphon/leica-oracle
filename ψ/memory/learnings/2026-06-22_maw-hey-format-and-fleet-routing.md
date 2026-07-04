# maw hey format and fleet routing

**Date**: 2026-06-22
**Source**: rrr: leica-oracle
**Tags**: maw, fleet, routing, messaging

## Lesson

`maw hey` has two forms with completely different routing:

| Format | Meaning | Use case |
|--------|---------|----------|
| `maw hey <session> "msg"` | Send to another session | Cross-oracle messaging |
| `maw hey <session>:<member> "msg"` | Send to a member within a team | Dispatching to codex coders |

**Never** use `session:session` — it tries to find a window named after the second session inside the first session, which doesn't exist.

## Fleet orphan routing

If an oracle shows `[orphan]` in `maw ls`, `maw hey` will persist to inbox but NOT deliver live. Fix: `maw fleet renumber` to reassign proper slot numbers. Fallback: `maw send-enter <session> "msg"` sends directly to tmux.

## Inbox delivery varies

Some oracles read `ψ/inbox/` via filesystem, others via MCP (e.g. arra-oracle-v3). `maw hey` and manual inbox file drops go to filesystem. If an oracle uses MCP for inbox reading, files may be invisible. `maw send-enter` is the reliable fallback for guaranteed delivery.
