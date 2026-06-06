# Caveman Architecture

**Project**: caveman  
**Creator**: Julius Brussee (@JuliusBrussee)  
**Purpose**: Token efficiency plugin for 30+ AI coding agents — compress output by ~75% while preserving technical accuracy  
**Primary Distribution**: Plugin/skill system (Claude Code, Codex, Gemini, Cursor, Windsurf, etc.)  
**License**: MIT  

---

## Problem Statement

AI coding agents (Claude Code, Cursor, Copilot, Gemini, etc.) generate verbose responses:
- Cost per token adds up across long sessions
- Verbose output slows reading/comprehension
- Fluff words don't add technical substance

**Caveman solves this** by forcing responses into compressed caveman-style prose that drops ~75% of output tokens while keeping 100% technical accuracy:

```
BEFORE:  "The reason your React component is re-rendering is likely because..."  (69 tokens)
AFTER:   "New object ref each render. Wrap in useMemo."                          (19 tokens)
```

Same fix. 73% fewer tokens.

---

## Core Design Principles

1. **One ruleset, many distributions** — Single SKILL.md file drives all 30+ agents (Claude Code, Cursor, Windsurf, Cline, Copilot, Gemini CLI, opencode, OpenClaw, 20+ others). Install mechanism differs; rules are identical.

2. **Persistence without friction** — Once activated, stays on until explicitly deactivated. No mode drift, no reversion after N turns. User says "stop caveman" or "normal mode" to exit.

3. **Intensity levels** — Six modes span lite → full (default) → ultra, plus classical Chinese (wenyan) variants. `/caveman lite` switches levels mid-session.

4. **Auto-clarity failsafes** — When compression risks ambiguity (security warnings, multi-step destructive ops, user confusion), drop back to normal prose, then resume. Rule prevents harm.

5. **Pure token compression** — Only output tokens affected. Thinking/reasoning tokens untouched. Compression is a *style filter*, not a reasoning limitation.

6. **Hook-based auto-activation** — Claude Code hooks inject ruleset at SessionStart without user action. No `/caveman` per session needed.

---

## Directory Structure

```
caveman/
├── README.md / INSTALL.md / CLAUDE.md           # User & maintainer docs
│
├── bin/install.js                               # Single unified installer (all 30+ agents)
├── bin/lib/
│   ├── settings.js                              # JSONC-safe settings.json reader/writer
│   └── openclaw.js                              # OpenClaw workspace install helper
│
├── src/
│   ├── hooks/                                   # Claude Code hook system
│   │   ├── caveman-config.js                    # Config resolver (env → file → default)
│   │   ├── caveman-activate.js                  # SessionStart hook (inject rules + write flag)
│   │   ├── caveman-mode-tracker.js              # UserPromptSubmit hook (slash commands + reinforcement)
│   │   ├── caveman-stats.js                     # Token counting for /caveman-stats
│   │   ├── caveman-statusline.sh / .ps1         # Statusline badge renderer (reads flag file)
│   │   └── package.json                         # Pins dir to CommonJS (require() safety)
│   │
│   ├── rules/                                   # Always-on ruleset bodies (single source)
│   │   ├── caveman-activate.md                  # Ruleset injected by SessionStart hook + per-repo init
│   │   └── caveman-openclaw-bootstrap.md        # SOUL.md marker-fenced snippet for OpenClaw
│   │
│   ├── tools/
│   │   └── caveman-init.js                      # Writes per-repo IDE rule files (.cursor, .windsurf, etc)
│   │
│   ├── plugins/opencode/                        # opencode native plugin
│   │   ├── plugin.js                            # ESM module, session.created + tui.prompt.append hooks
│   │   ├── commands/*.md                        # Slash command templates (/caveman, /caveman-commit, etc)
│   │   └── package.json
│   │
│   └── mcp-servers/caveman-shrink/              # npm-published MCP middleware
│       ├── index.js                             # MCP server (wraps any MCP server, compresses tool descriptions)
│       └── compress.js
│
├── skills/                                      # LLM-facing behavior (SINGLE SOURCE OF TRUTH)
│   ├── caveman/
│   │   ├── SKILL.md                             # Main ruleset (lite/full/ultra/wenyan modes)
│   │   └── README.md                            # User-facing explanation
│   ├── caveman-commit/
│   │   ├── SKILL.md                             # Conventional Commits + ≤50 char subjects
│   │   └── README.md
│   ├── caveman-review/
│   │   ├── SKILL.md                             # PR review: one-line format
│   │   └── README.md
│   ├── caveman-help/
│   │   └── SKILL.md                             # Quick-reference card
│   ├── caveman-stats/
│   │   └── SKILL.md                             # /caveman-stats behavior
│   ├── caveman-compress/
│   │   ├── SKILL.md                             # Memory file compressor
│   │   ├── README.md
│   │   └── scripts/                             # Python implementation (3.10+)
│   └── cavecrew/
│       ├── SKILL.md                             # When to delegate to caveman subagents
│       └── README.md
│
├── agents/                                      # Cavecrew subagents (read-only locators)
│   ├── cavecrew-investigator.md                 # Find symbols across codebase
│   ├── cavecrew-builder.md                      # Surgical 1-2 file editor
│   └── cavecrew-reviewer.md                     # Diff/file reviewer
│
├── commands/                                    # Codex/Gemini TOML stubs
│   ├── caveman.toml
│   ├── caveman-commit.toml
│   └── ...
│
├── plugins/caveman/                             # Claude Code plugin distribution (CI-synced)
│   ├── skills/                                  # Mirror of skills/
│   └── agents/                                  # Mirror of agents/
│
├── .claude-plugin/                              # Claude Code plugin manifest (required at root)
│
├── dist/                                        # Build artifacts (gitignored)
│   └── caveman.skill                            # ZIP of skills/caveman/ (rebuilt by CI)
│
├── tests/                                       # Node + Python test suite
├── benchmarks/                                  # Real Claude API token counts
├── evals/                                       # Three-arm eval harness
└── .github/workflows/sync-skill.yml             # CI: mirror skills → plugins/, rebuild dist/
```

