---
title: "Codex team complete reference — from Leica 2026-06-26"
date: 2026-06-26
source: "leica inbox message — consolidated codex-team teaching"
confidence: high
supersedes: ["2026-06-11_codex-team-playbook.md", "2026-06-16_codex-team-lifecycle-from-nat.md"]
tags: [codex, omx, maw, team, lifecycle, execution]
---

## omx = wrapper for OpenAI Codex CLI
- Manages tmux + worktree + HUD automatically
- Uses gpt-5.5 FREE under ChatGPT Pro subscription
- Does NOT cost Claude tokens

## 3 execution methods (lowest tier that works)

1. `codex exec -s workspace-write 'task'` — 1-2 tasks, no state, fire-and-forget
2. `omx team N:role 'task'` — omx manages tmux+worktrees, team coordination
3. `maw team up <name>` — full Oracle integration, charter YAML, branch isolation

## Skills available

- `/codex-team` — up/down/status/restart/scale with verification
- `/crew-up` — generic 8-phase team spinner, any repo/language

## 8-phase lifecycle

Charter → Trust → Spawn → Verify → Dispatch → Monitor → Merge → Teardown

## Critical gotchas

- maw hey ONLY for dispatching to omx coders (SendMessage = silent no-op)
- Charter YAML at ψ/teams/*.yaml = source of truth
- preflight uses PATH: `maw team preflight ψ/teams/name.yaml`
- team up/down uses NAME: `maw team up team-name`
- Dead agent: `maw done` first, then `maw team up --only codex-N`
- Every coder prompt must include: `WAIT for task via maw hey. Do NOT auto-explore.`
- omx resume flags before verb: `omx --yolo --direct resume --last`
- Scope tests: `bun test tests/path/` (bare bun test picks up ghost files)
- Branch diverge: repackage (clean branch + cherry-pick), NEVER rebase + force-push

## Decision tree

- EXECUTION (write code, refactor, build) → codex exec or omx team (FREE)
- ANALYSIS (code review, architecture, research) → Claude subagent (costs tokens)
- NEVER use Claude Agent tool and call it "codex" — different binary, different cost

## Quick reference

```bash
maw team preflight ψ/teams/my-team.yaml   # validate (PATH)
maw team up my-team                        # spawn (NAME)
maw team up my-team --only codex-N         # relaunch one
maw hey <session>:<member> "TASK: ..."     # dispatch
maw peek <session>:<member>                # check status
maw team down my-team                      # teardown (NAME)
maw done <session>:<member>                # clear dead state
```
