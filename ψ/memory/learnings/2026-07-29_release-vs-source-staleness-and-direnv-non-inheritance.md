---
id: learning_2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance
type: learning
title: "Verify binaries against releases, and know that direnv does not inherit (2026-07-29)"
concepts: [staleness, release-vs-source, direnv, envrc, credential-precedence, oauth-account, silent-fallback, verification-discipline, measurement, stale-memory, token-rotation]
tags: [maw, arra-oracle-v3, claude-code, multi-account, pass, keychain]
created: 2026-07-29
source: "rrr --deep: leica-oracle"
---

# Two root causes, one theme: the thing you are looking at is not the thing that runs

Three symptoms across two systems, all resolved on 2026-07-29. Every one of them came from
checking an artefact that *represents* the running system rather than the running system itself.

## 1. Verify a binary against its RELEASE, never its source tree — confidence: HIGH

`maw a leica` forcing a picker, and `maw wake` leaving its command un-executed in the shell
buffer, looked like two unrelated bugs. They were one 12-day-stale binary:

```
installed  v26.7.16-alpha.1159  (commit 80782dd, 2026-07-16)
released   v26.7.28-alpha.1027  (2026-07-28)
gap        99 commits
```

- `1d394e2` / #612 — auto-picks the single live Exact match when the rest are non-live
- `8f6133b` / #630 — polls pane readiness *before* send-keys; pre-fix maw fired keys while
  zsh + direnv were still initialising, so the Enter was swallowed

**The self-inflicted part.** My own memory said "pull + rebuild maw-rs". `~/.bun/bin/maw` →
`~/.local/bin/maw` is a **prebuilt binary fetched by `install.sh` from GitHub releases; cargo is
never invoked.** `git pull` on the source changed nothing while the source tree read as current.
Nat closed Un's own issue (#711) within 17 hours; Un kept hitting it for two more days because
the fix was never *installed*. **Wrong memory is worse than no memory — it stops you looking.**

**Do this instead:**
```bash
<tool> --version                                  # what actually runs
gh release list --repo <org>/<repo> --limit 1     # what is available
git merge-base --is-ancestor <fix-sha> <tag>      # is the fix really in that build?
```
Corollary: **two unrelated-looking symptoms with no shared code path is evidence *for* a version
problem, not against one.**

Also: `maw fleet doctor` / `maw fleet gc` report "no findings" while oracles are hard-broken —
not a health check. Sweep with the real operation: `maw wake <o> --dry-run | grep ambiguous`.
`maw a <n> --print` and `maw wake <n> --dry-run` resolve without touching tmux, so they are safe
from inside a live session.

## 2. `ps` decides what runs; config only states intent — confidence: HIGH

Two near-identical ghq clones existed: `arra-oracle-v3` and `arra-oracle-v3-alpha`. The live MCP
ran from **`-alpha`**. I audited the other one for an entire investigation.

`~/.claude.json` contains **more than one entry named `arra-oracle-v3`, and they disagree** — one
is `bunx --bun arra-oracle-v3@github:...`, the project-scoped one runs the local `-alpha` path.
Reading the wrong block produced the confident conclusion "the MCP does not run from ghq at all,"
and I was one step from *correcting a memory that was right*.

It survived only because `diff -q` showed the file under investigation was byte-identical in both
clones. That is luck, not method.

**Rules:** settle "which copy runs" with `ps ax | grep` before analysing anything. Grep the whole
config for duplicate entries of the same name. Rename unused sibling clones with a leading `_`
(done: `_arra-oracle-v3`) so the next investigation cannot pick wrong.

## 3. direnv loads only the NEAREST `.envrc` and does not merge with parents — confidence: HIGH

This was the two-day multi-account bug, and it is the most reusable fact of the day.

Precedence: `oauthAccount` (in `~/.claude.json`) **>** `CLAUDE_CODE_OAUTH_TOKEN` **>** Keychain.

The 07-28 fix — "remove `oauthAccount`, never `/login`" — was necessary and **not sufficient**.
The field came back within a day with Un confirming he never ran `/login`.

