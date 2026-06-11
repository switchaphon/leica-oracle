# arra-oracle-skills-cli Learning — 2026-06-11

**Mode**: deep (5 agents) | **Focus**: Codex integration + skill distribution

## What It Is
CLI tool that installs 35 Oracle skills to 19 AI agents (Claude Code, Codex, OpenCode, Cursor, Gemini, etc.). Single source of truth: `SKILL.md` → compiled to VFS for binary distribution.

## Key Findings for Codex Integration
- Codex gets skills via **plugin marketplace** (TOML v0.128, JSON v0.130+)
- Install: `npx arra-oracle-skills install -g -y --agent codex`
- Skills go to `~/.codex/skills/` + `~/.codex/prompts/`
- Version-aware: `codexUsesJsonFormat()` branches on Codex version

## Agent Files (not written — Explore agents are read-only)
Findings captured in agent task notifications, synthesized in parent `2026-06-11_CROSS-REPO-SYNTHESIS.md`.

| Topic | Agent | Key Finding |
|-------|-------|-------------|
| Architecture | arra-arch | 35 skills, 19 agents, VFS compilation, profile system |
| Code Snippets | arra-snippets | Codex marketplace TOML/JSON branching, fs-utils abstraction |
| Quick Reference | arra-ref | 4 profiles (minimal→lab), federated agent opt-in |
| Testing | arra-test | Bun test runner, 22 test files, no external mock libs |
| API Surface | arra-api | Plugin hooks, MCP integration, cross-agent installation |
