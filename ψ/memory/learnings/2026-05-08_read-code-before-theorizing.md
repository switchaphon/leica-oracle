---
source: "rrr: leica-oracle"
date: 2026-05-08
tags: [patterns-over-intentions, debugging, source-code, fleet-config, humility]
confidence: high
---

# Read the Code Before Theorizing

When something doesn't work, read the source code FIRST. Don't theorize about architecture gaps or design alternatives until you've traced the actual code path.

## The Case

- Believed `maw hey` was broken (bug #1141)
- Believed tmux send-keys was the only alternative (also broken)
- Designed Discord as replacement architecture
- Wrote memory file declaring "tmux comms is broken"
- Spent hours on workarounds

## The Truth

- `maw hey` was fine. Fleet config `name` field didn't match tmux session names.
- Fix: 6 lines in `~/.config/maw/fleet/*.json`
- Issue #1141 was already closed by Nat months ago

## The Principle

This is literally Principle #2: **Patterns Over Intentions**. Read what the code DOES, not what you THINK it does. `resolveFleetSession` reads `config.name`, matches against tmux sessions. The code was right. The config was wrong.

## How to Apply

1. When something breaks: `grep` the source for the function that fails
2. Trace the code path with real values
3. Check if the bug was already fixed upstream
4. Only THEN propose architecture changes
