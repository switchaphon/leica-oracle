# Claude Code Changelog Repository - Code Snippets & Patterns

**Repository**: marckrenn/claude-code-changelog  
**Date Explored**: 2026-06-06  
**Purpose**: Unofficial tracking of Claude Code prompt and feature-flag evolution across releases

## Project Overview

The Claude Code Changelog is a documentation repository that tracks the evolution of Claude Code system prompts, tool descriptions, feature flags, and CLI surface across versions. It is not a traditional source code project with executable code, but rather a structured documentation archive.

**Key Files**:
- `/README.md` - Main documentation and how to use the repository
- `/cc-prompt.md` - Legacy compatibility file per tag containing full system prompt
- `/cc-flags.md` - Legacy compatibility file per tag containing feature flags
- `/system-prompts/` - Extracted prompt artifacts grouped by category (49 files)
- `/meta/` - Derived metadata, statistics, and CLI surface documentation
- `/indices/` - Indexing tables for prompt artifacts organized by tokens, init date, last edit

## Repository Structure Patterns

### Metadata Organization

The repository uses a metadata-driven structure with the following organization:

**File**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/meta/metadata.md`

Tracked metadata includes:
- Package reference: `@anthropic-ai/claude-code`
- Bundle metrics: 29.5M bytes, 757,189 lines
- Prompt token distribution by kind
- Token p95/p99: 2,251 / 3,488
- Token breakdown: tools (90.3%), system-reminder (5.8%), system-data (1.8%), skill (0.9%), system (0.8%), agent (0.4%)

**File**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/meta/prompt-stats.md`

Prompt categorization strategy:
- System prompts (2 files)
- Tool prompts (44 files)
- Agent prompts (1 file)
- Skills (1 file)
- System reminders (1 file)

### CLI Surface Inventory

**File**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/meta/cli-surface.md`

Command surface tracking:
- 41 Commands
- 94 Options
- 620 Environment variables
- 0 Config keys
- 10 Tools
- 10 Skills
- 106 Models
- 8 Providers

Sample commands tracked:
- `add`, `add-from-claude-desktop`, `add-json`, `agents`, `auth`, `auto-mode`
- `config`, `doctor`, `enable`, `disable`, `init`, `install`
- `list`, `login`, `logout`, `mcp`, `plugin`, `setup`

### Feature Flags System

**File**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/cc-flags.md`

Pattern: Versioned feature gates and dynamic configuration:

```
# Claude Code Flags 2.1.167

## Feature Gates
- tengu_ccr_bridge
- tengu_ccr_bundle_seed_enabled
- tengu_harbor

## Dynamic Configs
- tengu_auto_mode_config
- tengu_bridge_min_version
- tengu_bridge_poll_interval_config
- tengu_bridge_repl_v2_config
- tengu_desktop_upsell
- tengu_iron_gate_closed
- tengu_kairos_brief
- tengu_kairos_cron
- tengu_kairos_cron_config
- tengu_kairos_cron_durable
- tengu_kairos_push_notifications
- tengu_malort_pedway
- tengu_max_version_config
- tengu_version_config
```

Naming convention: Prefix `tengu_` for internal feature gates, descriptive kebab-case suffixes.

## System Prompt Patterns

### Tool Descriptions (44 Files)

**Pattern**: Each tool has a standardized description with JSON schema definition.

**File Example**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/system-prompts/tool-description-grep.md`

Structure:
```markdown
# Tool Description: grep

- Source: native-prompt-markdown-tool

## Summary
A powerful search tool built on ripgrep Usage: - ALWAYS use Grep for search tasks.

# Raw Prompt Text
[Full prompt text with usage guidelines, parameter descriptions, examples]

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "pattern": {
      "description": "The regular expression pattern to search for in file contents",
      "type": "string"
    },
    "path": {
      "description": "File or directory to search in (rg PATH). Defaults to current working directory.",
      "type": "string"
    },
    [... more properties ...]
  },
  "required": ["pattern"],
  "additionalProperties": false
}
```

Key tool descriptions tracked (by token size):

1. **Bash Execution** (3,488 tokens)
   - Executes bash commands with output capture
   - Complex parameter handling for timeouts, backgrounds, descriptions

2. **Agent Tool** (2,251 tokens)
   - Launches specialized agents for complex tasks
   - Supports subagent types: Explore, general-purpose, Plan, statusline-setup
   - Parameters: description, prompt, subagent_type, model, run_in_background, isolation

3. **Skill Invocation** (1,774 tokens - latest version)
   - Evolved through 33+ versions (v2.1.128 to v2.1.142+)
   - Pattern shows progressive expansion of skill capabilities
   - Parameters: skill name, optional args

4. **Grep Tool** (1,115 tokens)
   - Ripgrep-based content search
   - Output modes: content, files_with_matches, count
   - Context parameters: -B, -A, -C, multiline support

5. **Bash Command Execution** (3,060 tokens, variant)
   - Extended safety instructions
   - Comprehensive error handling documentation
   - Git operation safety protocols

### Tool Description Source Patterns

Tools are sourced from:
- `native-prompt-markdown-tool` - Standard tools with markdown documentation
- `native-reference-match` - Reference-backed implementations with placeholder hints

Example from `/tool-description-edit.md`:

```
# Tool Description: edit

