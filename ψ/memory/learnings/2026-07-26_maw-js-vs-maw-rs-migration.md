# maw-js vs maw-rs — migration assessment

**Date**: 2026-07-26 21:20 +07
**Asked by**: Un
**Question**: update to latest maw-js, or migrate to maw-rs?
**Verdict**: **Migrate to maw-rs, staged side-by-side. Do not spend effort updating maw-js.**

---

## What we run today

| | |
|---|---|
| Binary | `~/.bun/bin/maw` → `~/.bun/install/global/node_modules/maw-js/src/cli.ts` |
| Package | `"maw-js": "github:Soul-Brews-Studio/maw-js#3318389"` (bun global) |
| Version | `26.6.6-alpha.1652`, commit `3318389`, **2026-06-06** |
| Runtime | Bun, executes TypeScript directly |
| Plugins | 108 loaded (105 symlink, 3 legacy) — 24 core / 51 standard / 33 extra |
| Daemon | **None** — no `maw serve`, no pm2 process. CLI + tmux only |
| Live tmux | 6 sessions (`09-leica`, `04-pops-vet`, `05-rpro-ent`, …) |

Our six **custom** plugins (the migration-sensitive ones):

| Plugin | Source |
|---|---|
| `leica` | `leica-oracle/maw-plugin` (TS, `index.ts`, uses discord.js, has `voice-daemon.ts`) |
| `leica-nowcast` | `leica-oracle/.maw/plugins/leica-nowcast` |
| `leica-pulse` | `~/.maw/plugins/leica-pulse` |
| `atlas` | `~/.maw/plugins/atlas` |
| `discord-graph` | `~/.maw/plugins/discord-graph` |
| `blog` | `kru32-oracle/maw-plugins/blog` |

---

## Q1 — ours vs latest maw-js

We are **459 commits behind** maw-js `alpha` (our pin `3318389` is a clean ancestor, so a fast-forward is possible).

But look at *what* those 459 commits are:

| Type | Count |
|---|---|
| `bump` (dependency bumps) | 72 |
| `fix` | 34 |
| `test` / `fix(test)` | 29 |
| **`feat`** | **8** |
| `release` | 6 |
| other (align/wip/docs/perf) | ~15 |

**Updating maw-js buys 8 feature commits and 72 dependency bumps.** It is maintenance, not capability.

And maw-js itself has stopped moving:

- Last release **v26.6.14-alpha.2110 — 2026-06-13** (6 weeks ago)
- **2 commits in the last 30 days**
- **7 of the 8 most recent PRs are still OPEN**, including Windows fixes stalled since 18–22 July

## Q2 — maw-js vs maw-rs

maw-rs describes itself as *"Rust port of maw-js."* It is not a competitor — it is the successor line.

**maw-js says so itself.** From `maw-js/docs/maw-rs-port-status.md`:

> "maw-js has reached the practical coverage ceiling… Remaining work belongs in **maw-rs crate/CLI parity issues rather than maw-js coverage work**."
>
> "Pick one open maw-rs crate/CLI parity lane **rather than reopening maw-js coverage work**."
>
> "`maw-js` remains the coordination layer and source of truth **until `maw-rs` reaches CLI parity**."

maw-js's role has changed from *product* to *spec source* — it owns the portable
`test/spec/*.fixtures.json` that maw-rs implements against.

### Activity, side by side

| | maw-js | maw-rs |
|---|---|---|
| Commits, last 30 days | **2** | **551** |
| Last release | 2026-06-13 (6 wks) | **2026-07-26 — two today** |
| Last commit | 2026-07-24 | **2026-07-26 21:01** |
| Recent PRs | 7 of 8 **OPEN**, stalled | merging **same-day** |
| Codebase | Bun/TS, 89 vendored plugins | 13 Rust crates, **203 native commands** |
| Safety | — | `unsafe_code = "forbid"`, clippy pedantic |

---

## What migration actually costs us

### ✅ Verified working (checked in maw-rs source, not docs)

