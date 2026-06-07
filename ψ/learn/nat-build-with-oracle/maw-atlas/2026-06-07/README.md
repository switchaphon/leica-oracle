# maw-atlas Learning Materials

**Date**: 2026-06-07  
**Source**: `/Users/switchaphon/ghq/github.com/nat-build-with-oracle/maw-atlas/`  
**Purpose**: Discord fleet infrastructure for orchestrating Codex agents via Discord threads

## Files in this directory

### `1405_CODE-SNIPPETS.md`
Comprehensive code reference with 10 sections covering:
1. **Command dispatcher** (`index.ts`) — thin router to subcommands
2. **Discord REST client** (`lib/discord.ts`) — all API methods
3. **Thread management** (`commands/threads.ts`) — channel resolution, create, archive
4. **Watch command** (`commands/watch.ts`) — polls for new threads, applies guards, spawns workers
5. **Route command** (`commands/route.ts`) — daemon that forwards Discord messages to codex panes
6. **Spawn-session** (`commands/spawn-session.ts`) — orchestrator: team up → threads sync → route start
7. **Reverse bridge** (`lib/reverse-bridge.ts`) — polls pane output, detects changes, posts to Discord
8. **Watch guards** (`lib/watch-guards.ts`) — security gates (allowFrom, maxWorktrees) + cleanup
9. **Error handling patterns** — try-catch, notifications, daemon lifecycle
10. **Utility helpers** — snowflake comparison, arg parsing, atomic writes

## Architecture Overview

```
Discord Server
    ↓
maw atlas watch <channel>           ← Watches for new threads
    ↓
[allowFromGate] → [maxWorktreesGate]  ← Security guards
    ↓
Post "spawn codex? reply go"
    ↓
waitForGo (polls for "go" message)
    ↓
maw wake <worker-name>              ← Spawn tmux pane + worktree
    ↓
Update routing table + record pane
    ↓
maw atlas route daemon              ← Forward: Discord → Codex panes
    ↓
maw atlas route <pane-output>       ← Reverse: Codex → Discord threads
```

## Key Concepts

- **State machine** (`WatchState`): Tracks known threads, pending confirmations, spawned workers
- **Routing table** (JSON): Maps Discord thread IDs to tmux panes + agent names
- **Guards**: Pure functions that check allowFrom (user whitelist) and maxWorktrees (capacity)
- **Confirmation gate**: Human approval required before spawning — "reply go" to confirm
- **Polling loops**: Watch polls every 10s, Route polls every 5s, Reverse bridge continuous
- **Atomic writes**: File updates use temp → rename pattern to prevent corruption
- **Snapshot diffing**: Reverse bridge only posts pane output diffs, not full output

## Command Examples

```bash
# Watch a channel, auto-spawn workers when humans say "go"
maw atlas watch #atlas-work --interval=5000 --max-worktrees=10

# Start routing daemon (Discord → codex panes)
maw atlas route start --interval=5000

# Check routing status
maw atlas route status --json

# Sync routing table from team charters
maw atlas route sync

# Create threads for team members
maw atlas team-threads sync

# One-shot session setup
maw atlas spawn-session .maw/teams/atlas-m5.yaml

# List active threads
maw atlas threads --json
```

## Error Handling

- **allowFromGate**: Rejects threads from users not in access.json allowFrom list
- **maxWorktreesGate**: Rejects spawns when worker count ≥ max (default 10)
- **Timeout on confirmation**: Waits 10 min for "go", logs timeout, discards request
- **Daemon crashes**: Route daemon monitored by PID file, can restart with `maw atlas route start`
- **Discord API errors**: All API calls throw with `Discord ${status} ${method} ${path}` context

## Integration Points

- **maw team up <charter>**: Creates tmux windows + panes for team
- **maw wake <worker> --thread <thread-id>**: Spawns worktree agent, receives thread context
- **maw hey <pane> <message>**: Sends message to tmux pane (used by forward bridge)
- **maw peek <pane>**: Reads pane output (used by reverse bridge)
- **maw kill <worker>**: Kills worker when thread archived (cleanup)
- **maw atlas threads --json**: Lists Discord threads as JSON (used by route sync)

## Notable Design Decisions

1. **Confirmation gate required**: Prevents accidental spawns, requires human "go"
2. **Daemon pattern**: Route runs as detached background process with PID file
3. **Snapshot-based diffing**: Reverse bridge seeds on first poll, then only posts changes
4. **Access control file**: allowFrom/groups pattern in JSON, extensible for future ACLs
5. **Atomic file writes**: All JSON state persisted with temp file → rename (POSIX atomic)
6. **Snowflake ID ordering**: Messages sorted by Discord snowflake ID (timestamp embedded)
7. **Guard composition**: Guards are simple functions, composable in watch flow

## Testing Checklist

- [ ] Watch detects new thread
- [ ] Watch applies allowFromGate correctly (rejects unauthorized users)
- [ ] Watch applies maxWorktreesGate correctly (rejects when at capacity)
- [ ] Human replies "go" → watch spawns worker
- [ ] Human doesn't reply → watch times out after 10min
- [ ] Route daemon forwards Discord messages to codex panes
- [ ] Reverse bridge detects pane output changes and posts to Discord
- [ ] Route sync rebuilds routing table from team charters
- [ ] Cleanup removes worktrees when threads archived
- [ ] Route daemon survives restarts (PID file preserved)