- Source: native-reference-match

## Summary
Performs exact string replacements in files.

Usage:
- You must use your `Read` tool at least once in the conversation before editing
- Preserve exact indentation (tabs/spaces) as it appears AFTER line number prefix
- ALWAYS prefer editing existing files in the codebase
- The edit will FAIL if `old_string` is not unique in the file
- Use `replace_all` for replacing and renaming strings across the file
```

### System Prompts (2 Files)

1. **Auto Mode Classifier Rules Review** (580 tokens)
   - Source: native-reference-match
   - Evaluates clarity and completeness of classifier rules

2. **Reference Documentation for Agents** (1,326 tokens)
   - Source: native-reference-match
   - Guidance on language-specific documentation for agents
   - Contains 22+ placeholder expressions (EXPR_1 through EXPR_22)

### Agent Prompts (1 File)

**File**: `agent-prompt-auto-mode-rule-reviewer.md`
- 312 tokens
- Initialized in v2.1.118, last edited in v2.1.167
- Purpose: Evaluate clarity and completeness of classifier rules

### Skills (1 File)

**File**: `skill-build-with-claude-api-reference-guide.md`
- 675 tokens
- API reference guidance for building Claude API applications

### System Reminders (1 File)

**File**: `system-reminder-anthropic-billing-header-version-native.md`
- 4,189 tokens
- Billing and version tracking header information
- Pattern: `x-anthropic-billing-header: cc_version=2.1.167.native; cc_entrypoint=sdk-cli; cch=00000;`

## Indexing Strategy

### By Tokens (Descending)

**File**: `/indices/system-prompts-by-token.md`

Top tools by token count:
1. Bash command execution (3,488 tokens)
2. Bash variant (3,060 tokens)
3. Agent tool (2,251 and 1,977 tokens)
4. Skill invocation (1,774 tokens, latest)
5. Grep (1,115 tokens)

### By Initialization Date (Newest First)

**File**: `/indices/system-prompts-by-init.md`

Most recently introduced tools (v2.1.141+):
- Skill invocation variants 9-33 (all at v2.1.141)
- Read local file content (v2.1.150)
- Earlier tools initialized at v2.1.118

### By Last Edit Date (Newest First)

**File**: `/indices/system-prompts-by-last-edit.md`

Most recently updated (v2.1.167):
- Tool descriptions: executes-bash, edit, grep, invoke-in-conversation variants
- System prompts: auto-mode-classifier, reference-documentation
- System reminders: anthropic-billing-header
- Agent prompt: auto-mode-rule-reviewer
- Skill: build-with-claude-api-reference-guide

## Configuration Pattern

**File**: `/Users/switchaphon/ghq/github.com/marckrenn/claude-code-changelog/cc-prompt.md`

Entry point header pattern:
```
Release Date: Unknown

# User Message
[System reminders and deferred tool definitions]
[Skill listings]
[User-facing context]

# System Prompt
x-anthropic-billing-header: cc_version=2.1.167.native; cc_entrypoint=sdk-cli; cch=00000;

[Security and capability guidelines]

# Harness
[Text output and tool use instructions]

# Text output guidance
[Response formatting rules]

