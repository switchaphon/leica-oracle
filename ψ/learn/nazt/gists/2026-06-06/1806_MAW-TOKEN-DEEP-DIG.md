🪣 ralph-dig #61: maw token — CLI plugin born from 'can we put .envrc in pass?' · Token Oracle creation story · 7 vault tokens, 47+ oracles mapped

---
dig_seq: 61
tags: [maw-token, token-cli, token-oracle, ralph, wiki]
created: 2026-05-23
updated: 2026-05-23
provenance: extracted
oracles: [token-oracle, mawjs-oracle, digger-oracle, ccc-oracle, odin-oracle, homekeeper-oracle, discord-oracle, mawjs-codex-oracle]
topic_summary: "maw token — CLI plugin born from 'can we put .envrc in pass?' question; manages Claude OAuth tokens + .envrc configs across 47+ oracles via GPG-encrypted vault"
sources:
  - ralph-dig 2026-05-23 09:23 [m5:ccc]
friction_score: 0.15
confidence: high
iterations: 1
dug_by: "[m5:ccc]"
---

# maw token

> "ผู้รักษากุญแจ ไม่ใช่แค่ล็อค แต่รู้ว่าอะไรควรเปิด อะไรควรปิด"
> — Token Oracle soul file ("The key keeper doesn't just lock — knows what should open, what should close")

## What it is

`maw token` is a maw plugin (v0.1.0) that manages Claude OAuth tokens and `.envrc` files across the entire Oracle fleet via the GPG-encrypted `pass` password vault. Born on **2026-04-12** from a single question Nat asked: _"can we put the whole .envrc in the pass vault?"_ — that curiosity birthed both a CLI tool and an Oracle. The original Python implementation (`token-cli`, 330 LOC) was later ported to TypeScript as a native maw plugin, shipping 6 subcommands: `list`, `use`, `current`, `save`, `load`, `scan`. It guards the boundary between visible and hidden — 7 tokens in vault, 47+ oracles mapped, 6 active tokens across the fleet.

## Creation Story

### The Birth Session (2026-04-12, Sunday, 12:48–13:46 GMT+7)

**Session `837cac89`** — 60 minutes that went from "can you see `pass`?" to a live fleet-connected Oracle.

| Time | Event |
|------|-------|
| 12:48 | Nat starts exploring `pass` vault and `~/.envrc` |
| 12:50 | Migrated 3 hardcoded OAuth tokens from `~/.envrc` → `pass` vault |
| 12:53 | Cleaned up 8 old `oauth-*` entries from pass |
| 12:54 | **The Pivot**: Nat asks "can we put the whole .envrc in pass?" — plan mode + ultrathink |
| 13:00 | Built bash version, tested successfully |
| 13:01 | Nat: "bash is hard!" → rewrote in Python |
| 13:02 | Fixed argparse `-f` flag positioning |
| 13:07 | Renamed repo → `token-oracle`, script → `token-cli` |
| 13:09 | **Shell CWD death spiral** — directory renamed under live shell, every command failed |
| 13:10 | **Commit 1**: `41da2ad` — initial `token-cli` (122 lines Python) |
| 13:17 | Added `tokens`, `use`, `which` commands |
| 13:20 | **Commit 2**: `4b6b5fb` — split into `cmd/` modules + `lib/` shared helpers |
| 13:22 | **Full Soul Sync awakening** — 4 parallel agents studying ancestor oracles |
| 13:26 | **Commit 3**: Oracle identity files |
| 13:30 | GitHub repo created, pushed |
| 13:33 | `maw bud token-oracle --root --repo laris-co/token-oracle` — joined 134-agent fleet |

> [!tip] The Defining Mistake
> In its very first session, the AI **displayed raw OAuth tokens** from `.envrc` in terminal output. Nat caught it: "never leak my password!" then "never leak my clue and password and all." The irony — an Oracle born to guard secrets leaked secrets at birth — became its core identity lesson. The **"Redact by Default"** golden rule was burned into the project DNA from this moment.