---

## Key Abstractions & Data Flow

### 1. **Ruleset System** (The Behavior)

**Source of Truth**: `skills/caveman/SKILL.md`  
**Distribution Path**:
```
skills/caveman/SKILL.md
    ├─→ plugins/caveman/skills/caveman/SKILL.md    (CI mirror for Claude Code plugin)
    ├─→ src/rules/caveman-activate.md              (extracted for hook injection + per-repo init)
    └─→ All other agents via npx skills CLI
```

**Structure** (YAML frontmatter + markdown body):
```yaml
---
name: caveman
description: "Ultra-compressed communication..."
---

Respond terse like smart caveman...

## Intensity

| Level | What change |
|-------|------------|
| lite | No filler. Keep articles. Professional tight |
| full | Drop articles, fragments OK (default) |
| ultra | Abbreviate prose words, arrows for causality |
| wenyan-full | Maximum classical Chinese terseness |
...
```

**Intensity levels**:
- `lite` — professional but tight (fewest cuts)
- `full` — classic caveman (default, 65-75% token reduction)
- `ultra` — telegraphic (80-90% reduction, max abbreviation)
- `wenyan-lite`, `wenyan-full`, `wenyan-ultra` — classical Chinese variants

**Auto-clarity rule** (safety valve):
- Drop caveman for security warnings, irreversible actions, multi-step sequences where fragment order risks misread
- Resume after clear part done

---

### 2. **Installation System** (How It Reaches 30+ Agents)

**Single Point of Entry**: `bin/install.js`
```bash
# All these delegate to bin/install.js:
curl -fsSL install.sh | bash
pwsh install.ps1
node bin/install.js [flags]
npx -y github:JuliusBrussee/caveman -- [flags]
```

**Provider Matrix** (PROVIDERS array in install.js):
- **Claude Code** → plugin install + optional hooks
- **Gemini CLI** → `gemini extensions install`
- **opencode** → native plugin copy + AGENTS.md snippet
- **OpenClaw** → workspace skill + SOUL.md marker block
- **Codex, Cursor, Windsurf, Cline, Copilot, ...** → `npx skills add ...` (20+ agents)

**Per-provider mechanisms**:

| Agent | How caveman arrives | Auto-activates? |
|-------|-------------------|-----------------|
| Claude Code | Plugin hooks (SessionStart injects rules + flag) | Yes |
| Gemini CLI | GEMINI.md context file | Yes |
| opencode | Native plugin (`plugin.js` lifecycle hooks) | Yes |
| OpenClaw | Workspace SOUL.md bootstrap block | Yes |
| Cursor/Windsurf/Cline | npx skills CLI or per-repo rule files | Yes (rule files) |
| Others (20+) | npx skills CLI | No (must say /caveman) |

