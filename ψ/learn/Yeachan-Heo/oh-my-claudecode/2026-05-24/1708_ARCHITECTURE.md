# oh-my-claudecode (OMC) — Deep Architecture Analysis

## Identity

- **Name**: oh-my-claudecode (OMC)
- **npm package**: `oh-my-claude-sisyphus` (brand mismatch — npm name differs from repo name)
- **Version**: 4.14.1
- **Creator**: Yeachan Heo (Korean, same as oh-my-codex)
- **Stars**: 34k GitHub
- **License**: MIT
- **Birth**: 2026-05-06 (only ~18 days old as of 2026-05-24!)
- **Commits**: 50 (extremely rapid development)
- **Codebase**: 281,522 lines TypeScript
- **Related**: oh-my-codex (same author, for OpenAI Codex CLI)

## What It Is

A **Claude Code plugin** that adds multi-agent orchestration, persistent execution loops, smart model routing, and structured workflows on top of vanilla Claude Code.

Tagline: *"Don't learn Claude Code. Just use OMC."*

It installs as a Claude Code plugin via:
```bash
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode
/plugin install oh-my-claudecode
```

Or as CLI:
```bash
npm i -g oh-my-claude-sisyphus@latest
omc setup
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Claude Code Session                  │
├──────────────────────────���──────────────────────────┤
│  OMC Plugin Layer                                    │
│  ┌─────────────────────────────��─────────────────┐  │
│  │ Hooks (lifecycle interception)                 │  │
│  │  • UserPromptSubmit → keyword-detector         │  │
│  │  • SessionStart → session-start, project-memory│  │
│  │  • PreToolUse → pre-tool-enforcer              │  │
│  │  • PostToolUse → post-tool-verifier            │  │
│  │  • Stop → persistent-mode, code-simplifier     │  │
│  │  • PreCompact → pre-compact, wiki-pre-compact  │  │
│  │  • SubagentStart/Stop → subagent-tracker       │  │
│  │  • SessionEnd → session-end, wiki-session-end  │  │
│  └────────────────────────────────��──────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │ Skills (slash commands — 37 skills)            │  │
│  │  /autopilot, /ralph, /ultrawork, /team, /ccg   │  │
│  │  /deep-interview, /ralplan, /ultraqa, /verify  │  │
│  │  /skill, /skillify, /ask, /hud, /wiki, ...    │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │ MCP Server ("t" — tools + state)              │  │
│  │  state_read, state_write, state_clear          │  │
│  │  notepad_read/write, project_memory_*          │  │
│  │  lsp_*, ast_grep_*, python_repl               │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │ Agents (19 roles × tier variants)             │  │
│  │  explore(haiku), analyst(opus), planner(opus)  │  │
│  │  architect(opus), debugger(sonnet),            │  │
│  │  executor(sonnet/haiku/opus), verifier(sonnet) │  │
│  │  security-reviewer, code-reviewer(opus)        │  │
│  │  test-engineer, designer, writer(haiku)        │  │
│  │  qa-tester, scientist, document-specialist     │  │
│  │  git-master, code-simplifier(opus), critic(opus)│ │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │ CLI (omc command — terminal-side)             │  │
│  │  omc setup, omc team, omc ask, omc wait       │  │
│  │  omc hud, omc explore, omc doctor             │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  External Workers (tmux CLI panes)                   │
│  • omc team N:codex "..."  → Codex CLI panes       │
│  • omc team N:gemini "..." → Gemini CLI panes      │
│  • omc team N:claude "..." → Claude CLI panes      │
└─────────────────────────────────────────────────────┘
```

## Source Structure

```
src/ (281k lines)
├── hooks/              # 30+ hook modules (lifecycle interception)
│   ├── keyword-detector/    # Magic keyword → skill routing
│   ├── ralph/               # Persistent mode enforcement
│   ├── autopilot/           # Auto-pilot hook logic
│   ├── ultrawork/           # Parallel execution hook
│   ├── ultraqa/             # QA cycling hook
│   ├── team-pipeline/       # Team orchestration
│   ├── code-simplifier/     # Auto code simplification
│   ├── learner/             # Skill extraction
│   ├── project-memory/      # Persistent memory
│   ├── notepad/             # Notepad state
│   ├── wiki/                # Wiki auto-inject
│   ├── persistent-mode/     # Don't-stop enforcement
│   ├── pre-compact/         # Save state before compaction
│   ├── subagent-tracker/    # Agent usage monitoring
│   ├── think-mode/          # Deep reasoning trigger
│   ├── factcheck/           # Fact verification
│   └── ...
├── features/           # Core capabilities
│   ├── model-routing/       # Haiku/Sonnet/Opus selection
│   ├── delegation-routing/  # Agent selection logic
│   ├── state-manager/       # .omc/ state persistence
│   ├── verification/        # Completion verification
│   ├── task-decomposer/     # Break down large tasks
│   ├── rate-limit-wait/     # Auto-resume on rate limit
│   ├── notepad-wisdom/      # Knowledge persistence
│   └── ...
├── team/               # Multi-agent team runtime
├── skills/             # Skill registration/injection
├── agents/             # Agent prompt generation
├── cli/                # Terminal CLI commands
├── mcp/                # MCP server implementation
├── hud/                # Heads-up display
├── tools/              # LSP, AST, Python REPL
├── notifications/      # Telegram/Discord/Slack
├── openclaw/           # OpenClaw gateway
├── ultragoal/          # Durable goal system
├── goal-workflows/     # Goal orchestration
├── ralphthon/          # Ralph persistence engine
├── autoresearch/       # Bounded research
├── planning/           # Plan generation
└── verification/       # Completion verification
```

