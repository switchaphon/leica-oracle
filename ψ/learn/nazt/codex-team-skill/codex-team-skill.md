# codex-team-skill Learning Index

## Source
- **Origin**: https://gist.github.com/nazt/319bce17aa49ca6e9ac9529414e903ee
- **Author**: Nat (nazt)

## Explorations

### 2026-06-16 1238 (deep)
- [Architecture](2026-06-16/1238_ARCHITECTURE.md) — Claude lead + OMX builders pattern
- [Gap Analysis](2026-06-16/1238_GAP-ANALYSIS.md) — Our setup vs Nat's proven recipe
- [Quick Reference](2026-06-16/1238_QUICK-REFERENCE.md) — Commands + charter template
- [Skill Source](2026-06-16/1238_SKILL-SOURCE.md) — Original gist content
- [API Surface](2026-06-16/1238_API-SURFACE.md) — maw commands + integration points

**Key insights**:
1. Engine is `omx` not `codex` — affects maw routing
2. Branch isolation per member (own branch + worktree) prevents conflicts
3. Charter belongs in `ψ/teams/` (brain-committed) not `.maw/teams/`
4. `maw hey` for dispatch, never `tmux send-keys` or `SendMessage`
5. Full lifecycle: preflight → up → peek → hey → down (not just spawn)
6. Nat scales to 7 parallel codex members
