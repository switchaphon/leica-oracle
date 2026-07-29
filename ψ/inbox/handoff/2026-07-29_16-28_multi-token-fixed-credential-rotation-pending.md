# Handoff: multi-token fixed · credential rotation pending

**Date**: 2026-07-29 16:28 GMT+7
**Session**: 12:17 – 16:28 (~4h 11m) · context ~540k
**Commits**: 6 (`c0986d5` → `6b5f48a`), all on `main`, **none pushed**

---

## What We Did

### ✅ maw upgraded — two "bugs" were one stale binary
`v26.7.16-alpha.1159` → **`v26.7.28-alpha.1027`** (99 commits behind).
Both the ambiguous attach picker and wake-lands-in-shell-buffer were fixed upstream days ago
(`1d394e2`/#612, `8f6133b`/#630). **Our own memory said "pull + rebuild", which is wrong** — maw
installs from GitHub *releases*, so `git pull` on the source changed nothing. Nat had closed
Un's own issue #711 within 17 hours; we just never installed it.
Backup at `~/.local/bin/maw.backup-v26.7.16-alpha.1159`.

### ✅ arra-oracle-v3 updated
Pulled 26 commits (`8212374d` → `7ff6fabe`), MCP restarted. Two near-identical ghq clones
existed; the live MCP runs **`arra-oracle-v3-alpha`**. The unused one is now `_arra-oracle-v3`.

### ✅ Upstream #2931 corrected
Posted a comment withdrawing four of our own claims — a transliterated path (`psi` for **ψ**), a
"missing" file that is indexed, "unknown number of lost learnings" that measured to **zero**, and
"never indexed" when only the vector is lost. The core bug still stands and got stronger:
`oracle_learn` returns `success: true` while embedding fails, on every call, because ollama is
down. Verified live during this session's own `/rrr` sync.

### ✅ Multi-token auth FIXED — the real root cause
Not the Keychain. Not `/login`. **8 of 15 oracle repos had a one-line `.envrc` that set no token,
and direnv does not merge with parent `.envrc` files** — so they shadowed `~/.envrc`, ran with no
credentials, fell through to Keychain, resolved to one shared account, and Claude Code wrote
`oauthAccount` back, poisoning every session opened afterwards.

Fixes: `maw token use un` on all 8 · `~/.envrc` removed · `claude()` guard added to `~/.zshrc` ·
`oauthAccount` removed · 4 Keychain entries deleted (defense-in-depth, **not** the fix).

**Five accounts now report distinct live usage — first time ever:**
`trio 14/41 · un 2/36 · por 1/1 · tul 0/24 · kla 1/0`

Also: `token-kla` had been **508 chars instead of 108** (extra text captured in a paste), which
made kla display trio's numbers and looked exactly like cross-contamination. Regenerated.

### 📄 Documented, deliberately NOT executed
- **Agent merge 26 → 10** (`c0986d5`) — re-validated against disk (26/26/6, all clean), three plan
  errors corrected: **3 git repos not 2** (`clinic/atlas` has its own remote), the snapshot commit
  is unnecessary (HEAD already *is* the snapshot), `agents-backup-26` is redundant on a feature
  branch. Un's call: the document is the deliverable.
- **Skill census** (`509dfd9`) — 96 of 120 skills never called (80%) across 331 transcripts.
  Option A (per-repo `.claude/commands/`) has **0% adoption after 82 days**.

### 🔁 Corrected my own false alarm
I claimed "39 dead symlinks" had drifted to "0 dead" and nearly sent pops-vet a correction.
**There was no drift.** "Dead" meant *never-called*, not *dangling*.
`96 never-called = 39 symlinks + 57 real dirs`; separately `45 symlinks, 0 dangling`. Both always
correct. Fixed in 5 places (`b55e0ba`).

---

## ⚠️ Discovered: `leica-oracle` is the ONLY PUBLIC oracle repo

| | |
|---|---|
| 🔴 PUBLIC | **`switchaphon/leica-oracle`** — this repo |
| 🔒 private | the other 14 (chrome, codec, neon, pops-*, rpro-*, vets-hub, …) |

And it holds the most cross-project memory, inter-oracle mail, and `ψ/learn/` dumps of other
people's codebases. **Full git history scanned — 1,428 objects, clean:** no GitLab PAT, no
Anthropic token, no `root:<32hex>`. One hit only:

```
ψ/learn/_POPs_/vets-hub/2026-04-26/1735_QUICK-REFERENCE.md
postgres://postgres:<8 chars, entropy 2.75>@localhost:5432
```

Reads as a dev default, but it is public — **confirm it is not reused before dismissing it.**

---

## 🔑 PENDING — 20 credentials to rotate

Un must do these; they live on external systems. Full checklist (mode 600, deliberately outside
git): **`/Users/switchaphon/security/rotation-checklist-2026-07-29.md`**

Scanned 9,188 files under `~/.claude/`. **Masked values excluded** — a "token" that is 60–90% the
letter `x` is a redacted example, not a secret. That filter removed 396 matches / 3 false alarms.

### GitLab PAT — 6 · rotate at `git.pops.vet` → Settings → Access Tokens

| ☐ | hash | len | files | where |
|---|---|---|---|---|
| ☐ | `2d2f46a47f` | 38 | 4 | pops-vet-oracle(2), pops-pet-oracle(2) |
| ☐ | `f00bc47968` | 38 | 3 | pops-vet(1), pawrent(1), **history.jsonl**(1) |
| ☐ | `ca260ade61` | 38 | 2 | **history.jsonl**(1), _POPs_/pops-vet(1) |
| ☐ | `5b2c26694b` | 38 | 2 | pops-vet-oracle(1), **history.jsonl**(1) |
| ☐ | `7e7878138a` | 38 | 1 | **history.jsonl**(1) |
| ☐ | `32fb83c3d7` | 26 | 1 | pops-vet-oracle(1) |

### Host credential `root:<32hex>` — 2 · the 07-28 incident, still unrotated

| ☐ | hash | files | where |
|---|---|---|---|
| ☐ | `01dfc71c27` | **97** | file-history(52), rpro-ent-oracle(36), paste-cache(8) |
| ☐ | `2e242ce524` | 1 | leica-oracle(1) |

→ Redis / InfluxDB / Postgres on host `rid`.

### Postgres passwords — 12

| ☐ | hash | len | files | where |
|---|---|---|---|---|
| ☐ | `6e75dea8e0` | 32 | 7 | paste-cache(3), pops-pet(2), _POPs_/pawrent(1) |
| ☐ | `fbd4a4a405` | 16 | 4 | paste-cache(2), rpro-ent-oracle(2) |
| ☐ | `7fa5f7f3c4` | 32 | 3 | pops-pet(2), history.jsonl(1) |
| ☐ | `f20a0d0dff` | 18 | 2 | pops-pet(1), file-history(1) |
| ☐ | `968ca52424` | 32 | 2 | pops-vet(1), file-history(1) |
| ☐ | `8978083a5e` | 48 | 2 | _POPs_/pawrent-frontend(1), paste-cache(1) |
| ☐ | `0de1020cfe` | 15 | 1 | history.jsonl |
| ☐ | `b9adc69265` | 32 | 1 | history.jsonl |
| ☐ | `ecc5a05393` | 15 | 1 | history.jsonl |
| ☐ | `dd3b118286` | 32 | 1 | history.jsonl |
| ☐ | `1fdec1154b` | 29 | 1 | pops-pet-oracle |
| ☐ | `a17a41d43e` | 16 | 1 | leica-oracle |

### Anthropic OAuth — ✅ nothing to do
Both matches are masked examples (87% and 64% the letter `x`), and neither matches any of the
five tokens currently in `pass`.

**Hot spots:** `~/.claude/history.jsonl` appears 8× · `~/.claude/paste-cache/` appears 14×.

**After rotating**, scrub the copies:
```bash
python3 ~/security/scrub-claude-credentials.py            # dry run — tested, touches nothing
python3 ~/security/scrub-claude-credentials.py --apply    # tar.gz backup first, then redact
```
It **redacts in place** rather than deleting — those `.jsonl` are session transcripts; deleting
one to remove a token throws away the whole conversation. Marker: `«REDACTED-<hash>-2026-07-29»`.
The backup tarball contains cleartext secrets — delete it once satisfied.

---

## Pending (non-credential)

- [ ] **Push 6 commits** — `main` is ahead of `origin/main`, nothing pushed today
- [ ] **Agent merge 26 → 10** — fully specified, ready, deliberately not run. Note `vet` and
      `clinic/frontend/app` sit on an **active** `prototype` branch that took commits today, so
      "verified against disk" decays. Hosts are self-hosted GitLab — `gh` does not apply,
      `glab` is not installed.
- [ ] **Skill re-baseline against 120** before implementing Option A. Tier structure is sound;
      the arithmetic (88 → 120, 69% → 80%) is stale.
- [ ] **`census2.py` cannot reproduce `clean.json`** — no session-exclusion guard, different
      schema. The committed page cites evidence its own script can't regenerate.
- [ ] **Re-test `maw wake --prompt`** against v26.7.28 — the "wake bare, then `maw hey`"
      workaround is enshrined in global CLAUDE.md and may be obsolete (#630 fixed that race).
- [ ] **#2931 still unfixed** upstream at `7ff6fabe`; ollama down locally.
- [ ] **ollama is down** → `vector_status: degraded`, all search is FTS5-only.

---

## Key Files

| Path | What |
|---|---|
| `~/security/rotation-checklist-2026-07-29.md` | the 20 credentials (600, outside git) |
| `~/security/scrub-claude-credentials.py` | dry-run by default (700) |
| `ψ/memory/retrospectives/2026-07/29/15.25_maw-stale-multi-token-root-cause.md` | 5-agent deep retro |
| `ψ/memory/learnings/2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md` | the durable lessons |
| `docs/oracle-skills-census.html` · `docs/pops-agent-team-structure.html` | documented, not executed |
| `~/.zshrc:150-165` | the `claude()` token guard |

**Rollback points:** `~/.zshrc.backup-2026-07-29` · `~/.envrc.removed-2026-07-29` ·
`~/.claude.json.backup-2026-07-29-1448` · `~/.claude.json.oauthAccount-removed-2026-07-29` ·
`~/.local/bin/maw.backup-v26.7.16-alpha.1159`

---

## Rules earned today — apply these next session

1. **Verify a binary against its RELEASE, not its source tree.** `git pull` on a repo you don't
   build proves nothing. `<tool> --version` vs `gh release list`.
2. **direnv loads only the nearest `.envrc`** and does not merge with parents.
3. **`ps` decides what runs; config only states intent.** Check for duplicate config entries of
   the same name before trusting the first block.
4. **Never verify an action with the tool that performed it.** `ps | grep -c` said 0 while
   `pgrep` found 2 live processes.
5. **`claude setup-token` writes `oauthAccount`** — run it *before* removing the field.
6. **Token acceptance test:** `pass show claude/token-<n> | wc -c` == 109. And `pass insert -m`
   answered-then-aborted **wipes the entry** (that is how `token-trio` was lost mid-session).
7. **A retraction is a claim** and needs the same evidence bar as what it retracts.
8. **Never reuse "dead"** for both *unused* and *unresolvable*. Say never-called or dangling.
9. **`command -v rg` returns success** even though no binary exists — `rg` is a shell function.
   Use `type` when the answer decides whether a subprocess can run it.
10. **Wrong memory is worse than no memory.** It stops you looking. Cost: two days.
