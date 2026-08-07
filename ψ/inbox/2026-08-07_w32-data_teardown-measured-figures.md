# W32 report data — pop-node0 teardown, measured

**For**: Monday's W32 weekly report (`ψ/archive/weekly-reports/`)
**Source**: pops-vet-oracle (supervisor), figures measured by Witchaphon (executor) 2026-08-07 17:2x
**Status**: measured, not planned — cite as such

---

## The numbers

| metric | before | after |
|---|---|---|
| prototype1 pool data | 81.56 % | **55.51 %** (predicted ~55 %) |
| prototype1 RAM | 50 / 62 GB | **34 / 62 GB** |
| `vm-100-disk-0`, `vm-101-disk-0`, `vm-104-disk-0` | present | **all three gone** |
| prototype2 pool | — | 30.80 % |
| prototype3 pool | — | 16.59 % |
| `PFree` (all three hosts) | 16 GB | **16 GB — unchanged** |

`PFree` not moving is **correct, not an anomaly**: VM disks are thin volumes inside pool `data`,
not separate PVs. Worth stating in the report so nobody reads it as a failed reclaim.

## Required wording

> **Moved 22 vCPU + 44 GiB from the old cluster to the new one — recycled, not retired.**

Do **not** write "freed" / "ปลดปล่อย". ADR-0007 is explicit that the capacity holds only for the
window between teardown and standing up the new 3-node cluster. Anyone reading "freed" will plan
workloads against it.

## Provenance — carry this into the report

- **G3** (data safety) closed by **measurement** — deployments `0/0`, 10 PVs / 87 Gi on NFS
  `10.100.1.198`, `reclaim=Retain`
- **G6** (node-local state) closed by **operator decision** — Witchaphon elected not to look

Never write "proven there was nothing on `.200`". The true sentence is **"the owner decided it did
not need to be looked at."** See [[closed-by-decision-vs-measurement]].

Executor was Witchaphon himself; **every Oracle is outside `10.100.1.0/24`** — pops-pet proved its
own lack of access with a control. Do not credit any Oracle with running these commands.

## Free findings from the same output — no new commands needed

**Appendix B item 3 of the P4 plan is answered.** `vm-103-disk-0` exists twice:

| host | size | flags | data | verdict |
|---|---|---|---|---|
| prototype2 | 1000 G | `Vwi-a-tz--` (**no `o`** = not open) | 0.47 % | **genuine orphan** — ~4.7 GB real on a 1000 GB reservation |
| prototype3 | 500 G | `Vwi-aotz--` (`o` = open) | 28.31 % | the one `pop-nfs` actually uses |

## 🟠 Two unrelated findings that need owners

- **`vm-102-disk-0` build-server (prototype2) — 500 GB @ 100.00 %.** Full. Build jobs can fail
  silently. This is the one worth acting on soon.
- **`vm-110-disk-0` pawrentdev (prototype3) — 150 GB @ 88.10 %.** Dev cluster approaching full.

Neither is teardown-related; both surfaced in the same `lvs` output.
