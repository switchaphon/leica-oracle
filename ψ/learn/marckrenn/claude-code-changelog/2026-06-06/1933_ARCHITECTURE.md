# Claude Code Changelog - Architecture

**Project**: https://github.com/marckrenn/claude-code-changelog  
**Type**: Data archive and tracking system  
**Status**: Active (tracks Claude Code releases and prompts)  
**Last Updated**: 2026-06-06

---

## Overview

Claude Code Changelog is an **unofficial, community-maintained historical archive** that tracks Claude Code's system prompts, feature flags, and CLI surface across all released versions. It functions as a deep-dive analytical resource for understanding how Claude Code evolves between releases.

The project is not traditional software with entry points and executable components. Instead, it is a **curated data repository** with generated documentation and indices that help users discover and compare prompt changes across versions.

---

## Directory Structure & Organization

```
claude-code-changelog/
├── README.md                      # Project overview and navigation guide
├── cc-prompt.md                   # Legacy full-prompt artifact (current version)
├── cc-flags.md                    # Legacy feature flags artifact (current version)
├── .github/
│   └── FUNDING.yml               # GitHub sponsorship config
├── system-prompts/               # Extracted prompt artifacts (49 files)
│   ├── tool-description-*.md     # Tool definition prompts (44 files)
│   ├── system-prompt-*.md        # Core system prompts (2 files)
│   ├── agent-prompt-*.md         # Agent-specific prompts (1 file)
│   ├── skill-*.md                # Skill instructions (1 file)
│   └── system-reminder-*.md      # Runtime reminders (1 file)
├── indices/                      # Curated index views of system prompts
│   ├── system-prompts-by-token.md      # Sorted by token count (descending)
│   ├── system-prompts-by-init.md       # Sorted by init version (newest first)
│   └── system-prompts-by-last-edit.md  # Sorted by last edit (newest first)
└── meta/                         # Derived metadata and statistics
    ├── metadata.md               # Build info, bundle stats, token distribution
    ├── cli-surface.md            # 41 commands, 94 options, 620 env vars, etc.
    ├── flags.md                  # Feature flags table with confidence/notes
    └── prompt-stats.md           # Per-prompt metrics (chars, tokens, lifecycle)
```

### Core Philosophy

**Clarity through organization**: The directory structure reflects a **discovery-first design**:
- `system-prompts/` contains raw artifacts in the format they appear in binaries
- `indices/` provides multiple entry points for the same data (sorted by tokens, version, edit date)
- `meta/` aggregates statistics for high-level understanding
- Root-level `cc-prompt.md` and `cc-flags.md` are legacy compatibility files per release tag

---

## Core Data Model

### 1. System Prompts (49 files)

Extracted prompt definitions organized by kind:

| Kind | Count | Purpose |
|------|-------|---------|
| **tool** | 44 | Tool/command descriptions sent to the model for tool use |
| **system** | 2 | Core system behavior rules and priorities |
| **agent** | 1 | Agent-specific prompt for auto-mode rule reviewer |
| **skill** | 1 | User-facing skill guidance (Claude API reference) |
| **system-reminder** | 1 | Runtime configuration/context reminder |

**Example tool**: `tool-description-edit.md` describes how the Edit tool works to Claude, including usage rules, parameter schemas, and constraints.

**Example system**: `system-prompt-auto-mode-classifier-rules-review.md` directs evaluation of classifier rule clarity.

### 2. Feature Flags (meta/flags.md)

Extracted feature flags table with columns:
- **Flag**: Internal flag identifier
- **Type**: `config` or `gate` (configuration vs. conditional enabling)
- **Category**: UI, tools, auth, safety, networking, filesystem, other
- **Summary**: What the flag controls
- **Confidence**: `high`, `medium`, `low` (extraction confidence)
- **Occurrences**: How many times the flag appears in the binary

**Example**: `tengu_auto_mode_config` gates auto-mode availability with circuit-breaker, model allowlist, and org allowlist checks.

