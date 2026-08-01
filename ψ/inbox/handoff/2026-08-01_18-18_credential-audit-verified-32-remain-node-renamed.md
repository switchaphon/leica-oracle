# Handoff: credential audit verified — 32 remain · node renamed to `mba`

**Written**: 2026-08-01 18:18 GMT+7
**Covers**: two sessions — 2026-07-29 17:00 → 07-30 06:04, and 07-31 17:20 → 18:07
**Supersedes**: `2026-07-29_16-28_multi-token-fixed-credential-rotation-pending.md`
(that file is still correct about what *it* knew; its headline number is not)
**Commits**: `1511eaf`, `174bf24` — both pushed, `main` in sync, working tree clean

> ⚠️ **This repo is public.** No credential map appears here. Hashes, file locations and the
> step-by-step runbook live only in `~/security/` (dir 700, files 600, outside git).

---

## Read this first if you read nothing else

The previous handoff said *"20 credentials pending rotation, checklist ready, just execute."*
**That number was wrong in both directions.** It was the honest output of six regexes over
9,188 files, and it got read as an inventory. Verified figures now:

| | |
|---|---|
| still to rotate | **32** |
| already closed | **24** |
| proven never to have been credentials | **~30** |

Anything still quoting "20" is stale.

---

## Done — do not redo

### ✅ Discord bot tokens — closed 13/13
14 leaked tokens across 13 bots. Un reset 11 into `pass` under `discord/<name>`; two
applications (`pops-atlas`, `Rust-bot`) were deleted outright. Verified per bot by decoding
the public bot ID out of each stored token — no secret was ever displayed:

```bash
pass show discord/leica | cut -d. -f1 | base64 -d     # -> the bot's own ID
pass show discord/leica | wc -c                       # -> 72, the acceptance test
```

### ✅ Discord tokens now come from `pass`, not `.env`
Eleven oracle repos each carry **one** line in their **own** `.envrc`:
`export DISCORD_BOT_TOKEN="$(pass show discord/<name>)"`. Verified resolving, right bot per
repo. `~/.envrc` was recreated by accident mid-session and removed again — **do not
recreate it**; direnv loads only the nearest `.envrc` and does not merge with parents, so a
home-level file is shadowed by all 15 repos and does nothing.

### ✅ GitLab PATs — 0 to rotate
All six returned 401. That was *unproven* until a live PAT was found in `pass` as
`gitlab/for-claude-oracle` (referenced from `pops-vet-oracle/.envrc`); it returned 200 while
a fabricated token returned 401, proving the method. The six really are revoked.
**Note: that control token expires 2026-08-03** — `for-claude-code-monitor` stops working then.

### ✅ Supabase — nothing to rotate
Un: no project uses Supabase any more. Confirmed by DNS with both controls — both project
refs are NXDOMAIN, identical to a fabricated ref, while `supabase.com` resolves. Three
secrets dropped. (An earlier "Supabase is internet-reachable ⚠️" claim was wrong: it tested
the *shared* pooler hostname, which answers for every tenant.)

### ✅ The public repo is clean, with no caveat
Its one hit is a dev-default connection string — user, password and host all defaults. Not a
secret. **No history rewrite is needed**; the 2026-07-28 *rotate-and-accept* governance
stands as written.

### ✅ maw node renamed `leica` → `mba`
Every inter-oracle message read `[leica:<agent>]`, which looked like Leica sent everything.
It was the **node name** — this machine's federation identity; the address format is
`<node>:<agent>` and all 15 oracles share one laptop. Changed in **both** config layers
(`~/.config/maw/maw.config.json` and `maw.config.50.json`; the `.50` layer held *more* agent
entries than the base). The `agents` routing table's values are now `local`, an official
selfAlias, so a future rename cannot orphan them. Backups: `~/.config/maw/*.backup-2026-07-31`.
**Nothing needed restarting** — verified per layer: the CLI re-reads config per invocation,
the agent sessions never read it at all, and the daemon serves neither name.

### ✅ The scrub script is ready but NOT run
`~/security/scrub-claude-credentials.py` — 6 patterns → 16, plus a `DENY_HASHES` list of 13
values proven not to be secrets, virtualenv exclusion, and a case-insensitive
reference-vs-value filter. Dry run: **56 values / 129 files**. Do not run `--apply` until
rotation is done; scrubbing a live credential's copy only removes your ability to find it.

---

## 🔴 Next action — two credentials are provably live

Runbook with per-step commands and verification: **`~/security/rotation-runbook-2026-07-29.md`**

| # | what | why it is first |
|---|---|---|
| 1 | **LINE channel access token**, bot `pawrent-dev` | tested LIVE (200). The only remaining credential that reaches **real people**. Use **Reissue**, not *Issue* — *Issue* leaves the old token valid and the step accomplishes nothing |
| 2 | **Gemini API key** | tested LIVE (200), billable. Create the new key before deleting the old |

