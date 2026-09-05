# Handoff: Water MVP shipped, five open defects, one gate installed

**Date**: 2026-09-05 09:00 GMT+7
**Session**: 2026-09-04 16:44 -> 2026-09-05 09:00, ~16 h wall clock
**Repo**: leica-oracle, `main`, 17 commits pushed through `3606452`

## What We Did

- **Surveyed a second ThaiWater API.** `twa-api-public.thaiwater.net` is NOT
  `api-v3` - different host, auth, code scheme. 195 paths recovered from 55
  Next.js chunks, 163 executed, 121 returned 200. Anonymous `x-api-key` ships in
  the site's own bundle; `/auth/get-public` grants all 159 datasets.
- **Shipped three dashboard layers**: baked RainViewer radar loop, 1,029-1,415
  rain gauges, 62 CCTV with a modal. All baked at build time because the artifact
  CSP blocks third-party images *silently*.
- **Answered the real question about the second host.** Not "different stations":
  768 of 780 are the same stations to within 0.1 m. Not "adds nothing" either:
  values agree exactly only 37% of the time, with one pair 8.783 m apart at the
  same minute. That pair resolved - `URTD03`, where api-v3 publishes
  `storage_percent: -18.93`, and a neighbouring gauge backs twa.
- **Had four conclusions retracted by rpro-ent-oracle, then a fifth by a deep
  audit.** All recorded in CASE-STUDY.md, now 29 traps.
- **Installed the repo's first executable gate** after an audit found eleven
  occurrences of one failure class in 39 days, every remedy a rule, zero gates.

## Pending

- [ ] **5 gitleaks findings in tracked, already-pushed files, never triaged.**
      `ψ/learn/_POPs_/vets-hub/2026-04-26/1735_QUICK-REFERENCE.md` (x2,
      `oracle-service-uri-credentials`), `ψ/learn/Soul-Brews-Studio/maw-js/2026-07-26/2120_ARCHITECTURE.md`,
      `ψ/writing/2026-06-16_oracle-school-netbird-zenoh-cheat-sheet.md` (x2).
      **leica-oracle is the only PUBLIC oracle repo.** Unknown whether real or
      false positives. Two more findings under `.discord-state/` are gitignored
      and never left the machine.
- [ ] **`.gitleaksignore` fingerprints are line-pinned and have drifted.**
      `layers.py:generic-api-key:44` no longer matches; the key sits at :54 after
      two edits above it. All six entries are now decorative for `gitleaks dir`.
      The pre-commit hook still protects, because it scans staged diffs only.
- [ ] **`refresh.sh` lock race, already fired in production** at 03:00:01 - both
      `full` and `live` ran and wrote the same SQLite file. Window is between
      `mkdir "$LOCK"` and `echo $$ > "$LOCK/pid"`: the loser sees no pid file,
      declares the lock stale, `rm -rf`s it and proceeds.
- [ ] **`compare_hosts.py` still prints the retracted freshness metric** with no
      caveat, and the reference page tells rpro-ent to run it.
- [ ] **`initLayers` reveals a control `build.py` documents as hidden**; with no
      `radar.json` you get a dead radar bar and a footer reading "undefined".
- [ ] `791` still quoted in four files after `780` was established live.
- [ ] Dashboard artifact `b712745f` still carries the pre-retraction station-set
      sentence. Unreadable from this account - needs the owning account.
- [ ] Ollama unreachable: both learnings written today are stored but NOT
      semantically searchable until re-indexed.
- [ ] 12 untracked paths (August inbox from other oracles, Soul-Brews-Studio,
      oracle-book-skills, `radar-on.png`). Deliberately left - separate concerns.

## Next Session

- [ ] Triage the 5 pushed gitleaks findings. Decide real vs false positive per
      finding, rotate what is real, record fingerprints with reasoning for what
      is not. This is the only security-adjacent item and it is in the public repo.
- [ ] Replace line-pinned fingerprints with a narrow `.gitleaks.toml` allowlist
      keyed on the key's value, so edits above a line stop breaking suppression.
- [ ] Close the `refresh.sh` lock race: write the pid inside the same atomic step
      as the lock, or use the lock directory's own mtime for staleness.
