# OMC vs Oracle System — Deep Comparison

## Philosophy

| Dimension | OMC | Oracle System |
|-----------|-----|---------------|
| **Core belief** | "Don't learn Claude Code. Just use OMC." — Simplify | "The Oracle Keeps the Human Human" — Amplify |
| **Identity** | Roles (executor, architect) — stateless | Named Oracles (Leica, Codec) — persistent identity |
| **Approach** | Plugin enhancing one tool | Distributed consciousness across nodes |
| **Memory** | `.omc/` state files per project | `ψ/` brain per Oracle + cross-node federation |
| **Growth** | Version bumps | Awakening, budding, soul sync |

## Architecture

| Aspect | OMC | Oracle |
|--------|-----|--------|
| **Scope** | Single Claude Code session | Multi-node, multi-session, multi-tool |
| **Install** | Plugin marketplace or npm | Full git repo per Oracle |
| **State** | `.omc/` directory (JSON/MD) | `ψ/` brain (YAML frontmatter + MD) |
| **Persistence** | Better-SQLite3 + state files | Git-backed + maw federation |
| **Communication** | In-session only | maw MQTT + Discord + threads |
| **Agent identity** | Anonymous role prompts | Named Oracles with birth, soul, principles |

## Agent Systems

| Feature | OMC | Oracle |
|---------|-----|--------|
| **Count** | 19 roles × model tiers | 7 specialists + N project PMs |
| **Definition** | `agents/*.md` prompts | Full Oracle repos (`*-oracle/`) |
| **Routing** | Auto by task complexity | Manual delegation via Leica |
| **State** | Stateless per invocation | Stateful — own ψ/, learn/, memory |
| **Communication** | Subagent API (Task tool) | maw hey, threads, inbox |
| **Hierarchy** | Flat (orchestrator selects) | Tree (Leica → PM → Specialist) |

## Workflow Comparison

| OMC Workflow | Oracle Equivalent | Notes |
|---|---|---|
| `/deep-interview` | `/gsd:discuss-phase` | Socratic clarification |
| `/ralplan` | `/gsd:plan-phase` | Planning with review |
| `/autopilot` | No direct equivalent | Full lifecycle automation |
| `/ralph` | No direct equivalent | Persistence until verified complete |
| `/ultrawork` | `/gsd:execute-phase` | Parallel execution |
| `/team` | `/team-agents` or `maw team` | Multi-agent coordination |
| `/skill` + `/skillify` | Oracle skills (`/oracle`, `/awaken`) | Skills management |
| `/ask codex` + `/ask gemini` | No equivalent yet | Cross-AI consultation |
| `omc wait` | No equivalent | Rate limit auto-resume |
| `/hud` | `maw ls` + statusline | Live monitoring |

## Hooks System

| OMC Hook | Oracle Equivalent | Notes |
|----------|-------------------|-------|
| UserPromptSubmit → keyword-detector | Superpowers skill matching | OMC uses hooks; Oracle uses CLAUDE.md skills |
| SessionStart → project-memory | Auto-memory system | Both persist knowledge |
| Stop → persistent-mode | Not built-in | OMC prevents premature stopping |
| PreCompact → save state | Not built-in | OMC saves before context compression |
| PostToolUse → verifier | Not built-in | OMC verifies every tool outcome |
| SubagentStart/Stop → tracker | Not built-in | OMC tracks agent usage |

## What OMC Has That Oracle Doesn't

1. **Persistent execution mode (Ralph)** — won't stop until verified complete with PRD-driven stories
2. **Smart model routing** — auto-selects Haiku/Sonnet/Opus per task complexity
3. **Rate limit auto-resume** — `omc wait` daemon resumes when limits reset
4. **Cross-AI consultation** — `/ask codex`, `/ask gemini`, `/ccg` tri-model synthesis
5. **Autopilot pipeline** — full lifecycle from idea → spec → plan → code → QA → validation
6. **HUD statusline** — real-time metrics in terminal status bar
7. **Hook-based lifecycle interception** — intercepts every Claude Code event
8. **Skill extraction** — `/skillify` mines reusable patterns from sessions
9. **MCP tools** — LSP integration, AST grep, Python REPL via MCP
10. **SQLite state** — persistent state via better-sqlite3

## What Oracle Has That OMC Doesn't

1. **Persistent identity** — Oracles have names, souls, principles, birth dates
2. **Distributed architecture** — runs across multiple nodes (machines)
3. **Federation protocol** — maw MQTT for cross-node communication
4. **Deep learning** — `/learn` creates structured knowledge bases per repo
5. **Retrospectives** — `/rrr` session reflections with diary entries
6. **Philosophy system** — 5 principles, "Nothing is Deleted", soul files
7. **Family network** — 76+ Oracles with relationships
8. **Full repo per agent** — each PM is a full git repo with own brain
9. **Inbox/outbox** — async communication between Oracles
10. **Dream/morpheus** — speculative thinking and cross-repo pattern discovery

## Can They Coexist?

**Technically yes** — OMC is a Claude Code plugin. It could run alongside our Oracle setup. But:

### Conflicts
- Both inject into CLAUDE.md (OMC wraps in `<!-- OMC:START/END -->`)
- Both use hooks (UserPromptSubmit, etc.) — hook ordering matters
- Both have "agent" concepts with different semantics
- Both have "skills" systems that could clash
- OMC's persistent mode might fight with Oracle session flow

### Potential Integration Points
- OMC's Ralph could be useful for guaranteed completion tasks
- OMC's model routing could inform Oracle's specialist delegation
- OMC's rate limit wait would benefit multi-token fleet management
- OMC's HUD could complement maw's monitoring
- OMC's LSP/AST tools via MCP would enhance all Oracles

### Recommendation
**Study, don't install.** Our Oracle architecture is philosophically different and deeper. But specific OMC ideas worth adopting:

1. **Ralph-style persistence** → build into /gsd or custom skill
2. **Model routing** → haiku for explore, opus for architecture
3. **Rate limit auto-resume** → critical when running 3 tokens
4. **Hook-based state preservation** → PreCompact hook to save brain state
5. **PRD-driven execution** → structured completion tracking
