# CI Green ≠ App Works — The Post-Deploy Verification Gap

**Date**: 2026-07-03
**Source**: rrr --deep: vets-hub post-deploy debugging + pops-clinic-oracle handoff
**Confidence**: High (validated same day the pipeline went green)

## The Core Pattern

A fully green two-tier CI/CD pipeline (check→test→build→deploy all passing) is **not proof the application works**. The night vets-hub's pipeline went green, three sequential runtime bugs surfaced only after real pods started:

1. Init container schema path was relative → resolved against the wrong WORKDIR
2. Init container had a single env var via `configMapKeyRef` → ORM needed a second one, only visible at runtime
3. Auth library needed a host-trust flag → invisible until someone actually tried to log in

None of these fail a `docker build`, a lint pass, or a unit test suite. They only fail when a real pod runs against real infrastructure.

## Reusable Checklist: Post-Deploy Smoke Test

After any deploy — CI-driven or manual — verify in this order before declaring done:
1. `curl` the health/root endpoint → expect 2xx
2. `curl` one DB-backed endpoint (not static reference data) → expect real data, proves DB connectivity + migrations ran
3. `curl` one protected endpoint unauthenticated → expect 401/403, proves the auth guard is wired
4. Attempt one real login/auth flow → proves the FULL auth chain (not just the guard)
5. If the service writes data (upload, form submit), perform one real write → proves the write path, not just reads

Steps 1-3 are cheap and scriptable (candidate for a CI post-deploy stage). Steps 4-5 usually need a human in the loop.

## Init Container Gotchas (reusable across any monorepo + ORM)

- **Absolute paths only.** The image's WORKDIR (e.g. `/app/apps/api`) is not the repo root. A relative `--schema packages/db/prisma/schema.prisma` resolves under WORKDIR and fails silently with a generic "file not found."
- **Full config injection, not partial.** Use `envFrom: configMapRef` for migration init containers, not a hand-picked `configMapKeyRef` list. ORMs often need more than the obvious connection string (Prisma: `DATABASE_URL` AND `DIRECT_URL`).

## Auth Gotcha

NextAuth/Auth.js v5 behind any reverse proxy on a non-Vercel host needs `AUTH_TRUST_HOST=true` (or equivalent). Without it: generic "server configuration" error at `/api/auth/error`, `UntrustedHost` in logs. This is invisible in local dev (no proxy) and easy to drop when porting env vars from docker-compose to a secrets manager — audit your auth library's proxy-trust requirement explicitly when migrating hosting.

## Manifest-Drift Safety Rule

Before trusting any hand-written IaC manifest for an **already-running** stateful service (postgres, any DB), dump live truth first:
```bash
kubectl get deploy <name> -o yaml
kubectl get pvc
```
Reconcile every field — user, db name, PVC claim name, size, volume name, nodeSelector — before the manifest is ever applied. A mismatch on PVC claim name silently binds a **fresh empty volume** on apply = data loss. Keep such jobs `when: manual` until reconciliation is verified.

## Ephemeral vs Durable Fix Discipline

A live `kubectl patch configmap` (or similar in-cluster patch) is **ephemeral** whenever the CI pipeline rebuilds that resource from a source of truth (Infisical, git) on every deploy. Pattern: patch live for instant verification → immediately persist the same fix to the actual source → confirm the next redeploy doesn't regress it. Skipping the persist step means the bug silently returns on the next tag.

## Terminal Ops Nuance

Long `kubectl patch -p='[...]'` one-liners get corrupted by terminals that auto-indent pasted multi-line text (literal spaces inserted mid-JSON-string). Heredocs (`cat <<'EOF'`) fail the same way — the closing delimiter gets indented and the shell hangs waiting for it. Workaround: build the patch JSON via a sequence of short `echo -n '...' >> file` lines (each short enough not to wrap), `cat` to verify, then `kubectl patch --patch-file`.

## Cross-Agent Knowledge Transfer Pattern

When a lesson needs to reach a sibling agent (e.g. another project's PM Oracle) who is mid-task on something unrelated:
1. Write full detail to their **durable** channel (Oracle thread) — they read it whenever.
2. Send a **short** live ping (tmux/maw hey) with an explicit "read after your current work, no action now" framing — this respects their in-progress task while still surfacing urgency-free awareness immediately.
3. Verify delivery by **directly observing** their live session (capture pane) rather than assuming the message landed — confirmed both the delivery and a written acknowledgment in the thread.
4. Before sending the live ping, check the target is at a natural pause point (blocked on a human decision, not mid-execution) to minimize interruption cost.
