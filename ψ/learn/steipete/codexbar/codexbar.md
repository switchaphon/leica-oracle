# codexbar Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/steipete/codexbar

## Explorations

### 2026-06-16 1340 (default)
- [Architecture](2026-06-16/1340_ARCHITECTURE.md)
- [Code Snippets](2026-06-16/1340_CODE-SNIPPETS.md)
- [Quick Reference](2026-06-16/1340_QUICK-REFERENCE.md)

**Key insights**:
- CodexBar supports 53+ AI providers (Codex, Claude, OpenAI, Cursor, Gemini, Copilot, etc.) vs CodexFleet which only does Codex accounts
- Privacy-first: reuses browser cookies/OAuth/CLI sessions, never stores passwords
- Multi-target: macOS app, CLI, WidgetKit, helper processes — same Core library
- Swift 6 strict concurrency throughout, pluggable provider architecture
- CodexFleet is a simplified fork focusing on Codex-only multi-account fleet monitoring with cat mascots
