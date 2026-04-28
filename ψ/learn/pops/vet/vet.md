# vet — Learning Index

## Source
- **Origin**: ./origin/ → `/Users/switchaphon/_POPs_/pops/app/vet`
- **GitLab**: https://git.pops.vet/pops/frontend/vet
- **Owner**: pops (company namespace)

## What this is

A Next.js 16 / React 19 frontend for **POPS** — a Thai veterinary clinic platform. Multi-tenant, multi-branch, RBAC-driven. Currently in soft-launch; bundle-size optimization is on the post-launch backlog.

**Stack**: Next.js (App Router, fully client-rendered), TypeScript strict, Tailwind, NextAuth v4 (JWT, three-token model), GraphQL via `graphql-request` (codegen), Vitest + Playwright + Storybook, MinIO for assets, Docker + GitLab CI deployment.

**Distinct from**: `pawrent` (B2C pet health for Thai users) and `vets-hub` (Thai gov vet reporting). This is a clinic-facing SaaS.

## Explorations

### 2026-04-28 22:58 (--deep, 5 agents, Sonnet)

| File | What's inside |
|------|---------------|
| [`2026-04-28/2258_ARCHITECTURE.md`](./2026-04-28/2258_ARCHITECTURE.md) | 660 lines. Project identity, directory tree, entry points, three-token auth, RBAC v3, multi-tenant flow, internal docs map |
| [`2026-04-28/2258_CODE-SNIPPETS.md`](./2026-04-28/2258_CODE-SNIPPETS.md) | Curated snippets: layout shell, dynamic page pattern, refreshAndRescope, SWR + GraphQL, `combineRoles`, Zod forms, Modals API, Vitest+Playwright examples, Storybook story |
| [`2026-04-28/2258_QUICK-REFERENCE.md`](./2026-04-28/2258_QUICK-REFERENCE.md) | 330 lines. Setup commands, env vars, scripts, conventions, gotchas, CI |
| [`2026-04-28/2258_TESTING.md`](./2026-04-28/2258_TESTING.md) | Vitest + Playwright + Storybook. Auth state via minted JWTs in global-setup. Coverage scoped to `_utils/` + `graphql-client.ts` |
| [`2026-04-28/2258_API-SURFACE.md`](./2026-04-28/2258_API-SURFACE.md) | 496 lines. GraphQL operations (20 Q + 31 M, 0 fragments), NextAuth, refresh-and-rescope workaround, RBAC mock store, MinIO, no real-time |

**Key insights**:

1. **Fully client-rendered despite App Router** — every page is `'use client'` or proxies to `_pages/`. The App Router is structural only; data fetching is SWR+GraphQL on the client.
2. **Three-token auth** — `loginAccessToken` (non-scoped) + `tenantAccessToken` (tenant-scoped) + `accessToken` (active). Refresh tokens lose tenant context (backend bug), so `refreshAndRescope()` re-calls `UserSelectTenant` + `UserSelectBranch` on every refresh.
3. **RBAC v3 is a fully working FE prototype on localStorage** — `computeEffectivePermissions.ts` is real, `mockStore.ts` holds the data. Backend (POPS-228) has a complete design doc in `docs/rbac-backend-design/` but is not yet implemented.
4. **CI only triggers on semver tags + `package.json` change** — no lint/test gate on MRs. Quality gates are local.
5. **No `.env.example`, no `pnpm-lock.yaml`** — install resolves fresh; env config is tribal knowledge plus the README table.
6. **No i18n** — Thai strings hardcoded, `lang="en"` on root is likely a bug.
7. **Bundle size known issue** — 9 of 9 protected routes exceed 250KB gzip; worst is `/setting/admin/user` at 400KB.

## Cross-references

This deep-learn snapshot will be copied into `vet-oracle`'s brain when that PM Oracle is awakened — the Oracle owns this knowledge for its lifetime, refreshing on demand when the codebase evolves.