**Real root cause:** 8 of 15 oracle repos (chrome, codec, neon, pixel, pops-atlas, relay,
rpro-ent-atlas, vets-hub) had a one-line `.envrc` exporting only `DISCORD_STATE_DIR`. Because
direnv does not merge with parents, **having *any* `.envrc` fully shadowed `~/.envrc`.** Those
repos ran with no credential → Keychain fallback → resolved to one shared account → Claude Code
wrote `oauthAccount` back → every session opened afterwards inherited it.

"Something else re-persists the field" was never a mysterious writer. It was ordinary sessions
with no token.

**Fixes applied:** `maw token use <name>` in all 8 (writes the same explicit three-line block the
healthy repos already use — deliberately *not* `source_up`, which would introduce a second
pattern into a uniform setup). `~/.envrc` removed; it had silently made every directory under
`$HOME` default to `por`, which is why `maw token scan` listed `~` as an oracle. A `claude()`
guard in `~/.zshrc` now refuses to launch without a token, allowlisting
`setup-token|mcp|doctor|config|update|install|--version|-v|--help|-h`.

**Honest limit of the guard:** `.zshrc` is sourced by *interactive* zsh only — not scripts, not
cron, not `zsh -c`. That gap is why the Keychain entries were removed afterwards. **A rule you
must remember is not a fix, but a guard is only as wide as the shells that load it.**

**Two hypotheses were labelled and then falsified** — good discipline worth repeating:
- "The 4 Keychain entries are the reservoir that refills the field" → the fix was observed
  holding *before* they were touched. Deletion was defense-in-depth, not the cure.
- "Running sessions flush the field back from memory" → `~/.claude.json` was rewritten twice
  and survived a session restart with the field still absent.

## 4. Auth-flow ordering, and the token acceptance test — confidence: HIGH

`claude setup-token` is an auth flow and **writes `oauthAccount` exactly like `/login`.** It must
run *before* removing the field. Reversed, it silently undoes the fix and burns the test — which
is how a whole day could have been lost a third time.

**Every token, every time:**
```bash
pass show claude/token-<n> | wc -c    # must be 109 (108 + newline)
```
Also check the 12-char prefix matches the others and no whitespace crept in. Save with
`pbpaste | pass insert -m -f claude/token-<n>` — never through shell history.

**`pass insert -m` answered-then-aborted wipes the entry.** Answering the overwrite prompt `y`
and then Ctrl-C leaves an empty secret. That is how `token-trio` was destroyed mid-session.

**A malformed credential fails silently and can display another account's numbers.**
`token-kla` was **508 chars instead of 108** — surrounding text captured during a paste. It froze
the usage poller, then showed kla as `14/41`, *identical to trio*, which reads exactly like
cross-contamination but was not. Regenerated → `1/0`. **Check credential shape before concluding
contamination.**

**What can and cannot identify an account:**
- `/status` names the auth **source** (`Auth token: CLAUDE_CODE_OAUTH_TOKEN`), not the account
- `userID` in `~/.claude.json` is a **machine id** — identical across accounts, useless here
- `CLAUDE_CODE_OAUTH_TOKEN` is **stripped from subprocess environments**, so no Bash call and no
  subagent can report its own account. Do not ask them.
- `~/.claude/runcat-<n>.json` holds **display cache only** (`title, symbol, metrics,
  lastUpdatedDate, metricsBarValue`) — no credentials. Judge the menu bar by `lastUpdatedDate`,
  not by the percentage.
- The only workable check is **per-account usage divergence**. Final proof:
  `trio 14/41 · un 2/36 · por 1/1 · tul 0/24 · kla 1/0`, all live.

## 5. Verification discipline — confidence: HIGH for the specific cases, MEDIUM as general rules

**Never verify an action with the tool that performed it.** `ps ax | grep -c <pattern>` returned
**0** while `pgrep -fl` and a native python scan both listed **2 live processes**. I was one step
from reporting a restart that had not happened. Use `pgrep`/`pkill`; treat a zero from a grep
pipeline as *unproven*, not as absence.

**The rtk rewrite matches the `ls` verb, not the program.** `tmux ls` printed one tmux session
while `tmux list-sessions -F` printed two. Prefer long forms (`tmux list-sessions`, `maw list`)
or `rtk proxy` whenever the result is evidence.

