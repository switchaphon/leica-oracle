# maw-rs Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/maw-rs
- **Self-description**: "Distributed terminal multiplexing & fleet management for AI
  agent oracles — **Rust port of maw-js**"

## Explorations

### 2026-07-26 2120 (default) — migration assessment vs maw-js
- [[2026-07-26/2120_ARCHITECTURE|Architecture]]
- [[2026-07-26/2120_CODE-SNIPPETS|Code Snippets]]
- [[2026-07-26/2120_QUICK-REFERENCE|Quick Reference]]

**Key insights**:
- **This is where the project actually lives now.** 551 commits in the last 30 days
  vs maw-js's 2. Releases ship daily (two on 2026-07-26 alone); PRs merge same-day.
- 13-crate Cargo workspace (`maw-cli`, `maw-tmux`, `maw-transport`, `maw-peer`,
  `maw-discord`, `maw-worktree`, `maw-schedule*`, `maw-auth`, `maw-xdg`,
  `maw-matcher`, `maw-plugin-manifest`). `unsafe_code = "forbid"` workspace-wide,
  clippy pedantic on.
- **203 native dispatcher entries** — commands register as `DispatcherEntry {command,
  handler}` consts (`DISPATCH_NN`) collected at build time.
- **Solves our send-keys pain point directly**:
  `action_resolution_parts/pending_input_detection.rs` +
  `submit_pending_state_after_grace()` detect text stranded in a pane buffer, verify it
  matches what was sent, and re-submit Enter with retries. This is the exact failure
  that drove the Discord workaround.
- **Our TS/Bun plugins have a supported path**: `runtime: "bun-dev"` in `plugin.json`
  runs the entry directly via Bun (dev tier — unsandboxed, prints a loud banner).
  `dispatcher.rs:848`, `plugin_manifest_opts_into_bun_dev()`. There is even a test
  fixture named `legacy-atlas` mirroring our own `atlas` plugin shape.
  The WASM ship tier is the *sandboxed* tier and needs a prebuilt sha256-verified
  artifact — it is not a requirement for running our plugins.
- Ships prebuilt `maw-rs-macos-arm64` + `.sha256` per release; installs as a drop-in
  symlink over `~/.bun/bin/maw`. Homebrew tap for stable: `soul-brews-studio/maw/maw`.
- Byte-level parity is tested against maw-js via committed fixtures
  (e.g. `tests/fixtures/hey-parity/maw-js-cli.json`).
- `docs/parity/parity-matrix.md` is the finish-line checklist — **but it is stale**
  (dated 2026-06-25, wave-3 refresh 07-15; 86 commits have landed since). Verify any
  `stub ⚠️` rating against source before trusting it: `wake` is rated stub yet is now
  3,147 LOC with full `--prompt`, and `maw-discord` is 3,144 LOC.

See the cross-repo decision doc: [[../../../memory/learnings/2026-07-26_maw-js-vs-maw-rs-migration|maw-js vs maw-rs migration assessment]]