## Key Mechanisms

### 1. Hook-Based Lifecycle Interception

Every Claude Code event is intercepted:

| Hook | What OMC Does |
|------|---------------|
| UserPromptSubmit | Detect keywords ("ralph", "ulw", "autopilot") → inject skill |
| SessionStart | Load project memory, wiki state, session context |
| PreToolUse | Enforce rules (e.g., prevent unauthorized writes) |
| PostToolUse | Verify tool outcomes, inject rules |
| Stop | Check if persistent mode active → re-inject prompt |
| PreCompact | Save state before context compression |
| SubagentStart/Stop | Track agent usage for analytics |
| SessionEnd | Save session summary, notify, cleanup |
| PermissionRequest | Auto-handle permissions |
| PostToolUseFailure | Recovery logic |

### 2. Ralph — Persistent Completion Engine

Ralph = "don't stop until VERIFIED done"

- Generates a PRD (Product Requirements Doc) as `prd.json`
- Breaks work into user stories with acceptance criteria
- Iterates story-by-story until all pass
- Each story verified by a reviewer agent (architect/critic/codex)
- Uses `progress.txt` for cross-iteration tracking
- Wraps ultrawork for parallel execution within stories
- Max iteration limit prevents infinite loops
- Post-completion deslop pass (code cleanup)

### 3. Autopilot — Full Lifecycle Pipeline

5 phases fully automated:
1. **Phase 0 — Expansion**: Idea → detailed spec (analyst + architect, both Opus)
2. **Phase 1 — Planning**: Spec → implementation plan (architect + critic)
3. **Phase 2 — Execution**: Plan → code (Ralph + Ultrawork delegation)
4. **Phase 3 — QA**: Build/lint/test cycling (up to 5 rounds)
5. **Phase 4 — Validation**: Multi-reviewer approval (architect + security + code-reviewer)

### 4. Team — Multi-Agent Pipeline

Staged pipeline:
```
team-plan → team-prd → team-exec → team-verify → team-fix (loop)
```

Uses Claude Code's native `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` feature.
Also supports tmux CLI workers (codex/gemini/claude panes).

### 5. Smart Model Routing

| Task Complexity | Model | Role |
|----------------|-------|------|
| Quick lookups | Haiku | explore, writer |
| Standard work | Sonnet | executor, debugger, verifier, test-engineer |
| Deep analysis | Opus | analyst, architect, planner, code-reviewer, critic |

### 6. Custom Skills System

- Project-scoped: `.omc/skills/` (committed)
- User-scoped: `~/.omc/skills/` (personal)
- Auto-injection based on trigger keywords
- `/skillify` extracts reusable patterns from sessions
- YAML frontmatter with triggers, description, source

### 7. MCP Server Tools

Single MCP server (`t`) provides:
- **State management**: read/write/clear/list OMC state
- **Notepad**: persistent session notes
- **Project memory**: cross-session knowledge
- **LSP integration**: hover, goto-def, references, diagnostics
- **AST grep**: structural code search/replace
- **Python REPL**: inline computation

### 8. Notifications & Integrations

- Discord webhook + tag list
- Telegram bot
- Slack webhook
- OpenClaw gateway (automated response workflows)
- File-based callbacks
- HUD statusline (tmux/terminal)

## Dependencies

Production:
- `@anthropic-ai/claude-agent-sdk` (official Anthropic agent SDK)
- `@modelcontextprotocol/sdk` (MCP)
- `@ast-grep/napi` (structural code search)
- `better-sqlite3` (local state DB)
- `chalk`, `commander`, `zod`, `ajv`
- `vscode-languageserver-protocol` (LSP)

## Commit Protocol

OMC enforces structured git trailers:
```
fix(auth): prevent silent session drops

Constraint: Auth service does not support token introspection
Rejected: Extend token TTL to 24h | security policy violation
Confidence: high
Scope-risk: narrow
Not-tested: Auth service cold-start latency >500ms
```

## Statistics

- 281,522 lines TypeScript
- 19 agent roles with tier variants
- 37 skills
- 11 hook lifecycle events covered
- 30+ hook modules
- 50 commits in 18 days
- v4.14.1 (rapid versioning)
- 34k GitHub stars
