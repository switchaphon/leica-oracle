# Oracle 101 — Ch05: Skills, Maw, and Plugin

**Source**: https://oracle101.vercel.app/ch05.html
**Learned**: 2026-05-08

---

## Three Layers

> "Oracle ให้ความจำ, Skills ให้ workflow, Maw ให้ทีม, Plugin ให้ระบบเติบโต"

| Layer | System | Purpose |
|-------|--------|---------|
| Memory | arra-oracle-v3 | Store, search, learn, trace |
| Orchestration | maw-js | Control tmux, message routing, fleet |
| Skills | ~/.claude/skills/ | Workflow instructions agents read |
| Plugins | maw runtime | System-level capabilities |

## Skills Framework

Markdown-based workflow instructions. Stored in `~/.claude/skills/` or `~/.codex/skills/`. Zero resource cost until invoked.

### Installation Profiles

| Profile | Use Case | Key Skills |
|---------|----------|------------|
| **seed** | Testing/new Oracle | `/rrr`, `/recap`, `/philosophy` |
| **standard** | General use | + `/trace`, `/learn`, `/forward` |
| **lab** | Production work | + `/dream`, `/morpheus`, `/fleet`, `/warp` |

```bash
arra-oracle-skills install -g --profile lab
/go lab   # switch profile via skill
```

### Essential Skills

| Skill | What it does |
|-------|-------------|
| `/recap` | Retrieves context from retros, handoffs, git state — prevents re-explaining |
| `/rrr` | Captures retrospectives, diary, lessons → ψ/ memory |
| `/trace` | Cross-project search through git, repos, docs, Oracle KB |
| `/learn` | Parallel agents explore codebases → architecture + snippets + reference docs |
| `/forward` | Creates handoff doc for future sessions |
| `/who-are-you` | Identity verification — model, session, profile |
| `/awaken` | Birth ritual for new Oracles |
| `/philosophy` | Display 5 Principles + Rule 6 |

### Advanced Skills

| Skill | Purpose |
|-------|---------|
| `/bampenpien` | Guided conversation on purposeful difficulty (contemplative) |
| `/harden` | Security audit — secrets, principles, memory, git config |
| `/morpheus` | Speculative prediction — future scenarios |
| `/dream` | Cross-repo pattern scanning — pains, plans, gains |
| `/feel` | Energy/burnout assessment |
| `/resonance` | Capture moments that click |
| `/fleet` | Deep fleet census across all nodes |
| `/dig` | Session history mining |
| `/warp` | SSH + tmux teleport to remote oracle |
| `/i-believed` | Rare — foundational trust proclamation |

## Maw: The Nervous System

> "maw-js เป็นระบบประสาท, maw-ui เป็นดวงตา, Oracle memory เป็นสมอง"

Maw is NOT agent replacement or memory — it's the orchestration layer.

### Primary Functions

1. Session lifecycle (wake, sleep, stop, done)
2. Message routing to agents
3. Output capture from tmux panes
4. Fleet status monitoring
5. Plugin loading
6. API and WebSocket exposure

### Why tmux?

- Agents are **visible** (not invisible background workers)
- Cross-agent output capture
- Persistent evidence of stuck workflows
- Transparency philosophy alignment

## Plugin Architecture

Extends maw without touching core.

### Plugin Ecosystem

| Repo | Purpose |
|------|---------|
| `maw-core-plugins` | Foundation (wake, sleep, stop, done) |
| `maw-plugins` | Supplementary (contacts, costs, health, ping, bud, oracle) |
| `maw-incarnation-plugin` | Template for new plugins |
| `maw-cell-plugin` | Reproduction (bud, fusion, absorb) |
| `maw-plugin-registry` | Central registry |

### Skill vs Plugin

| Dimension | Skill | Plugin |
|-----------|-------|--------|
| Storage | Agent folder | Maw runtime |
| Invocation | Agent commands | CLI, API, UI, peer, cron |
| Scope | Workflow instructions | System capabilities |
| Examples | recap, rrr, trace | wake, sleep, health, queues |

**Migration path**: When a skill matures and needs multi-surface invocation → becomes a plugin.

## Installation Order (Critical)

1. Bun, GitHub CLI, ghq, tmux
2. arra-oracle-v3 (memory FIRST)
3. Configure data paths + indexing
4. Register MCP
5. Install skills
6. Install maw-js
7. Configure fleet
8. Install plugins
9. Open UI

> "Don't reverse this. Runtime before interface. Memory before orchestration."

## Multi-Agent Workflow Pattern

```
Human → Primary agent → queries Oracle memory
                      → dispatches sub-agents via Maw
                      → sub-agents execute in tmux panes
                      → primary captures outputs
                      → system records retro/handoff
                      → future agents continue seamlessly
```