| Command | Status |
|---|---|
| `maw hey <target> <msg>` | native — and there is a **byte-level parity fixture against maw-js** (`tests/fixtures/hey-parity/maw-js-cli.json`) |
| `maw capture <target> [--pane N] [--lines N] [--full]` | native, `DISPATCH_77` (`capture.rs:2`) |
| `maw done <window> [--force] [--dry-run] [--clean-branch]` | native (`worktree_finish.rs:6`) |
| `maw wake` | native, **3,147 LOC**, full flags **including `--prompt`** |
| `ls` · `fleet` · `bud` · `awaken` · `swarm` · `sleep` · `kill` · `panes` · `oracle` · `peek` | native |

### ⚠️ Breaking — needs a CLAUDE.md edit

1. **`maw workon` has no `--prompt`.** maw-rs signature is
   `maw workon <repo|.|path|url> [task] [--wt [slug]] [--fresh] [--name <stable>] [-e <engine>] [--layout nested|legacy]`.
   Our documented workflow `maw workon <repo> <slug> --prompt "<brief>"` must become
   `maw wake <target> --task <slug> --prompt "<text>"` or `maw oracle-workon <repo> --task <slug> --prompt "<text>"` (both support `--prompt` natively).

2. **`maw team "<task>" --roles "chrome,flux,static"` does not exist.** `--roles` appears
   nowhere in maw-rs. `team` is subcommand-based (`up`, `spawn`, `enter`, `send`, …).
   Our `/team-agents` spawn pattern needs rewriting.

3. **`maw codex up/down/status/use`** — maw-rs natively provides only
   `maw codex accounts [--json] [--free] [--slots N]`. The `up/down/status/use` verbs come
   from the `maw-codex-team-kit` plugin and must be carried across.

4. **`maw discord`** is a partial port (REST subset). The crate is substantial —
   3,144 LOC with gateway/serve/access/tokens/bind — but treat full parity as unproven.

### ✅ Our custom plugins have a supported path

This was the thing I expected to block migration, and it does not.
maw-rs runs TypeScript/Bun plugins directly via **`"runtime": "bun-dev"`** in `plugin.json`
(`dispatcher.rs:848`, `plugin_manifest_opts_into_bun_dev()`). Dev tier = unsandboxed, prints a
loud banner. There is even a test fixture named **`legacy-atlas`** mirroring our own `atlas`
plugin's exact shape.

The WASM "ship tier" is the *sandboxed* tier requiring a prebuilt sha256-verified artifact —
it is **not** a prerequisite for running our six plugins.

### ❌ CORRECTION — the 12 NOT-PORTED items DO touch us

> **I got this wrong on the first pass and corrected it the same session.** My initial
> `ps aux | rg -i "maw|pm2"` returned empty and I concluded "no daemon running." That was
> false. `lsof` found it: **`maw serve` has been running since 10 July** (PID 1143,
> `bun ~/.bun/bin/maw serve`, port 3456). Lesson: an empty grep is not evidence of absence —
> confirm with a second method. See [[rtk_mangles_strings]].

What we actually run:

- **`maw serve` on :3456** — serving the **maw-ui "ARRA Office"** dashboard, whose bundle
  imports `useWebSocket`. `/api/health` reports *"maw server online (:3456, 6 sessions, probe ok)"*.
- **27 of our 108 plugins expose `api:` routes** — `/api/ls`, `/api/wake`, `/api/capture`,
  `/api/done`, `/api/oracle`, `/api/signals`, `/cross-team-queue`, …

The NOT-PORTED list is `serve-agents`, `serve-debug`, `serve-federation`, `serve-triggers`,
`serve-views`, `serve-worktrees`, **`serve-ws`**, plus the kanban and dispatch APIs the matrix
explicitly calls a *"cutover blocker for PM-style fleets."* We **are** a PM-style fleet running
the daemon.

maw-rs's `serve` is a far thinner surface:

