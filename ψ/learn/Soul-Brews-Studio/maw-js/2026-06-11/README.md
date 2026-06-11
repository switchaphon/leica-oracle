# maw-js Learning — 2026-06-11

**Mode**: deep (5 agents) | **Focus**: Engine registry, team charters, Codex-specific patterns

## What It Is
Multi-Agent Workflow CLI (TypeScript/Bun). The orchestration engine that resolves engines, spawns teams, routes messages across federation.

## Key Findings Since Last Learn (2026-06-07)

### Engine Registry (`src/config/engine-registry.ts`)
- 5 built-in engines: claude, codex, thclaws, opencode, aider
- Resolution: `config.engines` > `config.commands` > DEFAULT_ENGINES > raw cmd
- `isClaudeLikeEngine()` gates capabilities (channels, resume, model, system-prompt-file)
- **Codex lacks all 4 capabilities** — gets bare command only

### Team Charter (`src/vendor/mpr-plugins/team/team-charter.ts`)
- Zero-dependency YAML parser with anchor support (`&anchor`, `*anchor`)
- Charter-local `engines:` block for per-team command overrides
- Member fields: role, engine, cwd, prompt, worktree, branch, queue, node, channels
- `defaults:` section for inheritable member defaults

### Recent Commits
- **#2707** (2026-06-11): `assertTeamEngineResolvable()` — fail-loud on bad engine
- **#2534** (2026-06-08): Charter-local YAML anchor engine aliases
- **#2671** (2026-06-10): Support `commands` without `default` key

### docs/codex-team-pattern.md (Official Reference)
Real-world charter example with mixed Claude+Codex teams, engine aliases, worktree isolation.

## Agent Files (not written — Explore agents are read-only)

| Topic | Agent | Key Finding |
|-------|-------|-------------|
| Architecture | maw-arch | Engine registry, team charter system, swarm vs team, recent #2707 |
| Code Snippets | maw-snippets | resolveEngine(), buildCommandFromConfig(), capability gates |
| Quick Reference | maw-ref | Engine config modern vs legacy, charter YAML, federation |
| Testing | maw-test | 206 test files, isolated mocking, fixture-based specs |
| API Surface | maw-api | EngineDef interface, 40+ HTTP endpoints, SDK plugin surface |