### 3. CLI Surface (meta/cli-surface.md)

Aggregated CLI inventory:
- **41 Commands**: `add`, `agents`, `auth`, `auto-mode`, `config`, `init`, `install`, `login`, `mcp`, `plugin`, `project`, `status`, etc.
- **94 Options/Flags**: `--debug`, `--force`, `--model`, `--message`, `--worktree`, etc.
- **620 Environment Variables**: Mostly prefixed with `CLAUDE_CODE_*`, `ANTHROPIC_*`, plus system/cloud vars
- **10 Tools**: Agent, Bash, Edit, Glob, Grep, Read, ScheduleWakeup, Skill, ToolSearch, Write
- **10 Skills**: `claude-api`, `init`, `keybindings-help`, `loop`, `schedule`, `simplify`, `update-config`, etc.
- **106 Models**: Claude 1.3, 2.0, 2.1, 3-5-haiku, 3-5-sonnet, 3-7-sonnet, 4-opus, 4-5, etc.
- **8 Providers**: anthropic, aws, azure, bedrock, foundry, google, openai, vertex

### 4. Metadata & Statistics (meta/metadata.md, meta/prompt-stats.md)

**Bundle Info**:
- Entry bytes: ~29.5M
- Entry lines: 757,189
- File count: 4 (claude, LICENSE.md, package.json, README.md from @anthropic-ai/claude-code)
- Snapshot generated: 2026-06-06 01:40:53 UTC

**Token Distribution**:
- Total: 72,653 tokens
- Tool descriptions: 65,571 (90.3%)
- System reminders: 4,189 (5.8%)
- System data: 1,326 (1.8%)
- Skills: 675 (0.9%)
- System: 580 (0.8%)
- Agent: 312 (0.4%)

**Prompt Stats Table**: Per-prompt metrics including character count, token count, init version, last edit version, and lifecycle.

---

## Entry Points & Navigation

This is **not an executable project** with traditional entry points. Instead, navigation follows these patterns:

### 1. Primary Entry Point: README.md
- High-level overview of what's tracked
- Quick navigation to indices
- Data quality notes and interpretation caveats

### 2. Discovery via Indices (Three Views)

All indices cover the same 49 system prompts but sorted differently:

**a) By Tokens** (`indices/system-prompts-by-token.md`)
- Largest prompts first
- Useful for understanding prompt complexity and token budget
- Top: `Executes Given Bash Command` (3,488 tokens)

**b) By Init Version** (`indices/system-prompts-by-init.md`)
- Newest prompts first
- Useful for identifying recent additions
- Most prompts initiated in v2.1.118

**c) By Last Edit** (`indices/system-prompts-by-last-edit.md`)
- Most recently modified first
- Useful for tracking active development areas

### 3. Per-File Deep Dives

Each prompt file in `system-prompts/` contains:
1. Metadata header (source, summary)
2. Placeholder hints table (expression references with hints)
3. Raw prompt text (exact extracted content)

### 4. Aggregated Views

**For high-level understanding**:
- `meta/metadata.md` — bundle stats and token distribution
- `meta/cli-surface.md` — all commands, options, env vars at a glance
- `meta/prompt-stats.md` — tabular view of all prompts with metrics

**For feature changes**:
- `meta/flags.md` — feature flag inventory with confidence and notes

### 5. Version Comparison (Git Tags)

Tags follow semantic versioning: `v0.2.100` → `v2.1.167` (current).

Usage via GitHub compare view:
```
https://github.com/marckrenn/claude-code-changelog/compare/v2.1.44...v2.1.45#files_bucket
```

Provides file-level diffs showing what changed between releases.

---

## Core Abstractions & Relationships

### 1. Release Snapshot

A release snapshot is a complete extraction of prompts, flags, and CLI surface at a specific version.