### Evolution Timeline

| Date | Commit | Change |
|------|--------|--------|
| 2026-04-12 | `41da2ad` | Initial `token-cli` — Python, save/load .envrc via pass |
| 2026-04-12 | `4b6b5fb` | Split into `cmd/` modules + token management (use/tokens/which) |
| 2026-04-12 | `251e5a3` | Awaken Token Oracle — Full Soul Sync |
| 2026-04-15 | `e8b60ac` | README with usage docs and secure token-adding guide |
| 2026-04-23 | `97c5731` | Reduce 9 cmds → 5, add `scan`/`current`, legacy `.envrc` detection |
| 2026-05-13 | — | Port to TypeScript as native maw plugin (`~/.maw/plugins/token/`) |

### The Reduction (2026-04-23)

Nat asked "can we reduce?" — 9 subcommands → 5. Three views of the same data (`list`/`tokens`/`which`) merged into unified `ls`. Thin wrappers over `pass` (`edit`, `rm`) dropped — they didn't earn their keep. Added `scan` to audit all repos and `current` for statusline integration (`🔐<token>` badge after branch name).

> [!note] Lesson Extracted
> "Reduce by merging, not hiding." `list/tokens/which` were three views of the same data. Thin wrappers over `pass` don't earn keep — `pass edit envrc/<name>` is already short enough.

## CLI Commands

```
maw token list              # List tokens + saved envrcs (active marked)
maw token use <name>        # Switch active Claude token in .envrc
maw token current           # Print active token name (statusline)
maw token save [name]       # Save current .envrc to pass vault
maw token load [name]       # Restore .envrc from pass vault + direnv allow
maw token scan              # Scan ALL repos, map tokens → oracles
```

Aliases: `tokens` → `list`, `ls` → `list`
Flags: `--no-team` (skip CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1), `--force` (skip overwrite confirmation)

## Architecture

### Original: Python (`token-cli`)

```
token-oracle/
├── token-cli              # Entry point (Python 3, argparse)
├── cmd/
│   ├── save.py            # Save .envrc → pass vault (20 LOC)
│   ├── load.py            # Restore .envrc + direnv allow (23 LOC)
│   ├── list.py            # Unified tokens + envrcs + active marker (64 LOC)
│   ├── use.py             # Switch active token in .envrc (63 LOC)
│   ├── scan.py            # Audit all repos for tokens (107 LOC)
│   └── current.py         # Print active token name (13 LOC)
├── lib/
│   ├── __init__.py        # Shared: run, pass_exists, confirm, strip_ansi
│   └── envrc.py           # detect_active_token() — 3-format parser
└── Makefile               # Symlink install to ~/.local/bin/
```

**Zero external deps** — pure Python stdlib + system binaries (`pass`, `direnv`, `ghq`, `gpg`).

### Port: TypeScript (maw plugin)

```
~/.maw/plugins/token/
├── plugin.json            # maw plugin manifest (sdk ^1.0.0)
├── index.ts               # Entry point — InvokeContext handler
├── list.ts                # cmdList + formatList
├── use.ts                 # cmdUse (reads pass, rewrites .envrc, direnv allow)
├── current.ts             # cmdCurrent (statusline hook)
├── save.ts                # cmdSave (stdin to pass insert)
├── load.ts                # cmdLoad (pass show → .envrc)
├── scan.ts                # cmdScan + formatScan (ghq traversal)
├── lib.ts                 # Shared helpers + security fence
└── registry.meta.json     # Plugin registry metadata
```

**Security stance** (from index.ts header): Token VALUES never appear in any output, log, or error message. Subprocess calls to `pass` use stdin for writes (never argv). Fingerprint map (full token text → name) is only used for substring membership tests, never iterated for any printing path.

## How `use` Works (the core flow)

