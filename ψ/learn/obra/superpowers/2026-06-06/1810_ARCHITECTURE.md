# Superpowers Architecture

**Date**: 2026-06-06  
**Version**: 5.1.0  
**Status**: Active, multi-platform support (Claude Code, OpenCode, Copilot CLI, Cursor, Codex)

---

## Executive Summary

**Superpowers** is a distributed, cross-platform skill ecosystem designed to enforce proven AI development workflows. It's a Claude Code plugin that bootstraps agents with structured, reusable process documentation — teaching AI agents how to brainstorm, design, plan, implement, test, review, and ship code.

**Core thesis**: Disciplines like TDD, brainstorming, and code review are not suggestions — they are enforceable processes that prevent mistakes. When AI agents follow them rigorously, output quality increases dramatically.

**Key fact**: This is NOT a library. Superpowers is pure documentation (Markdown + YAML frontmatter). It has no runtime code except for the plugin bootstrap and hook system.

---

## Directory Structure

```
superpowers/
├── .opencode/
│   └── plugins/
│       └── superpowers.js           # OpenCode plugin bootstrap (injects skills path, bootstrap content)
├── hooks/
│   ├── hooks.json                   # Claude Code hook configuration
│   ├── hooks-cursor.json            # Cursor-specific hook config
│   ├── session-start                # SessionStart hook (Bash) — injects bootstrap content
│   └── run-hook.cmd                 # Windows hook runner wrapper
├── skills/                          # 14 core superpowers skills
│   ├── using-superpowers/           # Meta: How to use the skill system (injected at session start)
│   ├── brainstorming/               # Idea → design spec (hard gate on implementation)
│   ├── writing-plans/               # Design spec → implementation plan
│   ├── writing-skills/              # TDD-based skill authoring guide
│   ├── test-driven-development/     # RED → GREEN → REFACTOR cycle
│   ├── systematic-debugging/        # Finding root causes without guessing
│   ├── subagent-driven-development/ # Parallel task dispatch + two-stage review
│   ├── dispatching-parallel-agents/ # When and how to parallelize work
│   ├── executing-plans/             # Load, execute, and verify plans
│   ├── finishing-a-development-branch/ # Integration options (merge/PR/cleanup)
│   ├── requesting-code-review/      # How to get a security-aware code review
│   ├── receiving-code-review/       # How to interpret and respond to reviews
│   ├── using-git-worktrees/         # Isolated workspace management
│   └── verification-before-completion/ # Pre-ship quality gates
├── scripts/
│   ├── bump-version.sh              # Version synchronization across package.json and docs
│   └── sync-to-codex-plugin.sh      # Publish to Codex plugin registry
├── tests/
│   ├── claude-code/                 # Claude Code test suite (bash + CLI testing)
│   ├── explicit-skill-requests/     # Behavioral tests for skill invocation
│   ├── skill-triggering/            # Tests for skill discovery and loading
│   ├── subagent-driven-dev/         # Full workflow tests (go-fractals, svelte-todo)
│   ├── codex-plugin-sync/           # Registry sync verification
│   ├── brainstorm-server/           # WebSocket server tests (collaborative design)
│   └── opencode/                    # OpenCode-specific test scenarios
├── docs/
│   ├── README.opencode.md           # OpenCode installation and usage guide
│   ├── testing.md                   # Test infrastructure documentation
│   ├── plans/                       # Design docs for ongoing features
│   ├── specs/                       # Feature specifications
│   ├── windows/                     # Platform-specific guidance
│   └── superpowers/                 # Internal skill documentation
├── assets/
│   ├── app-icon.png                 # Brand asset
│   └── superpowers-small.svg        # Vector logo
├── package.json                     # Project metadata (name, version, entry point)
└── README.md                        # Installation and user guide
```

---

## Core Abstractions

### 1. Skill

A **skill** is a reusable, process-oriented reference guide. Skills are NOT:
- Tutorials
- Feature implementations
- Ad-hoc problem solutions

**What they are:**
- Proven techniques and patterns (TDD, debugging, code review)
- Step-by-step workflows with decision trees
- Reference documentation for tools and APIs
- Pressure-tested guidance that agents should follow rigorously

**Structure** (SKILL.md):
```yaml
---
name: skill-name-with-hyphens
description: "Use when [specific symptom/trigger] - [what it enables]"
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Decision tree or symptom checklist.

## The Process
Workflow steps, flowcharts, detailed guidance.

## Examples / Anti-Patterns / Advanced Topics
Context-specific advice.
```

