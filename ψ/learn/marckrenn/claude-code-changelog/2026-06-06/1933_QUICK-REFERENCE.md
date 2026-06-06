# Claude Code Changelog – Quick Reference

## What This Project Does

This is an **unofficial, community-maintained archive** that tracks the evolution of Claude Code's system prompts, feature flags, and CLI surface across releases. It documents what Claude Code does behind the scenes — the instructions it follows, the tools it can use, and the configuration options that control its behavior.

Think of it as a persistent changelog for Claude Code internals. Each release gets snapshotted with:
- System prompts (instructions Claude Code follows)
- Feature flags and dynamic configs
- CLI commands and options
- Tool descriptions
- Prompt statistics and token counts

**Real use**: Compare two versions to see what changed, understand how features evolved, audit security/compliance changes, or track prompt engineering evolution.

---

## Installation & Access

### 1. Browse Online
- **GitHub repo**: https://github.com/marckrenn/claude-code-changelog
- **Compare versions**: `https://github.com/marckrenn/claude-code-changelog/compare/v2.1.44...v2.1.45#files_bucket`
- **X account (updates)**: [@ClaudeCodeLog](https://x.com/ClaudeCodeLog)

### 2. Clone the Repository
```bash
git clone https://github.com/marckrenn/claude-code-changelog.git
cd claude-code-changelog
```

### 3. No Installation Required
The repo is read-only reference material. Just browse files or use GitHub's compare view.

---

## Project Structure

```
claude-code-changelog/
├── README.md                 # Overview and how to read
├── cc-prompt.md             # Latest system prompt (legacy compat file)
├── cc-flags.md              # Latest feature flags (legacy compat file)
├── system-prompts/          # Extracted prompt artifacts
│   ├── tool-description-*.md
│   ├── system-prompt-*.md
│   ├── agent-prompt-*.md
│   └── skill-*.md
├── meta/                    # Structured summaries
│   ├── metadata.md          # Build info, file counts, token stats
│   ├── cli-surface.md       # Commands, options, env vars
│   ├── flags.md             # Feature gates, dynamic configs
│   └── prompt-stats.md      # Token distribution by type
├── indices/                 # Historical cross-references
│   ├── system-prompts-by-token.md
│   ├── system-prompts-by-init.md
│   └── system-prompts-by-last-edit.md
└── [version tags]           # Git tags (v2.1.44, v2.1.45, etc.)
```

---

## Key Features with Examples

### 1. Per-Version Snapshots
Each Claude Code release gets tagged with system prompt and flag data:
- **Tags**: `v2.1.167`, `v2.1.166`, etc. → Git historical tags
- **Files**: Same snapshot in repo root and per-tag branches
- **Tracking**: System prompts extracted from Claude Code bundles

**Example usage:**
```bash
# Check what a specific version included
git show v2.1.167:cc-prompt.md | head -100

# Compare two versions side by side
git diff v2.1.166 v2.1.167 -- system-prompts/
```

### 2. System Prompts Archive
44+ extracted prompt artifacts organized by category:

| Type | Example | What it does |
|------|---------|------------|
| **Tool prompts** | `tool-description-bash.md` | Instructions for Bash tool (3,488 tokens) |
| **System prompts** | `system-prompt-auto-mode-classifier.md` | Rules for auto-mode decision logic |
| **Agent prompts** | `agent-prompt-auto-mode-rule-reviewer.md` | Guidance for agent-based rule review (312 tokens) |
| **Skills** | `skill-build-with-claude-api-reference.md` | Reference docs for Claude API skill |
| **System reminders** | `system-reminder-billing-header.md` | Billing and version tracking |

**Browse current prompts:**
```bash
ls system-prompts/ | wc -l  # Total: 49 files
cat system-prompts/tool-description-bash.md | head -50
```

### 3. Structured Metadata
Pre-computed indices for quick lookups:

**`meta/cli-surface.md`** — Claude Code's entire CLI:
- 41 commands (`add`, `init`, `agents`, `mcp`, etc.)
- 94 options/flags (`--model`, `--agent`, `--force`, etc.)
- 620 environment variables
- 10 tools (Bash, Read, Edit, Glob, Grep, Agent, Skill, ToolSearch, Write, ScheduleWakeup)
- 10 built-in skills

**`meta/prompt-stats.md`** — Token analysis:
- Total: 72,653 tokens across all prompts
- Breakdown: 90.3% tool prompts, 5.8% system reminders, 1.8% system data, etc.
- Per-file token counts and first-introduction versions

**`meta/metadata.md`** — Build provenance:
- Bundle size: ~29.5 MB (757K lines)
- Build timestamp tracking
- File inventory and extension counts

### 4. Version Comparison
Compare releases easily:

**On GitHub:**
```
https://github.com/marckrenn/claude-code-changelog/compare/v2.1.166...v2.1.167
```
Shows: added/modified/deleted prompts, flag changes, CLI surface changes.

**Locally:**
```bash
git log --oneline v2.1.160..v2.1.167 --  # Commits between versions
git diff v2.1.160..v2.1.167 -- meta/     # Metadata deltas
```

### 5. Historical Indices
Three ways to find a prompt:

**By token count** (`indices/system-prompts-by-token.md`):
```
1. tool-description-executes-given-bash... — 3,488 tokens (Bash tool)
2. tool-description-launch-new-agent... — 2,251 tokens (Agent tool)
3. tool-description-invoke-skill... — 1,774 tokens (Skill tool)
...
```

**By first introduction** (`indices/system-prompts-by-init.md`):
```
First seen in v2.1.118: Bash tool, Read tool, Edit tool, ...
First seen in v2.1.133: invoke-in-conversation-2, ...
...
```

**By last modification** (`indices/system-prompts-by-last-edit.md`):
```
v2.1.167 (latest): Bash tool, Agent tool, Billing header
v2.1.166: File pattern matching tool
...
```

---

## Configuration & CLI Usage

### Main Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `tag [path]` | Tag current version | `claude tag` |
| `init <name>` | Initialize CLAUDE.md | `claude init my-project` |
| `auth` | Authenticate with Anthropic | `claude auth` |
| `config` | View/edit configuration | `claude config --json` |
| `agents` | List available agents | `claude agents` |
| `mcp` | Manage MCP servers | `claude mcp list` |
| `status` | System health check | `claude status` |
| `validate <path>` | Validate code/config | `claude validate ./src` |

### Key Flags

| Flag | Use case | Example |
|------|----------|---------|
| `--model <model>` | Select Claude model | `--model claude-opus-4-7` |
| `--agent <agent>` | Spawn specific agent | `--agent explore` |
| `--effort <level>` | Review depth (low/medium/high/ultra) | `--effort high` |
| `--force` | Skip confirmations | `--force` |
| `--debug` | Enable debug logging | `-d` |
| `--timeout <min>` | Session timeout | `--timeout 120` |
| `--tools <tools>` | Allowed tools | `--tools bash,read,edit` |
| `--permission-mode <mode>` | Auth mode | `--permission-mode open` |

### Environment Variables

**Key settings** (620 total documented):
```bash
# API & Auth
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-7
CLAUDE_CODE_ENABLE_AUTO_MODE=1

# Behavior
CLAUDE_CODE_MAX_TURNS=50
CLAUDE_CODE_TIMEOUT_MS=120000
CLAUDE_CODE_DEBUG_LOG_LEVEL=debug

# Storage
CLAUDE_CONFIG_DIR=~/.claude
CLAUDE_CODE_PLUGIN_CACHE_DIR=~/.cache/claude-code

# Features
CLAUDE_CODE_ENABLE_THINKING=1
CLAUDE_CODE_DISABLE_AUTO_MEMORY=0
CLAUDE_CODE_ENABLE_XAA=1  # External AI agents
```

### Feature Flags

Two categories:

**Feature Gates** (3):
- `tengu_ccr_bridge` — Bridge compatibility
- `tengu_ccr_bundle_seed_enabled` — Bundle seeding
- `tengu_harbor` — Harbor feature

**Dynamic Configs** (17):
- `tengu_auto_mode_config` — Auto-mode parameters
- `tengu_kairos_cron_config` — Cron task config
- `tengu_kairos_push_notifications` — Notification settings
- `tengu_bridge_min_version`, `tengu_bridge_repl_v2_config`, etc.

---

## Common Workflows

### 1. Track Prompt Evolution
**Goal**: See how a tool's instructions changed over time

```bash
# Check Bash tool across versions
git log --oneline -- system-prompts/tool-description-bash.md | head -10

# View diff between two versions
git diff v2.1.165:system-prompts/tool-description-bash.md \
         v2.1.167:system-prompts/tool-description-bash.md

# Get full history for one prompt
git log -p -- system-prompts/tool-description-agent.md | head -500
```

### 2. Audit CLI Changes
**Goal**: What commands/flags were added/removed?

```bash
# Compare CLI surface
git diff v2.1.160 v2.1.167 -- meta/cli-surface.md

# Extract just command additions
git show v2.1.167:meta/cli-surface.md | grep "Commands:"
```

### 3. Understand Token Budget
**Goal**: How are tokens allocated across prompts?

```bash
# View full distribution
cat meta/prompt-stats.md

# Find token-heavy prompts
cat indices/system-prompts-by-token.md | head -20

# Check growth over releases
git log --oneline --all -- meta/metadata.md | tail -5
```

### 4. Research Feature Stability
**Goal**: When was a feature introduced? When was it last changed?

```bash
# Check when agent-prompt was added
git log --diff-filter=A --name-only --pretty=%h -- system-prompts/agent-*.md

# Find unstable prompts (changed frequently)
git log --oneline -- system-prompts/ | cut -d' ' -f1 | \
  while read commit; do git show $commit --name-only --pretty= ; done | \
  sort | uniq -c | sort -rn | head -20
```

### 5. Compare Two Releases Thoroughly
**Goal**: Full audit of what changed between v2.1.166 and v2.1.167

```bash
# Overview of changes
git log v2.1.166..v2.1.167 --oneline

# Which files changed
git diff --name-only v2.1.166 v2.1.167

# Detailed diffs by category
git diff v2.1.166 v2.1.167 -- system-prompts/   # Prompt changes
git diff v2.1.166 v2.1.167 -- meta/             # Metadata changes
git diff v2.1.166 v2.1.167 -- cc-flags.md       # Flag changes

# Stats summary
git diff --stat v2.1.166 v2.1.167
```

---

## Data Quality & Interpretation

**What's tracked accurately:**
- System prompts (verbatim extraction from Claude Code bundle)
- CLI commands and flags (parsed from help output)
- Version tags and release dates

**Caveats:**
- Token counts are **estimates** (tokenizer varies by model/runtime)
- Near-duplicates exist intentionally (skill variants)
- File names can change across versions even if content doesn't
- LOC estimates ±10% (derived from prettified bundle)
- Small statistical deltas need context (compare raw diffs too)

**How data is generated** (@ClaudeCodeLog automation):
1. Detect new Claude Code releases
2. Extract system prompts from bundle
3. Parse feature flags and CLI surface
4. Generate structured summaries
5. Compute token counts
6. Publish diffs on X/Twitter

---

## Real-World Examples

### Example 1: Investigating a Tool Change
*"Why did the Bash tool behavior change in v2.1.167?"*

```bash
git diff v2.1.166:system-prompts/tool-description-bash.md \
         v2.1.167:system-prompts/tool-description-bash.md
```
Output: Shows exact instruction changes, new warnings, permission clarifications.

### Example 2: Finding When a Feature Shipped
*"When was auto-mode added?"*

```bash
git log --all --diff-filter=A --name-only --pretty=%h:v%ai -- \
  system-prompts/agent-prompt-auto-mode* | head -1
```
Output: `abc1234:v2.1.118` (feature introduced in v2.1.118 on specific date).

### Example 3: Tracking Token Inflation
*"Have prompt tokens grown?*

```bash
for version in v2.1.160 v2.1.165 v2.1.167; do
  echo "=== $version ===" 
  git show $version:meta/metadata.md | grep "total prompt tokens"
done
```
Output: Shows token trend over 3 releases.

### Example 4: Security Audit
*"What security-relevant changes happened?"*

```bash
git log v2.1.160..v2.1.167 --oneline --grep="security\|permission\|auth"
git diff v2.1.160 v2.1.167 -- system-prompts/tool-* | grep -i "permission\|security\|auth"
```

---

## Key Resources

- **Main Repo**: https://github.com/marckrenn/claude-code-changelog
- **GitHub Releases**: https://github.com/marckrenn/claude-code-changelog/releases
- **X Updates**: [@ClaudeCodeLog](https://x.com/ClaudeCodeLog)
- **Claude Code Docs**: https://docs.anthropic.com/en/docs/claude-code
- **Claude Code NPM**: https://www.npmjs.com/package/@anthropic-ai/claude-code
- **Inspiration**: [cchistory](https://github.com/badlogic/cchistory)
- **Technical Deep-Dive**: [How cchistory works](https://mariozechner.at/posts/2025-08-03-cchistory/)

---

## Support & Contributing

**This is a community project** maintained by [@marckrenn](https://github.com/marckrenn).

**Support the maintainer:**
- Follow on X: [@ClaudeCodeLog](https://x.com/ClaudeCodeLog)
- GitHub Sponsors: https://github.com/sponsors/marckrenn
- Buy Me a Coffee: https://buymeacoffee.com/marckrenn

Server costs and token usage add up — contributions appreciated!

---

## Summary

Claude Code Changelog is a living reference for how Claude Code evolves. It captures:
- What prompts/instructions drive Claude Code behavior
- Which tools/commands are available and how they've changed
- Token budgets and complexity metrics
- Version-by-version evolution for auditing, comparison, and research

Perfect for developers who want to understand Claude Code's evolution, security researchers tracking permission changes, or teams auditing compliance over time.

**Start here**: Browse `/indices/` for quick lookups, or use GitHub compare view for release-to-release diffs.