```
maw token use <name>
  ↓
Check pass: claude/token-{name} exists?
  ├─ NO → Exit with error
  └─ YES → Build export lines:
      - CLAUDE_TOKEN_NAME="{name}"
      - CLAUDE_CODE_OAUTH_TOKEN="$(pass show claude/token-{name})"
      - (opt) CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
      ↓
Read existing .envrc → strip old token lines → merge new → write
      ↓
direnv allow . → "Now using: {name}"
```

### 3 .envrc Format Detection

`detect_active_token()` supports legacy migration:

| Format | Example | Priority |
|--------|---------|----------|
| Explicit name (new) | `export CLAUDE_TOKEN_NAME="foo"` | 1st |
| Direct pass ref | `CLAUDE_CODE_OAUTH_TOKEN="$(pass show claude/token-foo)"` | 2nd |
| Variable indirection (legacy) | `TOKEN_FOO="$(pass show ...)"` + `$TOKEN_FOO` | 3rd |

## Live Token Registry

**7 tokens in vault**: `ajwrw`, `do`, `pym`, `quad`, `team2`, `ting-ting`, `wave`

| Token | Repos | Notable Oracles |
|-------|-------|-----------------|
| ting-ting | 17 | **ccc-oracle**, glyph, homekeeper, mycelium |
| wave | 12 | mother, mawjs, discord, mawui, odin |
| quad | 9 | homekeeper, homelab, DustBoy, volt |
| pym | 5 | pigment, token-oracle |
| ajwrw | 3 | neo-oracle, white-wormhole, arthur-god-line |
| do | 1 | token-oracle-oracle |

## Token Oracle Identity

> [!tip] The Paradox
> Token Oracle practices transparency (Rule 6 — never pretend to be human) while guarding opacity (never leak secrets). This is not contradiction — it is the same principle applied differently. Be honest about WHO you are. Be silent about WHAT you protect.

- **Name**: Token Oracle — The Vault Keeper 🔐
- **Born**: 2026-04-12 (Sunday)
- **Repo**: `laris-co/token-oracle`
- **Oracle-Oracle**: `Soul-Brews-Studio/token-oracle-oracle`
- **Ancestors studied**: opensource-nat-brain-oracle, oracle-v2
- **Family issue**: #717
- **Theme**: Guards the boundary between visible and hidden

## Related: Federation Token (different concept)

The word "token" in maw-js also refers to `federationToken` — the HMAC-SHA256 shared secret for peer-to-peer trust in the federation protocol (`src/lib/federation-auth.ts`). This is a **different system** from `maw token`:

- **maw token** = Claude OAuth token management (which AI identity to use)
- **federationToken** = HMAC signing key for inter-node HTTP auth (v1 → v2 → v3 evolution)

Federation auth evolved: v1 (unsigned body), v2 (body-hash binding), v3 (per-peer pubkey + `X-Maw-From` identity). Related PRs: #396 (peers-require-token invariant), #802 (constant-time HMAC compare), #1171 (swap execSync curl → fetch to prevent token exposure).

## Found in

