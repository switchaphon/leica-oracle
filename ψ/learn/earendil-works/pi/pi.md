# pi Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/earendil-works/pi

## Explorations

### 2026-06-17 0519 (fast)
- [Overview](2026-06-17/0519_OVERVIEW.md)

**Key insights**:
- Minimal agent harness — 4 packages: tui, ai, agent-core, coding-agent
- TUI uses differential rendering (no Ink/React) — first → full → incremental
- Theming via JSON files in `packages/coding-agent/src/modes/interactive/theme/`
- Fork by customizing theme JSON + assets + extensions in `.pi/extensions/`
- 20+ LLM providers supported via `pi-ai` package
