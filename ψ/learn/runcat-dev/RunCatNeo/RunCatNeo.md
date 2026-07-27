# RunCatNeo Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/runcat-dev/RunCatNeo

## Explorations

### 2026-07-27 1115 (default)
- [[2026-07-27/1115_ARCHITECTURE|Architecture]]
- [[2026-07-27/1115_CODE-SNIPPETS|Code Snippets]]
- [[2026-07-27/1115_QUICK-REFERENCE|Quick Reference]]

**Key insights**:
- RunCat Neo watches JSON files via macOS DispatchSource (no polling) — any tool that writes a JSON snapshot gets a live dashboard card for free.
- Custom Metrics uses security-scoped bookmarks so file access survives sandbox restarts.
- The Claude Code integration is just a statusLine command that writes `~/.claude/runcat-usage.json` — we merged it into our existing `statusline-command.sh` by piping stdin to the RunCat script in the background.
