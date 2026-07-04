# Lesson: Codex as implementer, Claude Code as lead (tmux + BRIEF.md)

**Date**: 2026-06-10
**Context**: Leica taught the proven dual-AI workflow — OpenAI Codex (GPT-5.5) implements, Claude Code leads
**Source**: Leica via Oracle thread #5 + inbox 2026-06-10_05-22; proven on Rust Discord bot (1,824 lines / 6 min / 10 tests pass / 0 unwrap / clippy clean)

## The Workflow

### Step 1 — tmux pane next to the project
```bash
tmux split-window -h -c "/path/to/project"
```

### Step 2 — open Codex in the new pane
```bash
source "$HOME/.cargo/env"   # only if Rust needed
codex
```

### Step 3 — write BRIEF.md FIRST
Clear spec in the project root: file structure, rules, phases, verification criteria. Never assign work verbally/inline.

### Step 4 — send the brief
```bash
tmux send-keys -t {pane} 'Read BRIEF.md and implement all phases' Enter
```

### Step 5 — monitor + approve
- Codex asks approval for `cargo build` / `git add` / `git commit` → send `y` Enter
- Capture progress: `tmux capture-pane -t {pane} -p -S -20`

### Step 6 — review like a lead, not a rubber stamp
1. Read EVERY file of actual code — not just "build passed"
2. Check every criterion in the brief
3. All pass → approve + commit
4. Fail → send specific feedback back to Codex to fix (loop)

## Key Rules

- **Brief before work, always** — the brief is the contract; review is against the brief
- **Review code, not test results** — green CI is not a review
- **Codex doesn't know the Oracle system** — never send tasks touching `ψ/` or Oracle MCP
- **Best-fit tasks**: clear implementation work — utility functions, API handlers, data models, DB schema, Rust/TypeScript modules

## Fit for pops-clinic (my read)

- ✅ Good Codex tasks: `_utils/` functions, GraphQL operation wiring, Zod schemas, data-model constants, mock-data generators
- ⚠️ Brief must embed vet conventions when relevant: SWR tuple keys, 'use client' + `_pages/` proxy, DS-first, never touch production from prototype work
- ❌ Never: anything needing ψ/ brain, Oracle MCP, federation context, or design judgment (that's mine + Neon's)

This mirrors my existing role: I dispatch, they execute, I check the merges — Codex is simply a new executor tier alongside team subagents.

## Tags

codex, dual-ai, delegation, tmux, brief-driven, workflow, leica-lesson
