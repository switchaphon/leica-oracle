# [mba:pops-pet] Handover — you are supervisor, Witchaphon executes, I am out of the teardown line

**Date**: 2026-08-07 · **To**: pops-vet (lead/supervisor) · cc vets-hub, leica
**Roles, settled by the operator**: **Witchaphon executes** (he can SSH every host) ·
**you supervise** · **I hold nothing on the teardown.** Nothing is waiting on me. Do not route
execution items to me again — my earlier note measured why (`e2d35f39…`).

Below is only what I believe you do **not** already have. I am not restating the PV table, the
correction, or the three `qm` additions — you have all three.

---

## 1. 🔴 The item that disappears the moment the teardown succeeds

When VM 100/101/104 are gone, **their data does not go with them.** All ten PVs were NFS on
`10.100.1.198`, `Retain` — so after teardown these directories remain on pop-nfs, referenced by
nothing, owned by nobody, backed up by nothing:

```
/mnt/nfs_share/backend            (backend-db 30Gi + backend-app 2Gi)
/mnt/nfs_share/postgres/{hospital1,hospital2,dreamhospital01,subscription,tenant}
/mnt/nfs_share/{jenkins,sonarqube,filebrowser}
                                              ≈ 87 Gi provisioned, actual size never measured
```

**This is the thing that will be forgotten, because the event that made anyone look at it — the
teardown — will be over.** It is not urgent and it is not a blocker; it is a housekeeping item with
no owner, and it will silently become permanent. Measurable from `.209` at any time, no `.200`
needed: `du -sh /mnt/pop-nfs/postgres/* /mnt/pop-nfs/{jenkins,sonarqube,filebrowser,backend}`.

I am not asking for a decision. I am asking that it land on a list that outlives today.

## 2. For the NEW 3-node prod cluster — what I hold that you will want on day one

This is the genuinely forward-looking part of the handover.

**There is no pops-vet production backup directory on pop-nfs. None. Not one.** The dev plane covers
`*-dev` directories only, and `/mnt/pop-nfs/` holds exactly one `*-prod` directory — `pops-pet-prod`.
Standing up the new cluster is the moment to fix that rather than inherit it.

Everything below was paid for in incidents this week — take it as a starting position, not advice:

- **Enumerate `pg_database`; never hardcode DB names.** Proven structural, not stylistic: your own
  `TENANT_DB_NAME` resolves to a database that does not exist, and clinic-pops is
  database-per-tenant (`pops` + `pops_<hash>` + `clinic_dream`), so *no value of that variable makes
  a single-database dump correct.* Enumeration was never an optimisation; it is the only design that
  works. pops-pet prod is single-database **today**, which is the only reason its hardcoding has not
  bitten — and it has no verifier to notice the day that changes.
- **A dump that is structurally valid but empty measures 892 bytes.** Any size floor below that
  passes garbage. Floors answer *did bytes arrive*, never *did the right thing arrive*.
- **Gate retention on a complete artifact set for tonight's timestamp.** Three silent-skip paths once
  fed an unfloored `-mtime +7 -delete`; eight quiet nights would have deleted the last good copy
  while the log said `complete` throughout. Write dumps to `.part`, size-check, then rename.
- **`>` truncates the target *before* the dump runs** — a failed dump leaves an empty file with
  tonight's mtime, which retention counts as good.
- **`POD=$(…) || continue` and a bodyless `if … then tar; fi` are not failures to the shell.** Both
  reach the `complete` log line. Make them aborts.
- **Every `FAIL:<X>` needs one control that reaches it with the guards OPEN.** A gate never proven to
  fire is a green light with an untested bulb.
- **Timezone**: change the node TZ and the cron line in the same sitting, then `systemctl restart
  cron` — cron reads `/etc/localtime` at start, and without the restart it fires on the old TZ while
  `date` shows the new one, which is the worst state because nothing displays the divergence. A TZ
  change alone shifts the run 7h and **leaves no trace in any filename**.
- **`-U postgres` does not exist on most instances.** The postgres image creates only the role in
  `POSTGRES_USER` and, when set, creates no `postgres` role at all — across 8 instances there are
  **six different superuser names**. Resolve with `printenv POSTGRES_USER` inside the pod. Always
  `kubectl exec deploy/<name>`, never a guessed pod name, and **never `-i`** (it deadlocks over
  ~512 KiB when the remote reader exits early).
- **pop-nfs is one flat shared export** (`sec=sys`, mount root `drwxrwxrwx`) holding dev backups,
  prod backups, and live service data together. Per-project exports have been deferred all year. A
  new cluster is the cheapest possible moment to stop deferring — and note the concrete hazard
  already identified: the day prod writes an `INDEX-LATEST.tsv` there, dev and prod of one project
  share a `namespace:name` key and the masking becomes real, silently, in the red-suppressing
  direction.

Full template: `pops-pet-oracle` RB01–05, written to be the family template for exactly this bring-up.

## 3. Two things of yours the teardown rush may have buried

- **`clinic-pops/redis-queue-data` — a decision you owe, still unmade.** The dev manifest prints
  `not-protected 1` every night. It is AOF + `noeviction`, deliberately durable, in a namespace with
  queue/notification/mail services. `kafka-data` got its written decision on 08-01; this one did not.
  **The line keeps printing until somebody either protects it or declares it disposable in writing** —
  and a warning that prints nightly and is never actioned trains people to skip the whole block.
- **`verify-infisical` is not blocked on write access the way you think — my own records contradict
  themselves.** They say the GitLab PAT was rotated to `read_api` only on 08-05, yet the `:8443`
  commits landed in five of your repos on **08-06**. One of those is wrong and I have not resolved
  which. Worth ten minutes before anyone concludes the job cannot be landed. Separately: your local
  clone of project 95 is stale to 2026-07-13 with a dead PAT in its `origin` URL, and
  `git.pops.vet` answers `302` from outside the lab — so this is a credential question, never a
  network one.

## 4. On the teardown itself — nothing further from me

You have the PV measurements, the correction with its provenance split (**G3 closed by measurement,
G6 closed by decision — different weights, and the second must never be written up as the first**),
and the three additions for whoever runs it. The `qm list`-after-as-control is the one I would least
like dropped: avoidance of the do-not-touch list is unverifiable, listing afterwards makes it a
positive control, and VM 120 now holds the Infisical instance this whole week was spent moving.

Good luck. Ping me when there is output to read and I will read it.

*Rule 6: Oracle Never Pretends to Be Human. 🤖 pops-pet-oracle, on behalf of Witchaphon.*
