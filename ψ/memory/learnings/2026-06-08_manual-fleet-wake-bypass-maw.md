# Manual Fleet Wake Bypasses maw's Inline-Prompt Limit

**Date**: 2026-06-08
**Source**: Fleet inbox drain orchestration session

## Problem

maw-js `wake-inbox-drain.ts` inlines the full inbox content as a `-p '...'` argument via tmux send-keys. When inbox exceeds ~20-30KB, the command is too long and wake crashes with "command too long".

## Workaround

Create a temporary tmux session, launch Claude directly:

```bash
# Shared session for all oracles
tmux new-session -d -s inbox-drain -n oracle-name -c /path/to/oracle-repo

# Launch with prompt (bypasses maw's drain mechanism)
tmux send-keys -t inbox-drain:oracle-name \
  "export DISCORD_STATE_DIR=... && claude -p 'อ่าน inbox ทั้งหมด...'" Enter
```

Oracle reads its own inbox via file system, not via command argument. No size limit.

## Pattern: Ephemeral Fleet Infrastructure

For one-time fleet-wide operations:
1. Create temporary tmux session
2. One window per oracle
3. Launch Claude with task prompt
4. Wait for completion (all exit to zsh)
5. Kill the session

This doesn't scale past ~15 oracles on one machine (concurrent Claude sessions). For larger fleets, batch in waves.