**Mundane explanation before tool bug.** Four count discrepancies this session, **zero were tool
defects**: symlinks (`find -type d` cannot see them), timestamps (measured an hour apart), wrong
objects (agent worktrees vs definitions), hidden dirs (`glob('**')` skips dotted dirs — there
`rtk proxy` was right and the "native" check was wrong). Ask: different semantics? different
time? different objects? **There is no inherently trustworthy method, only agreeing methods.**

**Adopted verbatim from pops-vet-oracle, the most durable line of the week:**
> A positive control proves the tool CAN return hits — it does not prove the count is COMPLETE.

**Do not destroy your own evidence while filtering it.** I stripped zsh-history timestamps with
`sed` and then could not answer "who wrote this file at 14:10". Re-parsing `: <epoch>:<elapsed>;`
settled it in one command — the write matched Un's own `maw token use un` to the second.

## 6. Quantify "unknown number of X" before publishing — confidence: HIGH

Our #2931 report said "unknown number of learnings may have been written but never indexed" and
proposed a backfill. Measured directly against `oracle.db`: 205 files on disk, 188 rows, gap 17,
**0 orphan rows** — and all 17 have **no frontmatter at all**, so they never went through
`oracle_learn` and span 06-08 → 07-24 rather than one incident. **188/188 of documents that did
go through the tool are indexed. Confirmed loss: zero.** The backfill step was invented work.

Three further claims of ours were withdrawn in the same comment: a transliterated path (`psi` for
**ψ** — a reader following it finds an empty directory), a named "affected file" that is in fact
indexed, and "document never indexed" when only the *vector* is lost (FTS5 is a separate path and
works). **Narrowing your own impact claim is what makes the surviving claim credible** — and the
surviving claim did get stronger: with ollama down, `oracle_learn` takes the failure branch on
every call and still returns `success: true`.

## Memories this session proved wrong — supersede, do not just annotate

| File | Problem |
|---|---|
| `ψ/.../2026-05-08_claude-code-multi-account.md` | Recommends `claude auth logout`→`login` as "safest". That command writes `oauthAccount` and breaks every env-var token. **Actively dangerous.** |
| `ψ/.../2026-07-28_oauthaccount-overrides-env-var.md` | "Remove the field, never `/login`" — necessary, not sufficient; disproven within 24h. The correction currently lives only in auto-memory. |
| `maw_token_not_working.md` | Has a SUPERSEDED header but the body still instructs `/logout`→`/login` and "don't suggest `maw token use`". Both now backwards. |
| `rtk_eats_rg.md` | Mechanism is fiction — there is no `rg` binary at all; it is a shell function from `~/.claude/shell-snapshots/`, invisible to subprocesses, so `rtk proxy rg` also fails. Advice survives, cause does not. |
| `maw_wake_prompt_truncates.md` | Probably obsolete — that symptom was #630's pane-readiness race. Still enshrined in global CLAUDE.md; re-test before it hardens into DNA. |

**A supersede marker is not enough when the body still reads as a runnable instruction.**

## Unresolved — do not build on these

- **39 vs 45 dead symlinks.** Morning: "39 dead, the safe reversible first move." Afternoon:
  45 symlinks, **0 dead**. Unknown whether repaired or mismeasured. The planned first step of the
  skill cleanup no longer exists. The retracted figure is still live in
  `skill_architecture_three_tiers` (loads every session) and was **sent to pops-vet** with no
  correction in flight.
- **`CLAUDE_CONFIG_DIR`** — `~/.zshrc:141-142` already aliases `claude-kla`/`claude-por`, but
  neither directory was ever created. Designed and abandoned. It would make the shared-field bug
  structurally impossible; cost is fragmenting 120 skills + memory + MCP config across N dirs.
  Fall back to it only if `oauthAccount` returns.
- **`oracle_search` returns `source_file` paths that do not exist on disk** — the index stores
  title-derived filenames, and recent learnings are not retrievable at all. A plain `grep -ril`
  over the real directory found everything the search missed.

Related: [[2026-07-28_oauthaccount-overrides-env-var]], [[2026-07-28_silent-credential-override-pattern]],
[[2026-06-15_stale-memory-worse-than-no-memory]], [[2026-06-26_maw-engine-config-silent-fallback]],
[[2026-05-09_wrapper-trust-failure-three-same-source-agreeme]], [[2026-06-08_token-chain-documentation]],
[[2026-06-19_never-teach-untested-tools]], [[2026-07-29_keychain-entries-removed]]