```
usage: maw-rs serve [--host 0.0.0.0] [--port <port>] [--cached-pubkey <key>]
                  | maw-rs serve status|--status|stop
```

`maw help --all` shows **no websocket/`serve-ws` verb at all**.

**Revised risk**: the **CLI path is safe to migrate** — verified working against our live tmux
(`maw-rs ls` correctly reported all 6 sessions, right oracle names, right agent counts).
The **`maw serve` + web-UI path is not**. If the ARRA Office dashboard matters, that is a real
regression and the flip should wait.

Mitigating fact: both daemons are currently **idle — `lsof` shows LISTEN with zero ESTABLISHED
connections.** They are available-but-unused, so the practical cost may be nil. That is Un's
call, not mine.

### 🎁 It fixes our oldest pain point

Memory `tmux_comms_broken` records send-keys getting stuck in the buffer so oracles can't talk
without a human pressing Enter — the stated reason we built the Discord workaround.

maw-rs engineers against exactly this:
`action_resolution_parts/pending_input_detection.rs` plus
`submit_pending_state_after_grace()` in `pane_text_send_methods.rs` detect text stranded in a
pane, verify it matches what was sent (`pending_input_matches_sent`), and re-submit Enter with
retries (`enter_attempts`). There is a dedicated `send_text_pending_parts/pending_retry_tests.rs`.

### Install is low-risk

Prebuilt `maw-rs-macos-arm64` + `.sha256` ship on every release; we are arm64 macOS ✅.
Install is a symlink swap at the path we already use, so rollback is one command.
Homebrew tap exists for the stable channel: `brew install soul-brews-studio/maw/maw`.

---

## Caveat on the parity matrix

`docs/parity/parity-matrix.md` (135 rows: 81 native / 29 WASM / 13 stub / 12 not-ported) is the
project's own finish-line checklist — **but it is stale.** Dated 2026-06-25 with a wave-3
refresh 2026-07-15; **86 commits have landed since**. Two rows I checked were already wrong:
`wake` is rated `stub ⚠️` yet is 3,147 LOC with the full flag surface, and `discord` is far
larger than its row implies. **Verify any `stub ⚠️` rating against source before trusting it.**

---

## Recommendation

**Migrate to maw-rs. Staged, side-by-side, reversible.**

1. Install to `~/.local/bin/maw` — **do not** overwrite `~/.bun/bin/maw` yet. Both can coexist;
   PATH order decides which wins.
2. Smoke-test against a scratch tmux session: `hey`, `capture`, `ls`, `wake --prompt`, `done`.
3. Add `"runtime": "bun-dev"` to the six custom plugins' `plugin.json` and confirm each loads.
4. Rewrite the `workon --prompt` and `team --roles` patterns in `~/.claude/CLAUDE.md`.
5. Confirm the `maw-codex-team-kit` verbs still work.
6. Only then flip `~/.bun/bin/maw`. Old maw-js stays installed — **nothing is deleted**, rollback
   is one symlink.

**Do not invest in updating maw-js.** Its own maintainers have declared the line finished; the
459-commit gap is 72 dependency bumps and 8 features. If we want a stopgap before migrating,
fast-forwarding maw-js is safe (our pin is a clean ancestor) — but it is motion, not progress.

### Two genuine risks before flipping

1. **`maw serve` + maw-ui** — see the correction above. maw-rs's serve is a thin daemon; our
   27 plugin `api:` routes and the ARRA Office dashboard are not covered. Decide whether the
   UI matters before flipping.
2. **`maw discord` parity** — we run Discord bots. The crate is substantial (3,144 LOC) but
   the matrix rates it `stub ⚠️`. Test before the flip.

---

## Status as of 2026-07-26 22:0x

**Done — side-by-side install, nothing flipped:**

| | |
|---|---|
| maw-rs installed | `~/.local/bin/maw` → `v26.7.16-alpha.1159`, sha256 **verified** |
| maw-js | **untouched** — `~/.bun/bin/maw` still active on PATH (`v26.6.6-alpha.1652`) |
| Smoke test | `maw-rs whoami` + `ls` read our live tmux correctly — 6 sessions, right oracle names and agent counts |

