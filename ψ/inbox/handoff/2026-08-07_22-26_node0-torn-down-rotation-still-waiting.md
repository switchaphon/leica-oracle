# Handoff: pop-node0 torn down · the rotation is still waiting

**Date**: 2026-08-07 22:26 GMT+7
**Supersedes**: `2026-08-03_08-19_two-live-credentials-closed-rest-unverified.md`
**Arc covered**: 2026-08-05 (Discord bot recovery) → 2026-08-07 (teardown support)

> This repo is **public**. No credential map here — hashes, locations and the runbook live in
> `~/security/` (700/600, outside git).

---

## Where things stand

**pop-node0 is gone.** VM 100 / 101 / 104 destroyed 2026-08-07 ~17:2x. Executor was **Witchaphon
himself** — every Oracle is outside `10.100.1.0/24`; pops-pet proved its own lack of access with a
control. pops-vet-oracle supervised. Leica held no part of the execution and should not be
credited with any of it.

**Measured after** (figures kept in `ψ/inbox/2026-08-07_w32-data_teardown-measured-figures.md`
for Monday's W32 report):

| metric | before | after |
|---|---|---|
| prototype1 pool data | 81.56 % | **55.51 %** |
| prototype1 RAM | 50 / 62 GB | **34 / 62 GB** |
| `PFree` ×3 hosts | 16 GB | 16 GB — **unchanged, and correct** |

Required wording: **"moved 22 vCPU + 44 GiB from the old cluster to the new — recycled, not
retired."** Never "freed"; ADR-0007 says the capacity holds only until the new 3-node cluster
stands up.

---

## The two provenance rules this arc produced — carry them forward

**1. A gate closed by decision is not a gate closed by measurement.**
G3 (data safety) closed by measurement — `0/0` replicas, 10 PVs / 87 Gi on NFS `.198`,
`reclaim=Retain`. G6 (node-local state) closed by **operator decision** — Witchaphon elected not
to look. **Never write "proven there was nothing on `.200`".** The true sentence is *"the owner
decided it did not need to be looked at."*

**2. Put the irreversible step after the evidence.**
`qm list` found **three VMs named `infisical`** — 100 (p1, running), 104 (p3, stopped), **120 (p2,
running, the real one)**. Deleting by name was a 1-in-3 chance of destroying the live secrets
store. The guard that worked: `qm stop 100` → `curl :8443` proves Infisical still serves →
*then* `destroy`. `qm start 100` was full recovery in the gap.

---

## What got done (08-05 → 08-07)

- **12 `start.sh` rewritten + 1 created = 13 total.** (Corrected 2026-08-07 23:0x — an earlier
  draft of this handoff and the 08-05 retrospective both said "13 rewritten + 1 created", which
  implies 14. There are only 13 `start.sh` files fleet-wide: 11 uniform + leica's fleet script
  were rewritten, rpro-saas's was created. The fix itself is real and verified; only the tally was
  wrong. Caught by a `/rrr --deep` agent, not by me.) Every launcher was sourcing a stale `.env` that
  clobbered direnv's fresh token, and ran under non-interactive bash where the direnv hook never
  fires — so bots would have launched on rotated Discord tokens *and* dropped the per-repo Claude
  token. 13 dead credential files archived to `~/security/stale-discord-env-2026-08-05/`.
- **`/bot-up` skill** built and version-controlled at `.claude/skills/bot-up/` (live path is a
  symlink to it — one source of truth). **7 bots live**, all four token accounts confirmed
  *accepted* by reply, not merely loaded.
- **`.envrc` now gitignored in all 15 repos**; pops-vet's was the only one tracked — untracked
  with `git rm --cached` (gitignore never applies to a tracked file).
- **3 memory files corrected** that still carried the `claude auth logout → login` advice behind
  the two-day 15-oracle outage. The 07-29 fix had reached 1 of 4 files.
- **2 dead launchers fixed** — `pops-atlas` / `rpro-ent-atlas` now say *"has no Discord bot,
  application deleted 2026-07-29"* instead of telling the operator to run `direnv allow`.

---

## Pending — mine

- [ ] **Rotation Step 2 — the standing backlog, now deferred four sessions.** Most targets sit in
      one k8s secret, `pawrent-secrets` ns `pawrent`, on `.209`/`.206` — **not** on the teardown
      path, so it was never blocked by it. **Verify the key list against the live object first**;
      that README lied about the LINE token. Then Step 3 (`scrub-claude-credentials.py`, dry run
      first) and Step 5 (LINE token: ConfigMap → Secret).
      *This is the only item where risk grows with time.*
- [ ] Collapse the 12 hand-copied `start.sh` into one shared launcher (the drift is structural —
      it is how rpro-saas ended up with a bot and no launcher).
- [ ] Fix leica's fleet `start.sh`: header documents 11 repos' token assignments, body wires 2.

## Pending — needs Witchaphon

- [ ] **`requireMention`** — channel `…474455` is `false` in leica, rpro-ent and nodered, so all
      three answer everything there. Name which channels stay chatty; the rest get flipped.
- [ ] **rpro-saas has no access config** — `.discord-state/` empty since 8 Jun. Needs
      `/discord:access`, which only the operator runs.
- [ ] **Token map is public** in `leica-oracle/start.sh` (`trio`/`un`/`tul`/`kla` → repos). Pushed
      without asking. Low risk — nicknames, not secrets — but the call is his.
- [ ] **Two upstream issues, both outward-facing, both on other people's repos** — need the repo
      and a go-ahead:
      - `maw hey --inbox` / `maw notify` fail with *"not a known local oracle — check
        `maw locate <name> --path`"* while that exact command **succeeds, exit 0**. Plain `hey`
        paints a tmux pane and writes nothing durable (inbox delta 0 across 3 sends). Re-confirmed
        2026-08-07 on `maw-rs v26.7.28-alpha.1027` — **same binary as the 08-01 evidence, so that
        evidence is not stale.**
      - **`oracle_learn` / `vec0` — ONE bug: the embedding. Corroborated by two Oracles.**
        Returns `success: true` while the vector embedding fails. Two error surfaces, same root:
        leica got `sqlite-vec not connected` (`sqlite-vec.ts:198 requireDb`), vets-hub got
        `SQLiteError: no such module: vec0`. `oracle_search` is FTS5-only
        (`vectorAvailable: false`) and does not surface recent learnings for queries that should
        match dead-on.
        ⇒ Any Oracle asking "have we learned this before" gets a **false negative**, which reads as
        "this is new". **Operator action; not our repo.** Until fixed, read learnings from disk.

        > ### ⛔ RETRACTED — "it returns a filename it never creates" was FALSE, and mine
        >
        > I claimed `oracle_learn` returns `file:` paths it never writes, and called it a second,
        > separate bug. **It is not a bug at all. Every one of those files exists.**
        >
        > `oracle_learn` writes to the **vault** — `~/.oracle/ψ/memory/learnings/` (230 files,
        > written as recently as tonight) — and returns a path that *looks* repo-relative. I
        > resolved it against the repo, found nothing, and reported absence. **I checked one
        > location and never ran the control.** All four allegedly-phantom files were found in the
        > vault on the first look:
        > `2026-08-05_a-capable-instrument-still-lies-if-it-reads-its-ow.md` (4053 B, 5 Aug 19:07)
        > plus the three a `/rrr --deep` agent "confirmed" — it confirmed nothing, it inherited my
        > framing and checked the same wrong directory.
        >
        > **Root cause of my error:** the `/forward` skill states *"Never hard-code `~/.oracle/` —
        > that was a legacy vault pattern no longer in use."* That is **wrong**; the vault is live
        > and is where `oracle_learn` writes. It primed me to dismiss the only place the files
        > were. Worth fixing in the skill.
        >
        > Caught because vets-hub-oracle checked its own case before agreeing with me, which forced
        > me to check mine. Its correction was right that mine needed testing — and its own
        > resulting framing ("two separate bugs, mine proves the write path can succeed") also
        > collapses: there was only ever one bug. Credit to vets-hub either way; without the
        > pushback this would have reached the operator as fact.

## 🟠 Needs an owner — surfaced in the teardown `lvs`, unrelated to it

- [ ] **`vm-102-disk-0` build-server (prototype2) — 500 GB @ 100.00 %.** Full. Builds can fail
      silently. The one worth acting on soon.
- [ ] `vm-110-disk-0` pawrentdev (prototype3) — 150 GB @ 88.10 %. Slower burn.
- [ ] `vm-103-disk-0` on prototype2 is a **genuine orphan** (`Vwi-a-tz--`, no `o`, 0.47 % =
      ~4.7 GB real on a 1000 GB reservation). Closes Appendix B item 3 of the P4 plan with no new
      commands. The live one is the 500 G on prototype3.

## Elsewhere in the house

- **pops-vet-oracle** — lead on the new pops-vet prod 3-node cluster; reading pops-pet's
  `handover-orphaned-87gi-and-what-the-new-cluster-needs.md`.
- **vets-hub-oracle** — rev7 + selfaudit v3 parked until cluster planning lands. 12 commits
  unpushed as of 22:26 (its own work).
- **VMFS 1.34 TB on prototype1** — deliberately **not** part of the teardown. Separate job, needs
  a separate decision from Witchaphon. Nobody in 15 repos claims it, **and nobody has run the
  read-only `vmfs-fuse` look**. `wipefs` has no undo. Do not let it be treated as "free space" —
  the P4 plan calls it *"ข้อมูลที่ไม่มีใครแตะมา 12 ปี"*.

---

## Key files

| path | what |
|---|---|
| `ψ/inbox/2026-08-07_w32-data_teardown-measured-figures.md` | W32 numbers + required wording |
| `.claude/skills/bot-up/` | `/bot-up`; live path symlinks here |
| `~/security/stale-discord-env-2026-08-05/` | 13 archived dead tokens + provenance README |
| `~/security/rotation-runbook-2026-07-29.md` | 8 steps, per-step verification |
| `pops-pet-oracle/docs/adr/0007-*.md` | the teardown ADR |
| `pops-pet-oracle/ψ/plans/2026-07-31_dev-cluster-resize-and-infra-runbook.md` | P0–P6, holds P5/VMFS |

## Rules that earned their keep this week

1. **A capable instrument still lies if it reads its own footprint.** A tmux wait matched my own
   echoed command; `direnv export` printed nothing because `DIRENV_DIFF` was already set; a `ps`
   proxy contradicted the first-party window list. Anchor past your echo, take fresh reads
   (`env -i`), prefer the first-party registry.
2. **`set -a; source` is a clobber, not a fallback.** It overrides direnv rather than deferring.
3. **Apply a correction to every file carrying the claim, not just the one you were reading.**
4. **Closed by decision ≠ closed by measurement.**
5. **RTK turns empty output into one line.** It reported "1 commit" for 15 repos where the answer
   was 0. Use `rtk proxy` for any scan whose zero-result drives a decision.
