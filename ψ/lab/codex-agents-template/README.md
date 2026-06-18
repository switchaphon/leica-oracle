# Codex Agents Template

> ให้ PM Oracle ใช้ scaffold AGENTS.md + role agents สำหรับ project ของตัวเอง

## What This Is

Template สำหรับ deploy ลง project repo เพื่อให้ Codex อ่าน context ได้อัตโนมัติเมื่อถูก spawn ผ่าน `maw team up` หรือ `codex exec`

## Structure

```
project-root/
├── AGENTS.md              ← Codex reads this first (project overview + hard rules)
├── agents/
│   ├── chrome.md          ← frontend role (React, components, state)
│   ├── flux.md            ← backend role (API, auth, data)
│   └── static.md          ← testing role (unit, E2E, review)
└── .maw/teams/
    └── codex-squad.yaml   ← charter for maw team up
```

## How to Deploy

### For PM Oracle (run from project directory):

```bash
# 1. Copy template
cp -r ~/ghq/.../leica-oracle/ψ/lab/codex-agents-template/agents ./agents
cp ~/ghq/.../leica-oracle/ψ/lab/codex-agents-template/AGENTS.template.md ./AGENTS.md
cp -r ~/ghq/.../leica-oracle/ψ/lab/codex-agents-template/maw-teams ./.maw/teams

# 2. Fill project-specific sections in AGENTS.md
#    - Stack versions
#    - Hard rules specific to your project
#    - Architecture gotchas
#    - File structure

# 3. Customize role agents
#    - agents/chrome.md: your component patterns, styling conventions
#    - agents/flux.md: your API patterns, auth model
#    - agents/static.md: your test patterns, coverage thresholds

# 4. Add to .gitignore if project repo shouldn't track these
echo "agents/" >> .gitignore
echo "AGENTS.md" >> .gitignore
```

### Or let PM Oracle generate them:

PM Oracle knows the project deeply (from ψ/learn/). It can generate filled versions by reading its own deep-learn artifacts.

## Usage (from PM Oracle session)

```bash
# Spawn team
maw-team codex-squad

# Assign task to specific role
tmux send-keys -t %CHROME_PANE "codex exec -s workspace-write 'You are Chrome. Read agents/chrome.md. Task: build the appointment picker component per this spec: ...'" Enter

# Or single agent
codex exec -s workspace-write "Read AGENTS.md. Task: ..."
```

## Pilot

- **pops-clinic** (pops/vet): deployed 2026-06-15
- Other projects: pending — PM Oracle will customize from this template

## When to Promote to Codex Oracle

See leica-oracle CLAUDE.md or ask Leica. Short answer: when Codex needs memory across sessions (repeated mistakes, standing orders, coordination between Codex instances).