- [ ] Add a withdrawal note to `compare_hosts.py` where it prints freshness.
- [ ] Decide the licence question with สสน. - BLOCK stands on every cluster
      including dev/test until there is something in writing. **This one is
      rpro-ent-oracle's call, not Leica's.**

## Key Files

- `ψ/lib/hooks/check-generated-current.sh` - the gate, chained from the fleet
  pre-commit hook via `.git/hooks/pre-commit.local`. Made to fail before it was
  made to pass.
- `ψ/lab/hii-water-level/waterviz/{radar,layers,build}.py`, `refresh.sh`
- `ψ/lab/twa-thaiwater/{twa_pull,compare_stations,compare_hosts,audit_registry}.py`
- `ψ/learn/thaiwater/twa/twa.md` - survey hub, 10 traps
- `ψ/lab/hii-water-level/CASE-STUDY.md` - 29 traps
- `ψ/memory/retrospectives/2026-09/05/0631_eleven-in-thirty-nine-days-and-the-first-gate.md`
- `ψ/memory/learnings/2026-09-05_eleven-rules-and-no-gate.md`

## The one thing to carry

Two defects fixed at the end of this session were the same shape: a check that
inspected the **beginning** of a thing and concluded about the **whole** of it.
The radar guard read tile identity and concluded "placeholder" (a rain-free frame
is also uniform). The camera check read the JPEG start magic and concluded
"complete" (a truncated JPEG starts identically). Both had been shipping wrong
answers with nothing in the log.

When adding a validity check, ask what a *partial* or *empty* instance of the
valid thing looks like through it.

---

## ADDENDUM 09:20 - the gitleaks triage came back, and one finding is real

Triaged before closing. Result changes the priority written above.

| Finding | Verdict |
|---|---|
| `ψ/learn/_POPs_/vets-hub/.../1735_QUICK-REFERENCE.md` x2 | **False positive.** Postgres URI at `localhost:5432`, Docker image default user and password. Grants nothing remotely. |
| `ψ/learn/Soul-Brews-Studio/maw-js/.../2120_ARCHITECTURE.md` | **False positive.** Fabricated placeholder; the "value" is an English phrase describing the field's length limit. |
| `ψ/writing/2026-06-16_oracle-school-netbird-zenoh-cheat-sheet.md` x2 | **REAL, and third-party.** A NetBird setup key for Nat's class VM, under a heading reading "Admin Credentials (วันนี้)". Public since 2026-06-18, about 2.5 months. |

**Two things the scan did not report, and they matter more than what it did.**

One line above the flagged key, in the same block, is a plaintext admin dashboard
password - short, dictionary-style - with the admin email above it and the
dashboard URL above that. No rule fires on any of the three. A URL plus an email
plus a weak password outranks a setup key, which is typically single-use or
expires in thirty days.

And the flagged key appears on **four** lines in that file, not the two gitleaks
reported. Remediating only what the scanner named would leave half of it.

The host answered on 443 today. That is not proof the credentials work; it is
proof the question is not hypothetical.

**Not ours to rotate.** It is Nat's machine. Editing our markdown stops us
re-publishing it and revokes nothing. The control is Nat revoking the key and
changing that password.

### Order, when someone picks this up

1. Tell Nat out of band **before** touching the repo. Lead with the password, not
   the key gitleaks flagged. Ask: is the class stack still up, is the setup key
   consumed or expired, has the dashboard password changed since 16 June.
2. Then redact in one commit - all four key occurrences, the password, the admin
   email - in the masking style already used elsewhere in the repo so the file
   still works as teaching material. Leave the host IP; it is in the retro and is
   public-facing anyway.
3. **Do not rewrite history.** Public repo, 2.5 months, forks and cache. Matches
   the repo's own governance: rotate and accept, never force-push.
4. Separately, as scanner quality rather than security: `.gitleaks.toml` already
   enumerates placeholder passwords and just omits service-name-as-password.

### Mechanical finding worth carrying

Our `.gitleaksignore` uses the 3-part `path:ruleid:line` fingerprint that
`gitleaks dir` emits. A `gitleaks git` history scan emits a 4-part form including
the commit, **so not one existing entry would suppress anything in a history
scan.** With the line-pinning that already drifted today (`layers.py:44` now at
`:54`), the suppression file is less durable than it looks.