**Frontmatter requirements**:
- `name`: Hyphenated, alphanumeric only (no parentheses)
- `description`: Max 500 chars. Start with "Use when..." — focus on *symptoms*, not process

**Key principle**: Skills override default system prompts but are overridable by user instructions (CLAUDE.md, GEMINI.md, AGENTS.md).

### 2. Plugin (Platform-Specific)

Superpowers adapts to different AI platforms via plugins:

| Platform | Plugin | Entry Point | Mechanism |
|----------|--------|-------------|-----------|
| **Claude Code** | Claude Code native plugin system | `package.json:main` → `.opencode/plugins/superpowers.js` | Hooks (SessionStart) + config injection |
| **OpenCode.ai** | OpenCode plugin manager | `opencode.json:plugin` array | Config hook + auto skills discovery |
| **Copilot CLI** | Copilot plugin system | Same `superpowers.js` | Hook system + skillspath discovery |
| **Cursor** | Cursor plugin system | Separate `hooks-cursor.json` | Adapted hook format |
| **Codex** | Registry-based | Published to Codex registry | Downloaded during project init |

All platforms use the **same** skill files and **same** hook bootstrap mechanism.

### 3. Hook System

Hooks are execution points where the plugin can inject context into agent sessions.

**Available hooks**:
- `SessionStart`: Fires when agent starts a new session. Injects bootstrap content (using-superpowers skill + context).
- `experimental.chat.messages.transform`: (OpenCode) Transforms message history before sending to LLM.

**Hook entry point**: `hooks/session-start` (Bash script)
- Reads `skills/using-superpowers/SKILL.md`
- Extracts content (strips YAML frontmatter)
- Wraps in `<EXTREMELY_IMPORTANT>` tags
- Injects into first user message of session
- Guards against double-injection (idempotent)

**Output format**: JSON with platform-specific fields:
- Claude Code: `hookSpecificOutput.additionalContext`
- OpenCode/Copilot: `additionalContext` (top-level, SDK standard)
- Cursor: `additional_context` (snake_case)

### 4. Bootstrap Content

When a session starts, superpowers injects:
1. Full text of `using-superpowers/SKILL.md`
2. Tool mapping for non-Claude-Code platforms (translates `TodoWrite` → `todowrite`, etc.)
3. Legacy warning (if old `~/.config/superpowers/skills` directory exists)

**Why injected, not in system prompt?**
- Avoids token bloat (system messages sent every turn in some models)
- Prevents "multiple system messages" errors (Qwen, others)
- Bootstrap is cached after first load (no repeated disk I/O)

### 5. Skill Path Registration

The plugin auto-discovers all superpowers skills by injecting the skills directory path into the config.

**How it works**:
1. Plugin reads `skills/` directory from plugin root
2. On config hook, appends path to `config.skills.paths`
3. Platform's native skill discovery finds SKILL.md files in that path
4. Agent can invoke skills via native `skill` tool (Claude Code, OpenCode, Copilot, etc.)

**Result**: No symlinks, no manual config edits. Skills are auto-registered on plugin install.

---

## Workflows and Decision Trees

### The Superpowers Workflow Stack

Skills are designed to be chained in a specific order:

```
1. USING-SUPERPOWERS (meta-skill, injected at bootstrap)
   ↓
2. BRAINSTORMING (if creating something new)
   ├─ Explore project context
   ├─ Ask clarifying questions
   ├─ Propose 2-3 approaches
   ├─ Present design
   ├─ Get approval
   └─→ Writing-Plans
   ↓
3. WRITING-PLANS (spec → implementation plan)
   ├─ Break spec into independent tasks
   ├─ Estimate complexity
   ├─ Sequence dependencies
   └─→ (Subagent-Driven or Executing-Plans)
   ↓
4. SUBAGENT-DRIVEN-DEVELOPMENT (if parallel, same session)
   ├─ Dispatch fresh subagent per task
   ├─ Two-stage review per task (spec, then quality)
   ├─ Continuous execution (no human in loop)
   └─→ Finishing-a-Development-Branch
       OR
4. EXECUTING-PLANS (if sequential, separate session)
   ├─ Load and review plan
   ├─ Execute each task
   └─→ Finishing-a-Development-Branch
   ↓
5. FINISHING-A-DEVELOPMENT-BRANCH (always final step)
   ├─ Verify tests pass
   ├─ Detect environment (worktree vs. normal repo)
   ├─ Present integration options (merge/PR/discard)
   └─→ DONE
```

