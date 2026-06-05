---
pattern: Symlink shortcuts instead of directory migration
date: 2026-05-22
source: rrr — leica-oracle session
---

# Symlinks Beat Migration for Path Convenience

When the goal is just "shorter path to access", symlinks solve it with zero risk. Physical migration breaks:
- ghq repo management (expects `<root>/<host>/<owner>/<repo>` layout)
- Claude Code project memory (keyed by absolute path in `~/.claude/projects/`)
- maw fleet config (cached oracle paths)
- Any hardcoded paths in ψ/ docs, settings.local.json
- Running tmux sessions with cwd in old path

`~/_ORACLE_/` now has individual symlinks per oracle repo. One folder, all oracles, no migration.

Also: check for pre-existing directories before creating — Un had already created `~/_ORACLE_/` weeks earlier with a stale clone inside. Always verify before overwriting.
