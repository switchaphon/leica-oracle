# Monorepo CI/CD: 6-Iteration Pattern to Green

**Date**: 2026-07-02
**Source**: rrr --deep: vets-hub Phase 3b
**Confidence**: High (validated across 2 projects)

## Pattern

When adding GitLab CI/CD to an existing codebase (single app or monorepo), expect exactly 6 iterations before the pipeline is green:

1. **Format** — existing code isn't formatted. Run prettier, commit, retag.
2. **Lint errors** — a handful of real errors hidden in hundreds of warnings. Fix only errors.
3. **TypeScript** — test files have pre-existing type issues. Exclude `__tests__/` from CI typecheck via `tsconfig.check.json`.
4. **Flaky tests** — timezone-dependent or environment-dependent tests fail on CI server. Skip with `.skip`.
5. **Docker build** — build args, registry paths, or Dockerfile context issues.
6. **Deployment config** — shared ConfigMap key collisions (PORT), missing schema paths, init container failures.

## Reusable Checklist for Phase 3c

Before enabling CI on a new project:
- [ ] Run prettier and commit
- [ ] Run lint, fix only errors (not warnings)
- [ ] Create tsconfig.check.json excluding test dirs
- [ ] Run tests on CI-like environment, skip timezone-dependent ones
- [ ] Verify Dockerfile builds with monorepo root context
- [ ] Verify per-service env var overrides (PORT, HOSTNAME)
- [ ] Verify ORM schema path for init containers

## Monorepo-Specific Lessons

- **Shared ConfigMap problem**: `envFrom: configMapRef` injects ALL keys to ALL pods. Override per-deployment with explicit `env:` entries.
- **Prisma in packages/**: `prisma migrate deploy --schema packages/db/prisma/schema.prisma`
- **Build-time secrets**: Only Next.js web needs NEXT_PUBLIC_* at build time. API has zero build-time env.
- **pnpm in CI**: `corepack enable && corepack prepare pnpm@X.Y.Z --activate` before every job.

## GitLab 18.x Breaking Change

Runner registration no longer accepts `--tag-list`, `--locked`, `--access-level` via CLI. Set tags in GitLab UI (Build → Runners → New group runner), then register with only `--url --token --executor --name`.

## Runtime Gotchas Discovered Post-Deploy (7th+ iteration)

CI going green ≠ app working. After pods deployed, three runtime bugs surfaced that no CI stage catches:

1. **Auth.js v5 `UntrustedHost`** → login fails with generic "server configuration" error at `/api/auth/error`. Fix: `AUTH_TRUST_HOST=true` in the secret store (needed for any Auth.js/NextAuth v5 app behind a reverse proxy on a non-Vercel host). Easy to miss when porting env from docker-compose to Infisical.

2. **Init container relative paths** — the migrate init container inherits the image's WORKDIR (`/app/apps/api`), so a repo-relative `--schema packages/db/...` resolves wrong. Use the **absolute** path `/app/packages/db/prisma/schema.prisma`.

3. **Init container env completeness** — Prisma schema declares BOTH `DATABASE_URL` and `DIRECT_URL`; injecting only one key → validation error P1012. Give the init container the full ConfigMap via `envFrom`, not single `configMapKeyRef` keys.

## Ephemeral vs Durable Fixes

When Tier 2 rebuilds the ConfigMap from the secret store on every deploy, a live `kubectl patch configmap` is ephemeral — the next tag wipes it. Any config fix (like `AUTH_TRUST_HOST`) MUST also go into Infisical or it silently regresses on the next deploy. Patch live for speed, then persist to the source of truth immediately.

## Manifest Drift vs Live State

When adopting an already-running namespace into a fresh deployment repo, the hand-written manifests often DON'T match reality. Here the live postgres ran as `postgres`/`vets_hub` while the new manifest assumed `vetshub_admin`/`vetshub` on a different PVC. Guard stateful redeploys with `when: manual` AND reconcile the manifest to live values (`kubectl get deploy X -o yaml`) before ever applying — otherwise it binds a fresh empty PVC and "loses" the data.

## Terminal Paste Corruption (operational)

The user's terminal auto-indents multi-line pastes, which silently corrupted long `kubectl patch` one-liners (`/app` became `/ap p`, `/apapp`). For live JSON patches, build the file with short `echo -n '...' >> file` lines (leading whitespace is harmless inside the quotes), `cat` to verify, then `kubectl patch --patch-file`. Avoid heredocs too — the closing `EOF` gets indented and never terminates.