---

### 3. **Hook System** (Claude Code Auto-Activation)

**Why hooks exist**: Make caveman always-on without user typing `/caveman` every session. Single shared mode flag drives behavior.

**Hooks Location**: `src/hooks/` (copied to `$CLAUDE_CONFIG_DIR/hooks/` by installer)  
**Mode Flag**: `$CLAUDE_CONFIG_DIR/.caveman-active` (symlink-safe atomic write)

**Three hooks**:

#### **caveman-activate.js** (SessionStart hook)
- Runs once per Claude Code session start
- Writes default mode to flag file (via `safeWriteFlag` — symlink-safe)
- Emits full ruleset as hidden stdout → Claude Code injects as system context
- Checks settings.json for statusline config; nudges setup on first interaction

#### **caveman-mode-tracker.js** (UserPromptSubmit hook)
- Reads JSON from stdin (user message)
- **Slash command parsing**: `/caveman lite|full|ultra|wenyan...` writes new mode to flag
- **Natural language**: "talk like caveman" / "stop caveman" updates flag
- **Per-turn reinforcement**: If flag set, emits small reminder so model keeps caveman style after other plugins inject competing instructions

#### **caveman-statusline.sh / .ps1** (Statusline badge)
- Reads flag file + savings suffix
- Outputs colored badge for Claude Code statusline: `[CAVEMAN]` or `[CAVEMAN:ULTRA]`
- Suffix shows lifetime token savings (updated by `/caveman-stats`)
- Both shell versions (sh + PowerShell) for cross-platform roaming config

**Shared Module** (caveman-config.js):
```javascript
getDefaultMode()        // Resolve env → config file → 'full'
safeWriteFlag()         // Atomic write with symlink protection
validateHookFields()    // Zod-safe settings.json merge
```

---

### 4. **Skill Distribution Mechanisms**

#### **Claude Code Plugin** (Tier 1: auto-activate)
- Hooks wired by plugin system automatically
- `plugins/caveman/` (CI-mirrored from `skills/`)
- Plugin manifest at `.claude-plugin/` (required at root)

#### **npx skills CLI** (Tier 1-2: auto-activate + per-repo rules)
```bash
npx caveman --only cursor              # Installs upstream Cursor skill profile
npx caveman --with-init --only cursor  # Also writes .cursor/rules/caveman.mdc (per-repo rule)
```

#### **Codex Plugin** (Tier 1: auto-activate)
- Hooks in `.codex/hooks.json`, auto-discovery config in `.codex/config.toml`

#### **Gemini Extension** (Tier 1: auto-activate)
- GEMINI.md context file at repo root (auto-discovered by Gemini CLI)

#### **opencode Native Plugin** (Tier 1: auto-activate)
- `src/plugins/opencode/plugin.js` copied to `~/.config/opencode/plugins/caveman/`
- AGENTS.md ruleset marker-fenced block (same pattern as OpenClaw SOUL.md)
- Skills + agents + commands mirrored to `~/.config/opencode/`

#### **OpenClaw Workspace** (Tier 1: auto-activate)
- Skill at `~/.openclaw/workspace/skills/caveman/SKILL.md` (frontmatter merged: `version` + `always: true`)
- Bootstrap block in `SOUL.md` (marker-fenced, auto-injected every turn)
- Helper: `bin/lib/openclaw.js` (idempotent append/strip)

---

### 5. **Compression Engine** (The Rules in Practice)

**Rule System** (from SKILL.md):

```
DROP:      articles (a/an/the)
           filler (just/really/basically/actually)
           pleasantries (sure/certainly/happy to)
           hedging (might/could/probably)

KEEP:      technical terms (exact)
           code blocks (unchanged)
           error messages (exact quote)
           function/API names

PATTERN:   [thing] [action] [reason]. [next step].

EXAMPLES:
Normal:    "The reason your React component is re-rendering is..."
Caveman:   "New object ref each render. Wrap in useMemo."

Normal:    "I'd be happy to help. The issue is likely..."
Caveman:   "Bug in auth middleware. Token expiry use < not <=. Fix:"
```