**Relationships**:
- 1 Release = N System Prompts + N Feature Flags + CLI Surface
- Each prompt file has a lifecycle: `init` version → `last_edit` version
- Flags are classified by type (gate vs. config) and category

### 2. Prompt Artifact

A minimal unit representing a single prompt definition.

**Attributes**:
- Kind: tool, system, agent, skill, system-reminder
- Source: native-reference-match or native-prompt-markdown-tool
- Summary: One-sentence description
- Tokens: Estimated token count
- Init/Last Edit: Versions when created and last modified

### 3. Feature Flag

Extracted feature gate or config option.

**Attributes**:
- Type: gate (conditional) or config (parametric)
- Category: ui, tools, auth, safety, etc.
- Confidence: high, medium, low
- Notes: Observable behavior and constraints

### 4. CLI Entry

Command, option, environment variable, tool, skill, or model identifier.

**Relationships**:
- Commands reference options and tools
- Tools are invocable within the CLI
- Skills extend tool functionality
- Environment variables configure runtime behavior

---

## Dependencies & External References

### Direct Dependencies

**Source**: `@anthropic-ai/claude-code` npm package
- Package URL: https://code.claude.com/docs/en/overview
- README: https://code.claude.com/docs/en/overview
- npm: https://www.npmjs.com/package/@anthropic-ai/claude-code

### Inspiration & Related Work

- **Piebald-AI/claude-code-system-prompts**: Original full-prompt tracking inspiration
- **badlogic/cchistory**: Prompt extraction foundation
- **Mario Zechner**: Technical deep-dive on how cchistory works
- **Claude Code Documentation**: Official reference

### Data Flow (Extraction Pipeline)

```
@anthropic-ai/claude-code binary
    ↓
[Extraction tool - cchistory-based]
    ↓
Raw prompt artifacts (49 files)
    ↓
[Organization & Indexing]
    ↓
system-prompts/ (tagged by version)
    ↓
[Aggregation]
    ↓
meta/ indices/ (generated analytics)
    ↓
GitHub releases & tagged commits
```

---

## How the Project is Built & Maintained

### 1. Release Detection & Extraction

**Trigger**: New @anthropic-ai/claude-code release on npm

**Process**:
1. Extract prompts from binary using cchistory-based tool
2. Parse feature flags from config structures
3. Extract CLI surface (commands, options, env vars)
4. Generate metadata (token counts, statistics)

### 2. Git Workflow

**Commits**: One commit per significant change (per-prompt edits, flag updates)

**Tags**: Semantic versioning matching Claude Code versions (v2.1.167, etc.)

**Structure**:
- Each commit message indicates what changed: "v2.1.167 - init", "v2.1.167 - edit"
- Commits are atomic (one prompt file or one metadata file per commit)

### 3. Documentation Generation

**Index generation**: Sorted views of system-prompts generated from prompt-stats.md metadata

**Statistics aggregation**: Token counts, character counts, and lifecycle data per prompt

**Metadata consolidation**: CLI surface, flags, and metadata compiled into structured markdown

### 4. GitHub Actions & Automation

Implied by the project structure:
- Automated release detection
- Prompt extraction pipeline triggered on new releases
- Index and metadata regeneration
- Social media amplification via @ClaudeCodeLog X account

---

## Key Design Decisions

### 1. Markdown-Only Archive
**Decision**: Store all data in markdown files, not databases or structured data.  
**Rationale**: Version control-friendly, git-diff readable, GitHub-native discovery, human-readable, no dependencies.

### 2. Multiple Index Views
**Decision**: Same 49 prompts indexed three ways (by token, by init, by last edit).  
**Rationale**: Different use cases require different sort orders. Avoids forcing one organizational hierarchy.

### 3. Separated Raw & Metadata
**Decision**: `system-prompts/` contains extracted artifacts; `meta/` contains derived analytics.  
**Rationale**: Raw prompts change on every release; metadata is regenerated; separation enables clean diffs and version tracking.

