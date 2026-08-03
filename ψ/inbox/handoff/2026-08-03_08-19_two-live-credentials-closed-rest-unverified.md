# Handoff: the two provably-live credentials are closed

**Date**: 2026-08-03 08:19 GMT+7
**Supersedes**: `2026-08-01_18-18_credential-audit-verified-32-remain-node-renamed.md`
**Commits since**: `26ac237` → `2bdd708`, pushed, `main` in sync

> This repo is public. No credential map here — hashes, locations and the runbook live in
> `~/security/` (700/600, outside git).

---

## ✅ Closed and verified — do not redo

| what | how it was proven closed |
|---|---|
| **LINE channel access token** (`pawrent-dev`) | old token now returns **401**; the same test returned **200 with the bot's name** an hour earlier, so the method is proven |
| **Gemini API key** | old key deleted at AI Studio; new key in Infisical → patched into k8s → **pod confirmed serving the new value** |

These were the only two credentials in the whole audit **proven live by their own issuer**.
Everything else on the list is *"pattern matched and I could not reach it to test."*

## Where these things actually live (hunted down the hard way)

| credential | real home |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | **ConfigMap `pawrent-config`**, ns `pawrent` — *not* a Secret, *not* Vercel |
| `GEMINI_API_KEY` | **Secret `ai-secrets`**, ns `ai-pops`, deploy `doc-extraction`, fed from **Infisical** |
| the pawrent app | GitLab CI at `git.pops.vet` → downstream deploy repos `pops-pet/pawrent/deployment/{dev,prod}-cluster` → k8s. **Vercel is dead**; `vercel.json` and `.env.local` are leftovers |

Three dead ends that cost time — do not repeat them:
- `.env.local` says *"Created by Vercel CLI"*. Stale. Vercel is not used.
- `deployment/dev-cluster/README.md` claims `pawrent-secrets` holds the LINE token. It does not.
- `kubectl.kubernetes.io/last-applied-configuration` is the last *applied* config, not live
  state. Read `.spec` directly: `kubectl -n <ns> get deploy <d> -o jsonpath='{.spec.strategy.type}'`

## Working commands, in the shape that worked

```bash
# ConfigMap (plaintext)
kubectl -n pawrent edit cm pawrent-config
kubectl -n pawrent rollout restart deploy/app && kubectl -n pawrent rollout status deploy/app

# Secret (base64 — use stringData, never edit the encoded value by hand)
read -rs NEWKEY                       # silent; paste + Enter. Keeps it out of shell history
kubectl -n ai-pops patch secret ai-secrets --patch-file /dev/stdin <<EOF
stringData:
  GEMINI_API_KEY: "$NEWKEY"
EOF
unset NEWKEY
kubectl -n ai-pops rollout restart deploy/doc-extraction

# verify without displaying the secret
kubectl -n ai-pops exec deploy/doc-extraction -- printenv GEMINI_API_KEY | cut -c1-6
```

`doc-extraction` uses `strategy: Recreate` (still, as of today) — restarting it drops the
pod before the new one starts. Brief downtime, by design; the node was at 98% CPU requests
when that was set. There is a pending note to revert it to RollingUpdate after the
`pawrentdev` expansion.

---

## ❌ Retracted — claims from earlier handoffs that were wrong

Believing any of these will waste the next session:

| claim | truth |
|---|---|
| LINE channel secret leaked in two PUBLIC repos for 3 months | the value is `your-messaging-api-channel-secret`. A placeholder |
| `.env.example` files hold real values (3 files named) | all placeholders; one of the three files **does not exist** |
| `leica-oracle` may not be clean | it is clean. The 2026-07-29 conclusion stands |
| ~32 credentials still to rotate | **~29**, and none of them verified — see below |

Cause, once, for all four: I wrote ad-hoc scans that measured **length and entropy** and
bypassed the `is_placeholder` filter the real script already had. `cat` would have settled
each in five seconds.

---

## 🔜 Next session

**1. Triage the remaining ~29 before touching any of them.** They come from the same method
that produced four false alarms. Open them and read what the values *say* — do not measure
them. Expect the list to shrink a lot. ~10 minutes.

**2. Then rotate what survives.** Good news found late: many of them sit in **one k8s secret**
— `pawrent-secrets` in ns `pawrent` is documented to hold `POSTGRES_PASSWORD`,
`DATABASE_URL`, `DATABASE_ADMIN_URL`, `JWT_SECRET`, `CRON_SECRET`, `MINIO_ROOT_USER`,
`MINIO_ROOT_PASSWORD` and more. One coordinated change, not a scavenger hunt. **Verify that
list against the live object first** — the same README was wrong about the LINE token.

**3. Only then run the scrub.** `python3 ~/security/scrub-claude-credentials.py` (dry run
first). It knows 16 patterns and carries a deny-list of 14 values proven not to be secrets.

**4. File the maw upstream issue.** Two halves, both confirmed:
- pops-vet's: `maw hey` writes no inbox, exits 0, prints `delivered`. Reproduced 2/2 across
  two session types, including sending to self.
- mine: `maw hey --inbox` **and** `maw notify` both fail with *"cannot resolve a local inbox …
  not a known local oracle — check `maw locate <name> --path`"* — while
  `maw locate <same name> --path` **succeeds**. The error names the command that contradicts it.
- code: `send_federation.rs:470-475` records that `send_local_message_with_audit` takes no
  `inbox` parameter and always injects. The default path has no inbox write at all.
- **⇒ maw currently has no working durable message channel.** File-drop into `ψ/inbox/` is
  the only one. All three houses have adopted it; pops-vet's own report arrived that way.

**5. Small, real:** the LINE token lives in a **ConfigMap**, which is plaintext and readable
by more roles than a Secret. Move it to a Secret sometime.

---

## Key files

| path | what |
|---|---|
| `~/security/rotation-runbook-2026-07-29.md` | 8 steps, commands, per-step verification |
| `~/security/rotation-checklist-2026-07-29-ADDENDUM.md` | corrections both directions, retractions |
| `~/security/scrub-claude-credentials.py` | 16 patterns, dry-run default, deny-list |
| `ψ/inbox/2026-08-01_19-40_from-pops-vet_maw-hey-inbox-write-broken.md` | pops-vet's report, arrived by file-drop |
| `ψ/memory/learnings/2026-07-30_five-ways-a-secret-scan-lies.md` | why the count kept moving |
| `ψ/memory/learnings/2026-07-31_did-i-break-it-un-make-the-change.md` | the control technique |

## Rules that earned their keep this week

1. **A positive result is self-proving; only absence needs a control.** A 200 with the bot's
   own name cannot be faked by a placeholder.
2. **Read what a value says before measuring it.** Length and entropy called
   `your-messaging-api-channel-secret` a live credential.
3. **Never override a filter without asking why it filtered.** `is_placeholder` was right
   every single time.
4. **Report only what is not derived from the secret's characters** — length, a boolean, a
   hash, or what the issuer answered. Anything computed *from* its characters leaks it. This
   was violated three times in one day.
5. **`exit 0` is the actor's own testimony**, same as `capture` proving only the pane.
   Evidence is what the far end can see.