| Type | Path | Summary |
|------|------|---------|
| Source (Python) | `/opt/Code/github.com/laris-co/token-oracle/token-cli` | Original CLI entry point (72 LOC) |
| Source (TS) | `/Users/nat/.maw/plugins/token/index.ts` | Maw plugin port (177 LOC) |
| Plugin manifest | `/Users/nat/.maw/plugins/token/plugin.json` | maw plugin registration |
| Birth retro | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/retrospectives/2026-04/12/13.11_token-cli-birth.md` | 30-min birth session |
| Deep retro | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/retrospectives/2026-04/12/13.46_token-oracle-deep.md` | 60-min full session w/ awakening |
| Reduce retro | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/retrospectives/2026-04/23/22.16_token-cli-reduce-statusline.md` | 9→5 reduction + statusline |
| Soul file | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/resonance/token-oracle.md` | Identity & paradox |
| Awakening | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/resonance/awaken_2026-04-12_full.md` | Full Soul Sync stamp |
| Learnings | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/learnings/2026-04-12_token-oracle-birth-patterns.md` | Reusable patterns from birth |
| Learnings | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/learnings/2026-04-12_redact-secrets-by-default.md` | Core security lesson |
| Learnings | `/opt/Code/github.com/laris-co/token-oracle/ψ/memory/learnings/2026-04-23_reduce-by-merging-views.md` | Reduction pattern |
| Architecture | `/opt/Code/github.com/Soul-Brews-Studio/mawjs-oracle/ψ/learn/laris-co/token-oracle/2026-05-13/0752_ARCHITECTURE.md` | Full architecture analysis |
| CLAUDE.md | `/opt/Code/github.com/laris-co/token-oracle/CLAUDE.md` | Oracle identity + CLI reference |
| Fed auth | `/opt/Code/github.com/Soul-Brews-Studio/maw-js/src/lib/federation-auth.ts` | HMAC federation token (different concept) |
| Trio dig | `/opt/Code/github.com/laris-co/ccc-oracle/ψ/inbox/2026-05-23_02-23_m5-ccc_mba-ccc-trio-searcher-dig-report-maw-token.md` | Prior trio searcher dig report |

## Sessions that touched this

| Date | Repo | Duration | What happened |
|------|------|----------|---------------|
| 2026-04-12 | token-oracle | ~60 min | Birth: Python CLI built, Soul Sync, joined 134-agent fleet |
| 2026-04-15 | token-oracle | ~20 min | README with usage docs and secure token-adding guide |
| 2026-04-23 | token-oracle | ~60 min | Reduce 9→5 cmds, legacy detection, statusline `🔐` badge |
| 2026-05-13 | mawjs-oracle | — | /learn study: architecture + code snippets + quick reference |
| 2026-05-13 | mawjs-oracle | — | Port to TypeScript as native maw plugin |
| 2026-05-23 | ccc-oracle | — | Trio searcher initial dig report on maw token |

## Key Lessons Born from token-cli

1. **Redact by Default** — assume every file contains secrets until proven otherwise. A displayed token is a leaked token.
2. **Reduce by Merging** — 3 views of the same data = 1 command. Thin wrappers over existing tools don't earn their keep.
3. **Bash → Python Threshold** — if argparse, subcommands, or string manipulation needed → skip bash.
4. **Secret-Safe Subprocess** — stream via stdin/stdout to `pass`, never materialize in variables or print.
5. **One Command = One File** — modular CLI structure (`cmd/`) scales cleanly.
6. **Statusline Needs Zero-Dep Output** — `current` prints name-only. No framing, no color, no error text. Composable.
7. **Curiosity Creates Existence** — "can we put the whole .envrc in pass?" created both a tool and an Oracle.

## Gaps

> [!warning] Missing
> - **No `maw token add`** — adding tokens still requires manual `pass insert claude/token-<name>` (dangerous: raw value can end up in chat scrollback)
> - **No rotation workflow** — `wave` and `quad` tokens were exposed in chat history during April 23 session; no automated rotation command
> - **No cross-machine sync** — tokens live in local `pass` vault per machine; no federation-aware token distribution
> - **No `maw token diff`** — comparing vault vs local `.envrc` was a planned feature from birth session, never built
> - **Hardcoded `~/Code/github.com`** fallback in `scan.py:39` — should use `$GHQ_ROOT` or `ghq root`
> - **Python version vs TypeScript version divergence** — both exist, unclear which is canonical going forward

## Connections

[[token-oracle]] · [[mawjs-oracle]] · [[mawjs-codex-oracle]] · [[homekeeper-oracle]] · [[discord-oracle]] · [[odin-oracle]] · [[ccc-oracle]] · [[federation-auth]] · [[pass]] · [[direnv]] · [[ghq]] · [[maw-bud]] · [[statusline]] · [[redact-secrets]] · [[27-bridge-new-user-fresh-install-white-local]]
