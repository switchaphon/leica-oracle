# multi-agent-workflow-kit Learning — 2026-06-11

**Mode**: deep (5 agents) | **Focus**: Worktree isolation for multi-engine teams

## What It Is
Python+Bash toolkit that orchestrates parallel AI agents in isolated git worktrees with tmux. Engine-agnostic: works with Claude, Codex, OpenCode, Aider, or humans.

## Key Findings
- **agents.yaml**: Single source of truth — `model:` field is metadata only (not enforced)
- **Worktree isolation**: Each agent gets `agents/<name>/` dir + `agents/<name>` branch
- **Codex integration**: `.codex/prompts/` auto-synced from `.claude/commands/`
- **maw command**: Shell function (not binary) sourced via direnv `.envrc`
- **6 tmux profiles**: profile0 (3-pane) through profile5 (6-pane dashboard)
- **v0.5.1**: Early/PoC stage — no health monitor, no auto-recovery yet

## Agent Files (not written — Explore agents are read-only)

| Topic | Agent | Key Finding |
|-------|-------|-------------|
| Architecture | mawk-arch | Git worktree + tmux + direnv coordination layer |
| Code Snippets | mawk-snippets | Transport abstraction, federation auth v1/v2/v3 |
| Quick Reference | mawk-ref | 28 maw commands, 6 layout profiles |
| Testing | mawk-test | pytest, subprocess testing, no AI engine mocking |
| API Surface | mawk-api | Shell function interface, no formal plugin API |