### 4. Per-File Prompts
**Decision**: Each prompt stored as a separate .md file rather than consolidated.  
**Rationale**: Granular git history, easier to track lifecycle of individual prompts, enables compare views between versions.

### 5. Confidence Scoring on Flags
**Decision**: Feature flags include confidence levels (high, medium, low).  
**Rationale**: Extraction is heuristic-based; confidence indicates reliability of the interpretation, prevents false claims.

### 6. Legacy Compatibility Files
**Decision**: Root `cc-prompt.md` and `cc-flags.md` files per version tag.  
**Rationale**: Early tracking format; maintained for backward compatibility and ease of comparing full versions.

### 7. No Custom Build System
**Decision**: No build scripts, Makefile, or CI pipeline visible in repo.  
**Rationale**: Archive is pure data; generation likely happens in parallel tooling (@ClaudeCodeLog bot), not in this repo.

---

## Data Quality & Interpretation Notes

From README.md:

- **Token counts**: Estimated; vary by tokenizer/model/runtime
- **Per-file token counts**: Useful directional signals, not precise
- **LOC estimates**: Derived from prettified bundle; approximation only
- **File renames**: Happen across versions; content lineage may continue under different names
- **Duplicates**: Some prompts may have near-duplicates or intentional variants
- **Conceptual duplication**: One conceptual prompt can appear in multiple files
- **Statistical deltas**: Compare with raw diffs before drawing strong conclusions

---

## Current Version Snapshot (v2.1.167)

**As of**: 2026-06-06 01:40:53 UTC

**Prompt Counts**:
- Total: 49 files
- Tool descriptions: 44
- System prompts: 2
- Agent prompts: 1
- Skills: 1
- System reminders: 1

**Token Budget**:
- Total: 72,653 tokens
- Tool-heavy (90.3%)
- System reminders grow with feature expansion (5.8%)

**CLI Surface**:
- 41 commands
- 94 options
- 620 environment variables
- 10 built-in tools
- 10 user-available skills
- 106 models
- 8 providers

**Feature Flags**:
- ~22 identified flags
- Types: `config` (parametric), `gate` (conditional)
- Categories: UI, tools, auth, safety, networking, filesystem
- Confidence levels help identify extraction certainty

---

## Related Public Artifacts

**Social Media**: @ClaudeCodeLog (X/Twitter)
- Automated release detection
- Threaded diff summaries with screenshots
- Community engagement

**GitHub Releases**: Tagged with full-text release notes

**Status Page**: https://status.marckrenn.dev/status/claudecodechangelog

---

## Future Evolution Patterns

Based on current structure, likely future directions:

1. **Version expansion**: More releases tagged and archived
2. **Prompt evolution tracking**: Timeline of specific prompts (e.g., how bash tool description changed)
3. **Flag lifecycle analytics**: When flags introduced, disabled, superseded
4. **CLI surface trends**: Tracking command/option churn over time
5. **Token budget analysis**: How token allocation shifts between components
6. **Comparative diffs**: Highlighting what's different between any two versions

---

## How to Use This Archive

**For prompt research**: Navigate to `indices/system-prompts-by-token.md`, find the prompt, read the full definition in `system-prompts/`.

**For CLI changes**: Check `meta/cli-surface.md` for current surface; compare against previous versions using git tags.

**For feature flag analysis**: Review `meta/flags.md` for current gates and configs; trace changes across versions.

**For deep version comparison**: Use GitHub compare view between two tags to see exact diffs.

**For historical context**: Check prompt init/last-edit columns in `meta/prompt-stats.md` to understand stability.

---

## Summary

Claude Code Changelog is a **pure data archive** with a clear organizational philosophy: multiple entry points into the same data, organized for different discovery patterns. It has no executable components, no build system, and no application logic—only carefully extracted and indexed documentation that helps the community understand how Claude Code evolves.

The architecture prioritizes human readability, git-friendly storage, and analytical discovery over traditional software concerns like abstraction or modularity.