Then:

| # | what | count |
|---|---|---|
| 3 | four secrets still in repo `HEAD` (pops-pet, pops-vet) + three removed from `HEAD` whose rotation was **never confirmed** | 7 |
| 4 | cluster stores on the VPN — postgres, MinIO, InfluxDB, Redis | ~13 |
| 5 | auth/session signing secrets — **these log everyone out**, schedule it | ~9 |
| 6 | loose ends — Mapbox (restrict by URL, do not rotate), Upstash, LINE channel secret | 3 |
| 7 | scrub, then delete the cleartext backup tarball it writes | — |

**Two traps in step 4:** one postgres password is shared by **six** services (task / station /
user / device / cctv-capture / tenant-1) — rotate without updating all six and they all go
down. And one target runs on CloudNativePG: update the secret, don't `ALTER USER` behind the
operator. **vets-hub goes through Infisical** — editing its k8s secret directly gets
reverted on the next sync.

---

## Report upstream — needs no VPN, no waiting

1. **arra #2931 — the root cause we reported was wrong.** Three days of blaming ollama. The
   actual error is now explicit: `SQLiteError: no such module: vec0` — the sqlite-vec
   extension is not loaded into SQLite at all. ollama is *also* down, but fixing it would not
   help. `oracle_learn` still returns `success: true` while embedding fails, which is the
   original complaint and is still true.
2. **`maw hey --inbox` fails for every agent**, including the node's own oracle
   (*"cannot resolve a local inbox … not a known local oracle"*), while
   `maw locate <agent> --path` resolves those same agents to real repo paths. Two resolvers
   that should agree, disagreeing.
3. **No maw config layer contains `vets-hub-oracle`** — the name the live tmux session
   actually uses. `vets-hub` and `vets-hub-codex-2` exist only in the `.50` layer.

---

## Hygiene, still open

- **gitleaks pre-commit hook exists only in `leica-oracle`.** It belongs in all 15. It earned
  its keep during this session — it blocked a retrospective that had a credential-shaped URI
  written into it, in a document about not doing that.
- **`.env.example` files carry real values** in at least one repo. Two of the seven
  in-git-history secrets were sitting in one.
- **The inflow has not stopped.** New secrets were entering `~/.claude` *during* the audit.
  Scrubbing is a one-time cleanup of a pipe that is still open.

## Older carry-overs, untouched again

Skill re-baseline against 120 (96 never called) · agent merge 26 → 10 (documented, verified,
deliberately not executed) · `census2.py` cannot reproduce `clean.json` · re-test
`maw wake --prompt` against v26.7.28.

---

## Rules earned — apply these

1. **A scan's coverage is a property of its pattern list, never of its result.** Six regexes
   reported 20; the real number was three times that.
2. **A negative result needs a positive control.** "All six dead" and "the test never
   authenticates" produce identical 401s. And **the control is usually already on the
   machine** — in `pass`, in a `.envrc`, in a file you skimmed an hour ago.
3. **A positive result is self-proving.** Only a valid key gets a 200. Controls are for
   absence, not presence.
4. **"Not in HEAD" is not "rotated."** Deleting a line from a file does nothing to a password
   on a server. A commit named *"redact revoked …"* records an intention.
5. **When a change is followed by a failure, un-make the change and re-run.** Ninety seconds
   settles "did I break this?" better than any amount of reasoning. Requires a backup —
   which is why you always take one.
6. **A failing test is not evidence until you know the test reads what you changed.**
   `maw route` is a pure planner: no flags, no data, `not_found` forever.
7. **Redact the window, not the target.** This audit leaked two secrets itself by masking the
   value under investigation and printing its neighbours in full.
8. **Scanning for secrets creates secret-shaped strings.** A fabricated control written into
   a transcript is found by the next scan as a real hit. Deny-list it the moment you invent it.
9. **Short, low-entropy values must be dictionary-checked** before a reuse sweep is believed.
10. **Enumerate before you aggregate**, when the number is the deliverable. A summary figure
    hid seventeen library constants and one self-fabricated token for several turns.

---

## Key files

| path | what |
|---|---|
| `~/security/rotation-runbook-2026-07-29.md` | 8 steps, commands, per-step verification, final verdict |
| `~/security/rotation-checklist-2026-07-29-ADDENDUM.md` | the corrections in both directions |
| `~/security/rotation-checklist-2026-07-29.md` | the original 20, now annotated |
| `~/security/scrub-claude-credentials.py` | 16 patterns, dry-run by default |
| `ψ/memory/retrospectives/2026-07/30/06.04_…` | the credential audit retro |
| `ψ/memory/retrospectives/2026-07/31/18.07_…` | the node-rename retro |
| `ψ/memory/learnings/2026-07-30_five-ways-a-secret-scan-lies.md` | the durable method |
| `ψ/memory/learnings/2026-07-31_did-i-break-it-un-make-the-change.md` | the control technique |