Note: the downloaded binary is `v26.7.16-alpha.1159` — GitHub's "latest release" marker, and
the only one **not** flagged prerelease. Newer tags exist (`v26.7.26-alpha.1519`) but are all
marked Pre-release. Pull one explicitly if bleeding-edge is wanted.

**Rollback**: `rm ~/.local/bin/maw` — that is the whole procedure. maw-js was never modified.

---

## MIGRATED — 2026-07-27

Un confirmed he does not use the ARRA Office dashboard, so the `maw serve` gap was not a
blocker. Discord bots were cleared for restart. **The flip is done.**

```
~/.bun/bin/maw → ~/.local/bin/maw   (maw-rs v26.7.16-alpha.1159)
```

### Discord parity: PASS — maw-rs is *ahead*, not behind

The matrix's `stub ⚠️` rating is simply wrong now. Same-command output was byte-identical for
`discord status`, `tokens ls`, and `access list`. And on `discord version`:

| subcommand | maw-js | maw-rs |
|---|---|---|
| `pair <oracle> <chan>` | ⏸ v0.5 **planned** | ✓ v0.5 **implemented** |
| `route <from> <to>` | ⏸ v0.5 **planned** | ✓ v0.5 **implemented** |
| `serve` (after_send hook) | ⏸ v0.5 **planned** | ✓ v0.5 **implemented** |

Also worth recording: **the Discord bot is not a maw daemon at all.** `09-leica:leica-discord`
is a separate Claude Code session using the `plugin:discord:discord` MCP plugin. `maw discord`
is fleet *ops* tooling, not what keeps the bot alive — so bot uptime never depended on this.

### The real blocker was the plugins — found and fixed

maw-rs's bun-dev tier runs `bun <entry> <args>` as a **subprocess**
(`dispatcher.rs`, `dispatch_bun_dev_plugin`). maw-js instead **imports the module and calls
`handler(ctx)`** through its plugin SDK. Our plugins only did `export default handler` with no
`import.meta.main` guard — so under maw-rs bun loaded the module, called nothing, and
**exited 0 with no output.** A silent no-op: the worst failure mode, because it looks like success.

`blog` was the exception — it already had the guard, with a Thai comment describing this exact
bun-dev behaviour. So the fix was already proven inside the family; it just had not been
propagated.

Appended to all five (`leica`, `leica-nowcast`, `leica-pulse`, `atlas`, `discord-graph`):

```ts
if (import.meta.main) {
  const result = await handler({ source: "cli", args: process.argv.slice(2) });
  if (result.output) console.log(result.output);
  if (result.error) console.error(result.error);
  process.exit(result.exitCode ?? (result.ok ? 0 : 1));
}
```

Note it prints `result.output` — blog's shorter shim only calls `process.exit`, which works
solely because blog's handler `console.log`s internally. Ours accumulate into `out[]` and return
the text, so it must be printed explicitly. **Backward-compatible**: `import.meta.main` is false
when maw-js imports the module, and both CLIs were verified producing identical output.
Backups at `index.ts.bak-2026-07-26` beside each.

### Post-flip verification — all green

| | |
|---|---|
| Custom plugins | `leica family` 12 · `nowcast` 5 · `leica-pulse` 10 · `atlas` 31 · `discord-graph` 12 · `blog` 40 lines |
| Core | `ls` (6 sessions, correct names/agents) · `whoami` · `panes` · `capture` · `discord version` |
| `maw hey` | delivered **and submitted** — the scratch shell executed the injected text, proving Enter went through rather than sticking in the buffer |

### Rollback (maw-js untouched, never uninstalled)

```bash
ln -sf ../install/global/node_modules/maw-js/src/cli.ts ~/.bun/bin/maw
```
Original target also saved at `~/.maw-js-symlink-target.bak-2026-07-26`. The plugin shims can
stay — they are inert under maw-js.
