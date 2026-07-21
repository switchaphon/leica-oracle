# Lesson: Destructive commands need confirmation -- including tmux

**Date**: 2026-06-17
**Source**: tmux kill-window incident in pops-vet session
**Context**: User asked to close a tmux window; I killed the active window without asking which one, destroying their speech-to-soap work session

## Lesson

`tmux kill-window`, `kill-pane`, and `kill-session` are destructive and irreversible -- same category as `git reset --hard` or `rm -rf`. Always run `tmux list-windows` first, show the list, ask which one by name/number, then kill with explicit `-t` target. Never interpret "this" in a destructive context without confirmation.

## Application

- Before any tmux kill command: list, show, ask, kill-by-name
- When "this" is ambiguous and the action is irreversible, always ask
- Don't mentally categorize tmux management as "casual" -- a running session IS the user's workspace
- The system prompt's "measure twice, cut once" applies to all destructive commands, not just git