# Tools
[Agent tool specification with subagent types]
[Bash tool specification]
[Edit tool specification]
[... additional tools ...]
```

## Key Patterns & Idioms

### 1. Version Tracking with Tags

Pattern: Semantic versioning with git tags
- Format: `vX.Y.Z` (e.g., v2.1.167)
- Used for: Historical comparison, release navigation

### 2. Prompt Composition

Pattern: Modular prompt system with:
- Base system prompt + dynamic reminders
- Tool descriptions with JSON schemas
- Context blocks (harness, text output, environment)
- Deferred tool loading for large schemas

### 3. Tool Safety Protocols

Patterns observed:
- Read-before-edit requirement (Edit tool)
- Permission-based tool access
- Git safety guards (no --force without explicit request)
- Hook execution controls

### 4. Placeholder System

Pattern: Templated prompt expressions with hints
- Format: `EXPR_N` placeholders
- Resolved at runtime based on context
- Tracks source (native-reference-match, native-prompt-markdown-tool)

### 5. Token Optimization

Pattern: Multiple versions of same tool
- Skill invocation has 33+ versions (token reduction pattern)
- Tracks p95/p99 percentiles
- Total system ~72K tokens

## Error Handling Examples

### Tool Invocation Safety

From `tool-description-invoke-in-conversation.md`:
```
Important:
- Available skills are listed in system-reminder messages in the conversation
- Only invoke a skill that appears in that list
- NEVER guess or invent a skill name from training data
- If you see a <command-name> tag, the skill has ALREADY been loaded
- Do not invoke a skill that is already running
```

### Edit Tool Constraints

From `tool-description-edit.md`:
```
- You must use your `Read` tool at least once before editing
- Preserve exact indentation (tabs/spaces)
- The edit will FAIL if `old_string` is not unique
- Use `replace_all` for multiple occurrences
```

### Bash Tool Permissions

Pattern: Permission modes for tool execution
- Denied calls means user declined it
- Adjust behavior rather than retry verbatim
- Hook output treated as user feedback

## Metadata Statistics

**Latest Version**: 2.1.167

**Snapshot Timing**:
- Generated: 2026-06-06 01:40:53 UTC
- Embedded build timestamp: 2026-06-05 23:07:45 UTC
- Lag: 2 hours 33 minutes 8 seconds

**Bundle Composition**:
- Entry bytes: 29,543,062
- Entry lines: 757,189
- File count: 4
- Extension distribution: JSON (1 file, 289 bytes), MD (2 files, 297 bytes)

## Key Documentation Files

1. **README.md** - How to navigate and interpret the repository
2. **cc-prompt.md** - Full system prompt for current version
3. **cc-flags.md** - Feature flags and dynamic configs
4. **meta/metadata.md** - Bundle composition and statistics
5. **meta/prompt-stats.md** - Token and character counts per prompt
6. **meta/cli-surface.md** - Command, option, and tool inventory
7. **meta/flags.md** - Detailed feature flag listings
8. **indices/system-prompts-by-token.md** - Prompts sorted by token count
9. **indices/system-prompts-by-init.md** - Prompts by initialization version
10. **indices/system-prompts-by-last-edit.md** - Prompts by modification date

## Data Quality Notes

- Token totals are estimates; small differences expected
- Token counts vary by model/tokenizer/runtime
- Estimated LOC derived from prettified bundle line count (approximation)
- Files can contain intentional duplicates or near-duplicates
- File names may change across versions (renames/splits/merges)
- Single conceptual prompt can appear under multiple files
- Compare statistical deltas with raw diffs before drawing conclusions

## Entry Points & Usage

### For Version Comparison
1. Pick two tags: `https://github.com/marckrenn/claude-code-changelog/compare/v2.1.44...v2.1.45#files_bucket`
2. Use `system-prompts/` for per-file artifacts
3. Use `meta/` for aggregate metrics

### For Historical Analysis
- Use Init / Last edit columns as lifecycle hints
- For deep research, point coding agents at the repo directly
- GitHub Copilot has limited broad historical search capability on large repos

## Related Resources

- **Reference**: [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)
- **Foundation**: [cchistory](https://github.com/badlogic/cchistory)
- **Technical Deep-Dive**: [How cchistory works](https://mariozechner.at/posts/2025-08-03-cchistory/)
- **Official Docs**: [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- **Package**: [Claude Code on npm](https://www.npmjs.com/package/@anthropic-ai/claude-code)

## Summary

The Claude Code Changelog repository demonstrates sophisticated patterns for:
1. **Versioned documentation archiving** with semantic version tags
2. **Modular prompt composition** with tool definitions and JSON schemas
3. **Metadata-driven organization** for multi-dimensional indexing (tokens, init date, last edit)
4. **Safety-first tooling patterns** with read-before-edit, permission modes, and hook execution
5. **Progressive refinement** shown through multiple versions of same tool (token optimization)
6. **Comprehensive tracking** of CLI surface, feature gates, and prompt evolution

The repository serves as a reference implementation for how to systematically track and document the evolution of complex, production AI system prompts over time.