**Per-Level Behavior**:

| Lite | Full | Ultra |
|------|------|-------|
| Drop filler + hedging | Same + drop articles | Same + abbreviate (DB/auth/req) |
| Keep grammar | Fragments OK | Arrows (→) for causality |
| Professional tight | Classic caveman | Telegraphic |

---

## Entry Points & Usage Flows

### **For Users**

1. **Installation** (one-time):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
   ```
   - Auto-detects Claude Code, Cursor, Windsurf, Copilot, etc.
   - Installs appropriate mechanism for each (hooks, plugin, skills, rule files)

2. **Activation** (per-session, Claude Code):
   - SessionStart hook auto-injects rules → caveman active from message 1
   - User can switch levels: `/caveman lite` / `/caveman ultra`
   - User can deactivate: "stop caveman" or "normal mode"

3. **Other modes** (independent skills):
   - `/caveman-commit` — force next commit to Conventional Commits format
   - `/caveman-review` — one-line PR comments (L42: bug. Fix.)
   - `/caveman-compress <file>` — rewrite memory file into caveman-speak
   - `/caveman-stats` — show session token usage + lifetime savings

---

### **For Developers/Maintainers**

1. **Edit behavior**: Only edit `skills/caveman/SKILL.md`
   - CI auto-syncs to `plugins/caveman/`, `src/rules/caveman-activate.md`, all agent skill profiles
   - No manual mirroring needed

2. **Add new agent**: Edit `PROVIDERS` array in `bin/install.js` (single source)
   - Add detection rule (command, dir, extension, etc.)
   - Add optional `profile` slug (for `npx skills add`)
   - Run `node bin/install.js --list` to verify

3. **Release**: Push to main → CI workflow triggers
   - Mirrors skills → plugins/
   - Rebuilds dist/caveman.skill
   - Commits back to main with `[skip ci]`

---

## Core Dependencies

### **Zero Runtime Dependencies** (install.js)
- Node.js stdlib only (`fs`, `path`, `child_process`, `readline`)
- No npm packages — pure Node

### **Hook Runtime** (Claude Code)
- `caveman-config.js` — config resolution + symlink-safe flag write
- Communicates via filesystem flag file (no IPC, no complexity)

### **Sub-skills** (caveman-compress)
- Requires Python 3.10+
- Uses `anthropic` Python SDK (user supplies API key)

### **MCP Middleware** (caveman-shrink)
- npm package: `caveman-shrink`
- Wraps any MCP server, compresses tool descriptions on-the-fly

---

## Design Patterns & Decisions

### **Pattern 1: Single Source of Truth (SKILL.md)**
- One file drives all 30+ agents (Claude Code, Cursor, Copilot, Gemini, etc.)
- CI mirrors to plugin dirs + rule files
- Never edit synced copies (`plugins/caveman/skills/`, per-agent rule copies) — edit `skills/caveman/SKILL.md` only

### **Pattern 2: Idempotent Install**
- `bin/install.js` can re-run safely (checks for existing install, skips if found unless `--force`)
- Hook merge defensive (JSONC-tolerant settings.json reader, Zod validation before write)
- No duplicate marker blocks in SOUL.md / AGENTS.md (marker-fenced, idempotent append/strip)

### **Pattern 3: Symlink-Safe Flag File**
- `safeWriteFlag()` in `caveman-config.js` protects against local privilege escalation
- Opens with `O_NOFOLLOW` where supported, atomic temp + rename, `0600` permissions
- Parent dir symlink allowed (legitimate roaming config) but verified for ownership
- Flag file itself must never be symlink — that's the vector

### **Pattern 4: Auto-Clarity Failsafe**
- When compression risks ambiguity (multi-step sequences, security warnings), drop to normal prose
- Resume after clear part done
- Prevents confusion/harm from fragment-order misreads

### **Pattern 5: Persistence Without Drift**
- Mode flag stays active until explicit deactivation
- No reversion after N turns
- Hook reinforcement per-turn prevents other plugins from overwriting caveman style

### **Pattern 6: Platform Abstraction** (install.js)
- All OS-specific logic centralized in `bin/install.js` + helper functions (`quoteWinArg`, `spawnXplat`)
- No bash vs PowerShell dual-source (eliminated old `install.sh.legacy` / `install.ps1.legacy`)
- Works macOS, Linux, WSL, Windows (PowerShell 5.1+)

---

## Testing & Quality

### **Benchmarks** (`benchmarks/`)
- Real Claude API calls (not approximations)
- Measures actual token reduction across 10 prompts
- Average: **65% output reduction**, range 22-87%
- Results committed as JSON; README table generated from actual data

### **Evals** (`evals/`)
- Three-arm harness: baseline (no prompt) vs terse ("Be concise") vs caveman (skill)
- Honest delta = skill vs terse (not skill vs baseline)
- Prevents conflating skill with generic terseness
- Auto-discovers new skills in `skills/` directory

### **Tests** (`tests/`)
- Node test suite (installer, hook logic, settings merge)
- Python test suite (caveman-compress behavior)
- Validation: headings/code blocks/URLs/paths preserved after compression

---

## Limitations & Scope

1. **Output tokens only** — thinking/reasoning tokens untouched. Compression is a style filter, not reasoning reduction.

2. **Confidence boundaries** (Auto-clarity):
   - Security warnings: always normal prose
   - Irreversible actions: always normal prose
   - Multi-step sequences: normal prose if fragment order risks misread
   - User confusion: drop caveman, resume after

3. **Code/commits/PRs** — always written in normal prose (caveman is output-only for agent communication)

4. **Model behavior** — caveman is a prompt instruction, not a model limitation. Model still reasons fully; only the *output style* changes.

---

## Configuration & Extensibility

### **User Config** (`~/.config/caveman/config.json`)
```json
{
  "defaultMode": "lite"
}
```

### **Environment Variables**
- `CAVEMAN_DEFAULT_MODE` — override default mode
- `CAVEMAN_STATUSLINE_SAVINGS=0` — disable token savings badge
- `CLAUDE_CONFIG_DIR` — override config directory (for roaming configs)
- `XDG_CONFIG_HOME` — XDG standard (macOS/Linux)

### **Per-Repo Rule Init** (`caveman-init.js`)
- Writes agent-specific rule files from `src/rules/caveman-activate.md`:
  - `.cursor/rules/caveman.mdc` (Cursor)
  - `.windsurf/rules/caveman.md` (Windsurf)
  - `.clinerules/caveman.md` (Cline)
  - `.github/copilot-instructions.md` (Copilot)

---

## Integration Points

### **With Claude Code**
- Plugin system (settings.json hooks)
- Skill system (SKILL.md frontmatter + body)
- Session lifecycle hooks (SessionStart, UserPromptSubmit)

### **With Other Agents**
- **CLI agents** (Codex, Warp, Kiro, etc.): npx skills CLI profiles
- **IDE agents** (Cursor, Windsurf, Cline): per-repo rule files + upstream skill profiles
- **OpenClaw**: workspace skill + SOUL.md bootstrap
- **opencode**: native plugin + AGENTS.md ruleset

### **With MCP Servers**
- `caveman-shrink`: middleware wraps any MCP server, compresses tool descriptions

---

## Future Extensions (from ecosystem perspective)

The caveman philosophy scales to five tools (mentioned in README):

| Tool | What | Status |
|------|------|--------|
| **caveman** (this) | Output compression — why use many token when few do trick | ✅ Mature |
| **caveman-code** | Full terminal agent — whole agent can save | ✅ Separate repo |
| **cavemem** | Cross-agent memory — why agent forget when can remember | ✅ Separate repo |
| **cavekit** | Spec-driven build loop — why agent guess when can know | ✅ Separate repo |
| **cavegemma** | Gemma fine-tune on caveman pairs — why prompt every turn when weights remember | ✅ Separate repo |

Caveman is the *style layer*; the ecosystem handles memory compression, build spec driven development, and weight-level optimization.

---

## Maintainer Notes

**Critical invariants**:
1. Never delete history (git push --force forbidden) — past context matters later
2. Hook files must silent-fail on all filesystem errors — never block session start
3. Flag file writes go through `safeWriteFlag()` only — protects against symlink attacks
4. Settings.json reads go through `readSettings()` + `validateHookFields()` — JSONC-safe, Zod-validated
5. CI workflow commits back to main — account for when checking branch state
6. Benchmark/eval numbers are real — never fabricate or estimate
7. README voice intentionally caveman-like — preserve brand ("Brain still big." "Cost go down forever.")

