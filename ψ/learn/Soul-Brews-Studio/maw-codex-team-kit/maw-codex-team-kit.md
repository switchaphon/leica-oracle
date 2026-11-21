# maw-codex-team-kit Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/maw-codex-team-kit
- **State when read**: HEAD `397db8b`, 8 commits, all dated 2026-07-06, 18 tracked files, no tests, no activity since.

## Explorations

### 2026-11-02 1551 (default, 3 agents)
- [[2026-11-02/1551_ARCHITECTURE|Architecture]]
- [[2026-11-02/1551_CODE-SNIPPETS|Code Snippets]]
- [[2026-11-02/1551_QUICK-REFERENCE|Quick Reference]]

Method: three Haiku agents read the source read-only. The lead re-checked the headline claims against the cited lines
(engine string, trust seeding, `down` ignoring results, the `worktree: .` path arithmetic, every try/catch site) and
read the maw-rs dispatcher. Nothing was installed, built or run.

**Key insights**:
1. **It cannot run on the maw-rs we have, and the reason is structural.** maw-rs has a native `codex` command (only
   `accounts`). Its dispatcher lets a plugin answer after a native miss only for `cross-team-queue` and `squad`
   (`crates/maw-cli/src/core_impl/dispatcher.rs`, `native_plugin_fallthrough_command`), so a plugin named `codex` is
   shadowed even when linked into `~/.maw/plugins`. maw-rs documents its own route in `docs/guides/codex-team-spawn.md`.
2. **It reports success without checking.** `up` prints "N coders up" whatever happened; `down` prints "cleared" even
   when kill, move or `branch -d` failed (`team.ts:125`, `:152`). The regex charter parser keeps `# comments` in values,
   so the kit's own template gives a wrong `session` and `down` kills nothing (`team.ts:64`, `templates/team.yaml:10`).
   A charter with `worktree: .` makes `down` rename the repo root to `/tmp` (`team.ts:76`, `:138-141`; read, not run).
3. **Fixed, unsandboxed launch.** Every coder starts as `direnv exec . omx --yolo --direct` (`team.ts:33`), `direnv allow`
   approves the whole `.envrc` including lines the repo supplied, and trust is seeded by appending to the account's
   `config.toml`. It never logs in, never reads `auth.json`, has no quota logic, and never sends the charter's `prompt:`.
4. **What was worth having:** one `CODEX_HOME` per account via `.envrc` (spreads rate limits across accounts), trust
   seeding so a TUI boots silently, and a teardown order that never deletes (kill, mv to `/tmp`, prune, `branch -d`).
   None of it is needed by `codex exec` on a single account.
5. **Provenance is thin:** one author, eight commits in under an hour, two self-reported field reports (at most 5 coders,
   no logs, no quota events). Treat "validated" in the README as a claim.
