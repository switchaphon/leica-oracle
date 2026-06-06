# hermes-agent Learning Index

## Source
- **Origin**: [./origin/](./origin/) — symlink to ghq
- **GitHub**: https://github.com/NousResearch/hermes-agent
- **Submodule**: `tinker-atropos` — RL training integration

## Explorations

### 2026-04-20 1946 (default · 3 agents)
- [Architecture](./2026-04-20/1946_ARCHITECTURE.md) — structure, entry points, core abstractions, design decisions
- [Code Snippets](./2026-04-20/1946_CODE-SNIPPETS.md) — 10 illustrative snippets (agent loop, tools, prompts, providers)
- [Quick Reference](./2026-04-20/1946_QUICK-REFERENCE.md) — install, quickstart, config, gotchas

**Key insights**:
- Hermes is a self-improving agent with closed learning loops — Atropos RL feeds back into the agent via `tinker-atropos` submodule.
- Provider-agnostic core: single abstraction over Anthropic / Bedrock / Gemini / OpenAI-compatible (~7+ providers).
- Security-first prompt assembly scans context for injection patterns before handing off to the LLM.
- Extensibility via **Skills-as-Markdown** (procedural memory), pluggable Tools registry, and MCP support.
- SQLite + FTS5 state store backs memory and context compression.

### 2026-04-20 2218 (deep · 3 agents — philosophy lens)
- [Issues & Commits](./2026-04-20/2218_ISSUES-COMMITS.md) — release rhythm, commit style, argued themes, stated vs revealed philosophy
- [Testing](./2026-04-20/2218_TESTING.md) — tests/ structure, coverage gaps, what they trust LLM to do vs what they assert
- [API Surface](./2026-04-20/2218_API-SURFACE.md) — CLI / MCP / ACP / gateway / plugin / tool / skill / webhook / cron / Python-embed

**Key insights from the deep run**:
- **Release rhythm**: every ~4 days. Changelogs cite PRs, not marketing copy.
- **Commit discipline**: strict conventional commits (`type(scope): what`), atomic, no narrative — *code is the spec; discussions live in PRs*.
- **What they argue about**: provider compatibility (8+ bugs), gateway reliability (6), skill autonomy (5), config/onboarding (4), session search (3).
- **Tests are prescriptive, not proscriptive** — they assert the harness works, they trust the LLM to use it correctly. Skills auto-creation loop and cross-platform routing have thin coverage; `tinker-atropos` has **zero test files**.
- **Python embedding is unsupported** — hermes is a daemon/CLI, not a library. Use ACP or subprocess.
- **The one claim only hermes makes**: "The only agent with a closed learning loop that works across all platforms and all models simultaneously, without lock-in."
