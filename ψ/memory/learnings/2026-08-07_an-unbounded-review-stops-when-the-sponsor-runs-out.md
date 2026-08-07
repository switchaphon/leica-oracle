# An unbounded review stops when the sponsor runs out of patience, not when it is done

**Date**: 2026-08-07
**Confidence**: HIGH — diagnosed by the operator himself, mid-operation, and he was right
**Related**: `2026-08-05_a-test-must-be-able-to-detect-the-thing.md`,
`2026-08-05_instrument-reading-its-own-footprint.md`, `closed-by-decision-vs-measurement`

---

## The failure

A *"does anything invalidate this?"* review is **structurally unbounded**. Every honest round can
surface one more real thing — and each finding *feels* like diligence, because it is. The process
has no internal signal distinguishing **"still finding things"** from **"should have stopped an
hour ago."**

2026-08-07, pop-node0 teardown: three Oracles verified across two days. Findings kept arriving and
kept being genuine — the last one (Secrets/ConfigMaps live in etcd, so `0/0` replicas and NFS
`Retain` prove nothing about them) landed *at the moment of decision*. The next round would
probably have found something too.

Witchaphon stopped it:

> **ไม่ต้องสนใจของในเครื่อง `.200` มันคือของเก่า ปล่อยมันไป** — การสืบต่อกำลังพาทั้งบ้าน
> *"เดินลงลึก หรือถอยหลังไปเรื่อย ๆ"* · **16:00 แล้วยังไม่ได้เริ่ม rollout เลย**

He was right. The teardown then ran clean in under an hour.

**The stop came from the person paying for the process, not from the process.**

---

## The rule

**Set a round budget or a deadline before an open-ended review starts.** "Two rounds, then we
decide on what we have" is a real answer; "keep going until nothing new appears" is not — nothing
guarantees that state is ever reached.

**Report each new finding with the cost of the delay it implies, not just its own severity.** A
finding is not automatically worth acting on merely because it is true and new.

The lens already exists and gets applied to *other people's* backlogs — the same day's handoff
says of the credential rotation, *"the only item where risk grows with time."* That is
cost-of-delay reasoning. It was never once turned on the investigation while it was running.

---

## How to apply

- Before starting a verification sweep, state out loud: **how many rounds, or until when.**
- With every finding, volunteer: *"one more round costs roughly X; the delay costs roughly Y; I
  recommend proceed / continue."* Give the recommendation unprompted — the sponsor should not have
  to pull rank to get one.
- **Supplying more verification is not the same as helping.** Past a point it is the opposite, and
  it externalises the decision onto the human while looking like rigour.
- When overruled: drop it cleanly, no re-litigating — but keep the provenance honest. The question
  was **set aside**, not answered. See `closed-by-decision-vs-measurement`.

---

## The corollary that saved this operation

Stopping the *risk-appetite* questions did not stop the *correctness* ones. `qm list` before
`qm destroy` survived the release order, and it found **three VMs named `infisical`** — 100, 104,
and the live 120 — a 1-in-3 chance of destroying the running secrets store.

> A decision can close **"is there anything valuable inside?"**
> A decision cannot close **"am I operating on the right object?"**

Know which kind of question you are holding before you drop it.
