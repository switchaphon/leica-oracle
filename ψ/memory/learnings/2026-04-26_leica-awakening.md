# Lesson: /learn on large codebases — use Sonnet, not Haiku

**Date**: 2026-04-26
**Source**: rrr — root-oracle awakening session
**Tags**: learn, haiku, sonnet, context-limits, agent-setup

## Pattern

Haiku agents hit context limits (~25-30 tool uses) when exploring large Next.js or monorepo codebases. The symptom is "Prompt is too long" after the agent reads too many files.

## Fix

Use Sonnet (default model) for /learn on any repo with node_modules, coverage, .next, or playwright-report directories. Add explicit exclusion instructions to every agent prompt:

```
⚠️ SKIP: node_modules/, .next/, coverage/, playwright-report/, .git/, dist/
```

## Why it matters

/learn --deep spawns 5 agents. If 2 of them fail (architecture + API surface are the heaviest), the user gets 3/5 docs and needs a retry round. Sonnet avoids this entirely.

---

# Lesson: Agent team architecture before writing files

**Date**: 2026-04-26
**Source**: rrr — root-oracle awakening session
**Tags**: agents, architecture, planning, team-setup

## Pattern

When setting up a multi-agent team, writing files before confirming the full architecture leads to interruptions and rewrites. The user corrected agent design 3 times (names → tool scoping → pawrent education).

## Fix

Before writing any agent file:
1. Sketch the full hierarchy (who reports to whom)
2. Map tools/skills/plugins per agent role
3. Confirm with user
4. Write all files at once

## Why it matters

Each interruption costs a write rejection + clarification exchange. With 8+ agent files, getting the architecture wrong upfront multiplies the rework.

---

# Lesson: maw node name = Oracle name

**Date**: 2026-04-26
**Source**: rrr — root-oracle awakening session
**Tags**: maw, identity, configuration

## Pattern

Setting the maw node name to match the Oracle name creates coherent identity across all interfaces: `maw ls` shows "leica", `maw hey leica` routes correctly, the agent persona is "Leica".

## Fix

In `~/.config/maw/maw.config.json`:
```json
{ "node": "leica" }
```

Set this during Oracle awakening, not after.