**Hard gates**:
- **Brainstorming → Design required before ANY implementation** (hard-gate in skill)
- **TDD: Test BEFORE code** — if code is written first, delete it and restart
- **Two-stage review: Spec compliance BEFORE code quality** (both must pass)

### When to Use Which Skill

| Task | Skill | Reason |
|------|-------|--------|
| Starting new feature/project | brainstorming | Hard gate prevents premature implementation |
| Fixing bugs | test-driven-development | TDD finds root cause faster |
| Facing multiple unrelated failures | dispatching-parallel-agents | Parallelize investigation |
| Implementing large spec | subagent-driven-development | Fresh agent per task, two-stage review |
| Implementing medium spec, separate session | executing-plans | Load plan, execute, verify |
| Code quality concerns | requesting-code-review | Gets security-aware reviewer |
| Understanding a code review | receiving-code-review | How to interpret and respond |
| Workflow issues unclear | using-superpowers (meta) | Defines the entire system |

---

## Key Design Patterns

### Pattern 1: Skill as Process Documentation

Skills are **rigid documentation of proven processes**, not flexible guidelines.

Example (TDD):
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
Write code before the test? Delete it. Start over.
```

**Why rigid?**
- Shortcuts cause bugs
- AI agents rationalize away discipline
- Written rules prevent rationalization

**Enforcement mechanism**: Skills contain red-flag tables listing common rationalizations and why they're wrong.

### Pattern 2: Pressure-Tested Skills (TDD Dogfooding)

New skills are written using TDD:
1. **RED**: Run a baseline scenario with subagents. Document exactly how they violate the desired process.
2. **GREEN**: Write skill documentation addressing those specific violations.
3. **REFACTOR**: Find new loopholes, plug them, re-verify.

Skills are tested with real subagent prompts, not just code.

### Pattern 3: Two-Stage Review (Subagent-Driven-Development)

After implementing a task:
1. **Spec compliance review**: Does code match the design spec?
2. **Code quality review**: Is the code well-structured, tested, etc.?

Both reviewers must pass. This prevents "it works but is a mess" code.

### Pattern 4: Fresh Subagent Per Task

Instead of one agent implementing everything:
- Each task gets its own subagent with focused context
- No pollution from previous task history
- Coordinator agent stays fresh for orchestration

### Pattern 5: Hard Gates (Brainstorming, TDD)

Some skills have **hard gates** that must be passed before proceeding:
- Brainstorming: No implementation until design is approved
- TDD: No production code without failing test first

These are not "guidelines" — they are prerequisites.

---

## Interactions Between Skills

### Brainstorming → Writing-Plans

**Output of brainstorming**: Design spec document  
**Input to writing-plans**: That design spec  
**Transition**: "Invoke writing-plans skill to create implementation plan"

### Writing-Plans → Subagent-Driven-Development

**Output of writing-plans**: Implementation plan with task list  
**Input to subagent-driven-development**: That plan  
**Transition**: Execute plan by dispatching fresh subagent per task

### Subagent-Driven-Development → Finishing-a-Development-Branch

**Output of subagent-driven-development**: All tasks completed, tests pass  
**Input to finishing-a-development-branch**: Current repo state  
**Transition**: "Invoke finishing-a-development-branch to complete this work"

### Error Paths

If a skill encounters a blocker:
- **Brainstorming**: Needs more context → ask clarifying questions
- **TDD**: Test doesn't capture requirement → revise test, not code
- **Subagent-Driven**: Task blocked → assess blocker type, escalate if needed
- **Code Review**: Reviewer finds issues → implementer fixes and re-submits

---

## Dependencies and External Systems

### Runtime Dependencies
- **None**. Superpowers is pure documentation.

### Platform Dependencies
- **Claude Code CLI**: For testing and hookruntime
- **Node.js**: For plugin bootstrap (superpowers.js runs in Node runtime)
- **Bash**: For hook scripts and version management
- **Git**: For worktree tests and version bumping

### Optional Integrations
- **Codex Plugin Registry**: For distributing to Codex users
- **OpenCode.ai**: Native plugin manager
- **WebSocket server** (tests/brainstorm-server): For potential collaborative design features

---

## Plugin Bootstrap Mechanism (Deep Dive)

### How superpowers.js Works

When a project loads the superpowers plugin:

1. **Plugin initialization** (`SuperpowersPlugin` export):
   - Called once at plugin load time
   - Receives `{ client, directory }` context
   - Returns object with hooks

2. **Config hook**:
   ```javascript
   config: async (config) => {
     config.skills = config.skills || {};
     config.skills.paths = config.skills.paths || [];
     if (!config.skills.paths.includes(superpowersSkillsDir)) {
       config.skills.paths.push(superpowersSkillsDir);
     }
   }
   ```
   - Runs once at config load time
   - Modifies `config` singleton in-place
   - All subsequent skill lookups find superpowers skills

3. **Messages transform hook** (OpenCode):
   ```javascript
   'experimental.chat.messages.transform': async (_input, output) => {
     // Inject bootstrap content into first user message
   }
   ```
   - Runs before each agent step
   - Checks if bootstrap already injected (idempotent)
   - Prepends bootstrap to first user message

### Bootstrap Caching

Module-level cache prevents repeated I/O:
```javascript
let _bootstrapCache = undefined; // undefined = not loaded, null = missing
const getBootstrapContent = () => {
  if (_bootstrapCache !== undefined) return _bootstrapCache;
  // Read file, parse, cache
  _bootstrapCache = <content>;
  return _bootstrapCache;
};
```

**Benefit**: One file read per session instead of potentially dozens.

### SessionStart Hook (Bash)

For Claude Code and other platforms using hook scripts:

1. **Bash script** (`hooks/session-start`):
   - Reads using-superpowers/SKILL.md
   - Escapes for JSON embedding
   - Outputs JSON with platform-specific field names

2. **Platform detection**:
   ```bash
   if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
     # Cursor: use additional_context
   elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
     # Claude Code: use hookSpecificOutput.additionalContext
   else
     # Copilot CLI, others: use additionalContext
   fi
   ```

3. **Legacy warning**:
   - Checks for old `~/.config/superpowers/skills`
   - If found, injects warning message
   - User must migrate to `~/.claude/skills`

---

## Testing Strategy

### Test Layers

1. **Content tests** (fast, ~2 min):
   - Verify skill exists and is loadable
   - Check frontmatter is valid
   - Spot-check key requirements documented

2. **Behavioral tests** (medium, ~5 min):
   - Run real Claude Code prompts
   - Verify agent produces expected behavior
   - Example: Requesting code review → reviewer catches planted bugs

3. **Integration tests** (slow, ~10-30 min):
   - Create real test projects
   - Execute full workflow end-to-end
   - Verify subagents follow skill, code works, tests pass

### Test Infrastructure

**helpers** (`tests/claude-code/test-helpers.sh`):
```bash
run_claude "prompt" [timeout]           # Execute Claude with prompt
assert_contains output pattern name     # Verify pattern exists
assert_count output pattern count name  # Verify exact count
create_test_project                     # Create temp test dir
create_test_plan project_dir            # Create sample plan
```

**test runner** (`tests/claude-code/run-skill-tests.sh`):
```bash
./run-skill-tests.sh              # Run fast tests (default)
./run-skill-tests.sh --integration # Run slow tests
./run-skill-tests.sh --verbose    # Show full output
./run-skill-tests.sh --timeout N  # Custom timeout
```

### Example Test Projects

- `tests/subagent-driven-dev/go-fractals`: Go project, Mandelbrot fractal
- `tests/subagent-driven-dev/svelte-todo`: Svelte frontend, todo app

Both test full workflow: brainstorm → design → plan → implement → review → finish.

---

## Version Management

### Version Bumping (`scripts/bump-version.sh`)

Centralized version control across multiple files:

```bash
./bump-version.sh 5.2.0   # Bump to 5.2.0
./bump-version.sh --check # Show current versions (detect drift)
./bump-version.sh --audit # Check + scan for undeclared files
```

**Configuration** (`.version-bump.json`):
```json
{
  "files": [
    { "path": "package.json", "field": "version" },
    { "path": "docs/superpowers/plans/foo.md", "field": "version" }
  ],
  "audit": { "exclude": ["CHANGELOG.md", "node_modules/"] }
}
```

**Why?**
- Single source of truth for version
- Prevents drift (package.json ≠ docs)
- Audit finds undeclared references automatically

---

## Platform Support

### Claude Code (Native)
- **Plugin**: `.opencode/plugins/superpowers.js`
- **Hooks**: `hooks/hooks.json` + `hooks/session-start`
- **Skills discovery**: Auto via config injection
- **Tests**: Full suite in `tests/claude-code/`

### OpenCode.ai
- **Plugin**: Same JavaScript, OpenCode plugin manager
- **Entry**: `opencode.json:plugin` array
- **Skills discovery**: Auto via config hook
- **Tool mapping**: `skill` tool (native)
- **Docs**: `docs/README.opencode.md`

### Copilot CLI
- **Plugin**: Same JavaScript
- **Hook detection**: Checks `$COPILOT_CLI` env var
- **Tool mapping**: Adapts to Copilot tool names
- **Status**: Tested, working

### Cursor
- **Plugin**: Cursor plugin system
- **Hooks**: `hooks/hooks-cursor.json` (snake_case fields)
- **Status**: Platform-specific hook formatting

### Codex
- **Distribution**: Registry-based (not Git clone)
- **Installation**: Via Codex plugin manager
- **Sync**: `scripts/sync-to-codex-plugin.sh`

---

## Key Insights

### Insight 1: Skills Are Discipline Codification

Superpowers succeeds because it codifies proven disciplines (TDD, design-before-code, two-stage review) as **non-negotiable processes**, not suggestions. Hard gates prevent agents from rationalizing away discipline.

### Insight 2: Plugin Bootstrap Is Minimal

The plugin code is tiny (~150 LOC in superpowers.js, ~60 in session-start Bash). Most "logic" is in skill documentation. This is intentional — keep the runtime simple, move all wisdom into readable Markdown.

### Insight 3: Skills Are Pressure-Tested

New skills are written using TDD: run baseline scenario, watch agent fail, write skill, verify pass, refactor to close loopholes. This ensures skills actually work.

### Insight 4: Platform Abstraction Is Clean

All platforms (Claude Code, OpenCode, Copilot, Cursor, Codex) use the same skill files and almost identical plugins. Platform differences are isolated to hook format and tool names.

### Insight 5: Fresh Subagents Prevent Context Pollution

Instead of one massive agent context, subagent-driven-development spawns fresh agents per task. This avoids "attention diffusion" — where large contexts cause agents to lose focus on the current task.

---

## Extensibility

### Adding a New Skill

1. Create `skills/my-skill/SKILL.md`
2. Write YAML frontmatter + Markdown content
3. Test with subagent baseline scenario (RED → GREEN → REFACTOR)
4. Add to version bump config if needed
5. Auto-discovered on next plugin load

### Adding a New Platform

1. Create `hooks/hooks-<platform>.json` if hook format differs
2. Update `superpowers.js` platform detection (if needed)
3. Document in `docs/`
4. Test integration

### Adding Custom Skills to Project

Users can create project-specific skills:
- Claude Code: `~/.claude/skills/my-skill/SKILL.md`
- OpenCode: `~/.config/opencode/skills/my-skill/SKILL.md`
- Codex: `.codex/skills/my-skill/SKILL.md`

---

## Files of Interest

| File | Purpose | Type |
|------|---------|------|
| `.opencode/plugins/superpowers.js` | Plugin bootstrap, config injection | JavaScript |
| `hooks/session-start` | SessionStart hook, injects bootstrap | Bash |
| `skills/using-superpowers/SKILL.md` | Meta-skill, system rules, when to use other skills | Documentation |
| `skills/brainstorming/SKILL.md` | Design before code (hard gate) | Process documentation |
| `skills/writing-plans/SKILL.md` | Spec → implementation plan | Process documentation |
| `skills/test-driven-development/SKILL.md` | RED → GREEN → REFACTOR | Process documentation |
| `skills/subagent-driven-development/SKILL.md` | Parallel task execution, two-stage review | Process documentation |
| `skills/writing-skills/SKILL.md` | How to author new skills using TDD | Meta-documentation |
| `tests/claude-code/run-skill-tests.sh` | Test runner (fast + integration) | Bash harness |
| `scripts/bump-version.sh` | Version synchronization across files | Bash utility |
| `docs/README.opencode.md` | OpenCode-specific installation guide | User documentation |

---

## Summary

Superpowers is a **skill ecosystem and plugin framework** that teaches AI agents proven development workflows. Its architecture is minimal (lightweight plugin + hook system) by design — the real intelligence lives in structured Markdown documentation of proven processes (TDD, brainstorming, code review, debugging). 

The system scales across multiple platforms (Claude Code, OpenCode, Copilot, Cursor, Codex) without duplication. Skills are pressure-tested with real subagent scenarios before deployment. Hard gates (brainstorming before code, TDD before implementation) prevent agents from rationalizing away discipline.

**Core principle**: Make it impossible for AI agents to skip proven workflows by making those workflows explicit, enforceable, and codified as non-negotiable process documentation.
