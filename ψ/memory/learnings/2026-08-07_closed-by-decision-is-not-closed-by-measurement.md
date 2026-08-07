# Closed by decision is not closed by measurement

**Date**: 2026-08-07
**Confidence**: HIGH — specified by pops-vet-oracle as a fleet discipline, applied same day
**Related**: `2026-07-30_five-ways-a-secret-scan-lies.md` (Lie 1, Lie 5),
`2026-08-05_a-test-must-be-able-to-detect-the-thing.md`,
`2026-08-07_an-unbounded-review-stops-when-the-sponsor-runs-out.md`

---

## The rule

When a question is closed, **record how it closed**. There are two kinds, and they carry different
weight:

| kind | meaning | example (pop-node0 teardown, 2026-08-07) |
|---|---|---|
| **Closed by measurement** | evidence answered it | **G3** — deployments `0/0`, 10 PVs / 87 Gi on NFS `10.100.1.198`, `reclaim=Retain` |
| **Closed by decision** | the owner elected not to look | **G6** — Witchaphon: *"ไม่ต้องสนใจของในเครื่อง `.200` มันคือของเก่า ปล่อยมันไป"* — no etcd snapshot, no inventory, no `/root /opt /srv /etc/kubernetes/pki` |

**Never write the second as the first.** "Proven there was nothing on `.200`" is false. The true
sentence is:

> **"The owner decided it did not need to be looked at."**

That is a fully valid closure and entirely his to give. But an unanswered question that was **set
aside** is not an answered one, and the record must say which happened.

---

## Why it matters

The record outlives the session. Six months on, *"proven empty"* invites the next person to build
on evidence that was never gathered. *"Owner decided not to look"* tells them exactly what they do
and do not have, so they can re-open it cheaply if the stakes change.

This is `five-ways-a-secret-scan-lies` (unproven negatives) generalised onto a new axis: there the
gap was a **measurement** that could not detect the thing; here it is a closure that **never
measured at all**.

---

## How to apply

- Tag every closed gate with its closure mode, in every document that cites the closure —
  handoffs, retrospectives, weekly reports.
- If the owner overrules a concern: **drop it cleanly, no re-litigating.** Releasing a work item
  and pretending it was disproven are different acts; do the first, never the second.
- Watch for the drift on restatement. A closure summarised third-hand loses its mode first.
- **A decision can close a risk-appetite question. It cannot close a correctness one.**
  `qm list` before `qm destroy` survived the release order — and found three VMs named
  `infisical`, one of them the live secrets store. *"Is there anything valuable inside?"* was
  closed. *"Am I deleting the right box?"* never was, and could not be.

---

## Provenance of the actor, too

Same discipline, applied to who did the work: the teardown was executed by **Witchaphon himself**.
Every Oracle is outside `10.100.1.0/24` — pops-pet proved its own lack of access with a control
(`ping 1.1.1.1` OK, everything else unreachable) after briefly accepting an execution role it
could not perform.

> **Measurements arriving *through* an actor are not evidence of access *by* that actor.**

Record who had hands on the keyboard separately from who advised or verified.
