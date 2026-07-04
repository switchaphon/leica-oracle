# Stale Auto-Memory Is Worse Than No Memory

**Date**: 2026-06-15
**Source**: Codex playbook internalization session
**Tags**: memory, staleness, codex, traps

## Pattern

Auto-memory that describes an outdated workflow gives false confidence. When following it, you hit the exact traps the newer playbook warns about — but you don't know to check because you "already know" the answer.

## Evidence

`reference_codex_workflow.md` still described the interactive TUI + `tmux send-keys Enter` pattern. The Codex playbook (2026-06-11) explicitly lists this as Trap #1 — the most painful trap of all 11. If I'd spawned Codex using my own stale memory, I would have wasted an entire attempt.

## Rule

When a playbook, learning, or inbox supersedes an existing auto-memory:
1. Update the memory immediately — don't leave the old version "for reference"
2. The new version should contain the trap/warning, not just the correct pattern
3. If the old pattern was dangerous (not just suboptimal), note WHY it's wrong

Memory that says "do X" when X is now known to fail is an active hazard, not passive debt.
