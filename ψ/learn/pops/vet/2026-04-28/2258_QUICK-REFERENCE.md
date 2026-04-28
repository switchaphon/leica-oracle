# POPS Vet — Quick Reference

> Generated: 2026-04-28 22:58 | Source: `app/vet` @ commit `60e5334`

---

## 1. What This Is

**POPS Vet** is the Thai veterinary clinic management frontend for the POPS platform (`pops.vet`). It is a multi-tenant SaaS used by veterinary clinics — the primary users are vets, vet techs, clinic receptionists, and clinic owners/admins. It solves the day-to-day clinic workflow: patient (pet/owner) management, queue, appointments, veterinarian scheduling, basic reporting, and role-based access control across clinic branches.

The frontend is a Next.js 15 App Router application that connects to a NestJS microservices backend via an Apollo Federation GraphQL gateway.

---

## 2. Tech Stack

| Category | Library | Version |
|---|---|---|
| Framework | Next.js (App Router) | ^15.3.9 |
| Language | TypeScript | ^5 |
| Runtime (React) | React / React DOM | ^19.0.0 |
| Styling | Tailwind CSS | ^3.4.1 |
| Component lib | Shadcn/UI (Radix primitives) | — |
| Radix UI | @radix-ui/* (accordion, dialog, select, etc.) | ^1–2 per pkg |
| State / data cache | SWR | ^2.3.6 |
| Auth | NextAuth.js | ^4.24.13 |
| Forms | react-hook-form + zod | ^7.65.0 / ^4.1.12 |
| GraphQL client | graphql-request | ^7.2.0 |
| GraphQL codegen | @graphql-codegen/cli + client-preset | ^6.2.1 / ^5.2.4 |
| Icons | lucide-react | ^0.575.0 |
| Charts | recharts | ^2.15.3 |
| Date utilities | luxon (primary), moment (legacy) | ^3.7.2 / ^2.30.1 |
| Animations | lottie-react | ^2.4.1 |
| Font | @fontsource/ibm-plex-sans-thai | ^5.2.6 |
| Unit testing | Vitest + @testing-library/react | ^4.1.0 / ^16.3.2 |
| E2E testing | Playwright | ^1.58.2 |
| Component docs | Storybook | ^8.6.18 |
| Performance | @lhci/cli (Lighthouse CI) | ^0.15.1 |
| Bundle analysis | @next/bundle-analyzer | ^16.1.6 |
| Linting | ESLint 9 + eslint-config-next | ^9 / ^15.3.9 |
| Formatting | Prettier | ^3.8.1 |
| Changelog | git-cliff | (npx, not pinned) |

---

## 3. Setup Commands

```bash
# 1. Install (pnpm — no lock file committed, README specifies pnpm)
pnpm install

# 2. Environment — no .env.example exists; set these manually:
cp /dev/null .env.local
# Required vars — see section 5 for full list

# 3. GraphQL codegen (gateway must be reachable, or set NEXT_PUBLIC_POPS_API_URL)
pnpm codegen

# 4. Dev server
pnpm dev          # http://localhost:3000

# 5. Unit tests
pnpm test         # all Vitest tests (unit + component + integration)
pnpm test:unit    # src/__tests__/unit only
pnpm test:component
pnpm test:integration

# 6. E2E tests (mock mode — no backend needed)
pnpm test:e2e

# 7. E2E integration (real backend at api-dev)
pnpm e2e:integration

# 8. Storybook
pnpm storybook    # http://localhost:6006

# 9. Production build
pnpm build
pnpm start
```

> No lock file is checked in. `pnpm install` will resolve fresh from the registry. If you see phantom peer warnings, check the pnpm version matches Node 22 (used in Dockerfile).

---

## 4. Key Scripts

| Script | What it does | When to use |
|---|---|---|
| `dev` | Next.js dev server (port 3000) | Daily development |
| `build` | Production Next.js build | Pre-deploy / CI |
| `build:analyze` | Build + Webpack Bundle Analyzer (`ANALYZE=true`) | Investigating bundle bloat |
| `start` | Serve production build | After `build` locally |
| `lint` | ESLint with next/core-web-vitals + typescript rules | Pre-commit / CI |
| `changelog` | Regenerate full CHANGELOG.md via git-cliff | Before cutting a release |
| `changelog:unreleased` | Prepend unreleased entries to CHANGELOG.md | Sprint closing |
| `test` | Run all Vitest tests | General test run |
| `test:unit` | Vitest — unit tests only | Fast inner loop |
| `test:component` | Vitest — component tests | Component work |
| `test:integration` | Vitest — integration tests | API contract checks |
| `test:watch` | Vitest watch mode | TDD |
| `test:coverage` | Vitest + V8 coverage report | Coverage audit |
| `test:e2e` | Playwright in mock mode | Feature development |
| `test:e2e:ui` | Playwright UI mode | Debugging E2E |
| `test:e2e:headed` | Playwright headed (browser visible) | Visual debugging |
| `codegen` | GraphQL codegen — generates `src/__generated__/` | After any `.graphql` or query change |
| `codegen:watch` | Codegen in watch mode | GraphQL development |
| `storybook` | Start Storybook on port 6006 | Component design |
| `build-storybook` | Static Storybook build | Deploying docs |
| `seed:test` | Seed E2E test data (`tests/e2e/helpers/seed.ts`) | Before E2E integration run |
| `seed:dev` | Seed dev tenant with complete fixture data | New dev environment setup |
| `seed:cleanup` | Dry-run sweep of E2E artifacts | Cleanup after integration E2E |
| `lhci` | Lighthouse CI autorun (standard budget) | Performance gate |
| `lhci:full` | Lighthouse CI with full budget config | Pre-release perf check |
| `check:bundle-size` | Node script checks bundle size limits | CI gate |
| `perf:baseline` | build + bundle-size + lhci chained | Full perf baseline snapshot |
| `qa:report` | Scan repos and dry-run QA dashboard data update | Audit current test counts |
| `qa:report:write` | Scan + write updated data.js to qa dashboard | After significant test changes |
| `qa:report:open` | Open `docs/qa-report/qa-report.html` | Review QA status |
| `qa:report:refresh` | scan + write + open in one shot | Quick QA check |

---

## 5. Environment Variables

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `NEXT_PUBLIC_POPS_API_URL` | Yes | GraphQL gateway base URL. Used in codegen (`/service` endpoint) and at runtime | `https://api-dev.pops.vet` |
| `NEXTAUTH_SECRET` | Yes | JWT signing secret for NextAuth (min 32 chars) | `some-long-random-string-here` |
| `NEXTAUTH_URL` | Prod only | Canonical URL for NextAuth callbacks | `https://pops.vet` |
| `NEXT_PUBLIC_POPS_MOCK` | No | `true` enables mock data mode (no backend required) | `true` |
| `NEXT_PUBLIC_REPORTS_MOCK` | No | `true` enables mock data for the Reports module specifically | `true` |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID (Google login flow) | `...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret | `GOCSPX-...` |
| `NEXT_PUBLIC_WEB_VITALS_DEBUG` | No | `true` enables client-side Web Vitals console output | `true` |
| `NEXT_PUBLIC_WEB_VITALS_ENDPOINT` | No | Endpoint to POST Core Web Vitals metrics | `https://metrics.pops.vet/vitals` |
| `NODE_ENV` | Auto | Set by Next.js. Drives `removeConsole` in production builds. | `development` / `production` |
| `ANALYZE` | No | Set to `true` to enable bundle analyzer during `build` | `true` |

> No `.env.example` or `.env.mock` file exists in the repo. The README references `.env.mock` as a guide — it may have been removed. Use the table above as your reference.

---

## 6. Project Structure Cheat Sheet

```
src/
  app/
    (auth)/              # Public routes (no auth required)
      login/             # /login page
      activate/          # /activate?token= (email activation)
    (routes)/            # Protected routes (middleware enforces auth)
      dashboard/         # /dashboard
      queue/             # /queue
      appointment/       # /appointment
      owner-pet/         # /owner-pet + /owner-pet/[petId]
      veterinarian/      # /veterinarian
      report/            # /report
      setting/           # /setting (admin: /setting/admin/*)
      ipd/               # /ipd (inpatient)
      lab/               # /lab
      shop/              # /shop
      help/              # /help
    api/
      auth/              # NextAuth API routes ([...nextauth])
    _pages/              # Page-level components (rendered by page.tsx files)
    _components/         # Shared UI components and layout
      providers/         # Context providers (Auth, Theme, WebVitals, etc.)
    _assets/
      shadcn/ui/         # Shadcn/UI component library (Radix + Tailwind)
      lib/
        graphql-client.ts     # GraphQLClientManager singleton
        graphql-operations.ts # All GQL queries/mutations (centralized)
    _utils/
      hook/              # SWR data hooks (pet.ts, owner.ts, appointment.ts, queue.ts, vet.ts, etc.)
      initGraphQL/       # initGraphQLClient.ts — token injection, SSR/client split
      rbac/              # computeEffectivePermissions.ts, mockStore.ts
      context/           # React context (auth, tenant, etc.)
      admin/             # Admin-specific utilities
    _types/              # TypeScript types (rbac.ts, graphql.ts, etc.)
    _constants/          # rbacFeatures.ts (feature catalog, system roles), etc.
    _config/             # config.ts — getGraphQLEndpoint() and other runtime config
    _styles/             # Global CSS
    interfaces/          # Shared interface types
  __generated__/         # Auto-generated GraphQL types (DO NOT EDIT — run codegen)
  __tests__/
    unit/                # Unit tests
    component/           # Component integration tests
    integration/         # Integration tests
  test/
    setup.ts             # Vitest global setup (@testing-library/jest-dom, etc.)
  types/                 # Global type declarations (next-auth.d.ts, etc.)
tests/
  e2e/                   # Playwright E2E tests
    helpers/             # seed.ts and test utilities
    global-setup.ts      # Playwright global setup (seeds .env.test)
    global-teardown.ts
docs/
  testing/RUNBOOK.md     # Full environment setup + troubleshooting
  rbac-backend-design/   # RBAC design docs + diagrams
  qa-report/             # Self-contained HTML QA dashboard
scripts/
  check-bundle-size.js   # CI bundle size check
  qa-report/generate.mjs # QA dashboard scanner
  seed-dev-tenant.ts     # Dev data seeder
```

**Where to go for common tasks:**

| Task | Location |
|---|---|
| Add a new page/route | `src/app/(routes)/<name>/page.tsx` + `_pages/<name>/` |
| Add a public page | `src/app/(auth)/<name>/page.tsx` |
| Add a GraphQL query or mutation | `src/app/_assets/lib/graphql-operations.ts` (centralized) |
| Regenerate GQL types | Run `pnpm codegen` → edits `src/__generated__/` |
| Add a shared component | `src/app/_components/` |
| Add a Shadcn/UI primitive | `src/app/_assets/shadcn/ui/` |
| Add a data hook (SWR) | `src/app/_utils/hook/` |
| Add a permission / feature | `src/app/_constants/rbacFeatures.ts` — add entry to `FEATURE_CATALOG` |
| Add a system role | `src/app/_constants/rbacFeatures.ts` — add to `SYSTEM_ROLES` |
| Add a translation / Thai label | Thai labels live inline in `FEATURE_CATALOG` and component files (no i18n framework — strings are hardcoded in Thai/English) |
| Change auth logic | `src/app/api/auth/authOptions.ts` + `src/middleware.ts` |
| Change GraphQL endpoint | `src/app/_config/config.ts` |

---

## 7. Conventions

### Code style (Prettier)
- Single quotes (`singleQuote: true`)
- Semicolons on (`semi: true`)
- 2-space indentation, no tabs
- Trailing commas everywhere (`trailingComma: "all"`)
- Print width 80
- JSX: single quotes (`jsxSingleQuote: true`)
- LF line endings

### ESLint
- Extends `next/core-web-vitals` + `next/typescript`
- `@typescript-eslint/no-explicit-any` is a **warning** (not error) — pre-existing `any` usage is being progressively typed
- `@typescript-eslint/no-unused-vars` is off

### Naming patterns
- Files: `camelCase.ts` / `PascalCase.tsx` for React components
- Route segments: lowercase kebab (`owner-pet/`, `setting/`)
- Internal directories prefixed with `_` (`_pages/`, `_utils/`, `_assets/`)
- GraphQL types: `snake_case` fields (codegen `namingConvention: 'keep'` — matches backend)
- Hooks: `use<Name>.ts` in `_utils/hook/`
- RBAC feature keys: `snake_case` strings (e.g., `'medical_records'`, `'settings.users'`)
- Tests: `*.test.ts` / `*.test.tsx` under `src/__tests__/`

### Path aliases (tsconfig)
```
@/_assets/*   → src/app/_assets/*
@/_components/*  → src/app/_components/*
@/_pages/*    → src/app/_pages/*
@/_constants/* → src/app/_constants/*
@/_utils/*    → src/app/_utils/*
@/_types/*    → src/app/_types/*
@/_config/*   → src/app/_config/*
@/_styles/*   → src/app/_styles/*
```

---

## 8. Common Gotchas

**GraphQL codegen requires a running gateway.**
`pnpm codegen` hits `$NEXT_PUBLIC_POPS_API_URL/service` for introspection. If the gateway is down, codegen fails. Use `https://api-dev.pops.vet` (set in env) or export the SDL from the gateway and reference it as a local file in `codegen.ts`.

**GraphQLClientManager is client-side only.**
`graphql-client.ts` is marked `'use client'` and throws on SSR. All data fetching goes through SWR hooks in Client Components. Do not attempt to call `graphQLClientManager.getClient()` from Server Components or Route Handlers.

**Token cache TTL = 30 seconds.**
`initGraphQLClient.ts` caches the session token for 30s on the client. After a tenant switch or token refresh, there is up to a 30s window where the old token may be used. Call `clearGraphQLTokenCache()` explicitly after login/logout.

**Multi-tenant flow: two tokens.**
Login gives a user-scoped `accessToken`. The user then selects a clinic → `UserSelectTenant` mutation returns a `tenantAccessToken`. Both are stored in the NextAuth JWT. All protected API calls use `tenantAccessToken`. If `selected_tenant` cookie is absent, the middleware allows `/login` even for authenticated sessions (tenant selection step).

**Admin routes are RBAC-guarded at middleware level.**
`/setting/admin/*` redirects to `/dashboard` for any role not in `['clinic-owner', 'admin', 'OWNER', 'ADMIN']`. This is a hard middleware guard — the RBAC system in `_utils/rbac/` is a frontend prototype using `localStorage` (`mockStore.ts`); the real backend RBAC is a separate design.

**RBAC mockStore is localStorage-only.**
`useRoles`, `useUserSeats` in `useRbac.ts` read/write from `localStorage` via `mockStore.ts`. This is a prototype — it resets on `resetMockStore()`. The backend RBAC (POPS-104 design) has a different shape. Do not treat the mock as canonical.

**`luxon` is preferred, `moment` is legacy.**
Both are in dependencies. Use `luxon` for new date logic. `moment` is kept for existing code and will be progressively removed.

**No i18n framework.**
There is no `next-intl`, `i18next`, or similar. Thai strings are hardcoded inline. Adding a new locale requires manually updating every string in every component.

**`console.*` calls are stripped in production.**
`next.config.ts` sets `compiler.removeConsole: true` for `NODE_ENV=production`. Debug logs won't appear in prod builds.

**`lodash` is modularized.**
`next.config.ts` uses `modularizeImports` for lodash. Import individual methods (`import get from 'lodash/get'`) — do not import the whole library (`import _ from 'lodash'`).

**Playwright E2E loads `.env.test`.**
`playwright.config.ts` calls `process.loadEnvFile('.env.test')`. This file is not committed. Create it locally with at minimum `NEXTAUTH_SECRET=<same-as-.env.local>` before running E2E.

**Coverage thresholds are enforced.**
Vitest coverage: lines 70%, statements 70%, functions 60%, branches 60%. CI will fail if coverage drops below these. Thin GraphQL hook wrappers are intentionally excluded from coverage.

---

## 9. CI/CD

Platform: **GitLab CI** (`.gitlab-ci.yml`)

Stages: `test → build → deploy`

**Trigger:** All three stages run only when:
1. A git tag matching `v<major>.<minor>.<patch>(-<build>)?` is pushed (e.g., `v1.0.1-12`)
2. AND `package.json` has changed in that commit

| Stage | Job | What it does |
|---|---|---|
| test | `test-image` | SonarQube scan (currently echoed/skipped) |
| build | `build-image` | Docker buildx build with local layer cache → push to registry. Image tag: `frontend-$CI_COMMIT_TAG` |
| deploy | `deploy-image` | Triggers downstream deployment pipeline at `pops/deploy/deployment` |

Runner tag: `pops-build` (self-hosted runner).

**Release flow** (from CHANGELOG):
```bash
npm version <patch|minor|major>   # bumps package.json + creates git tag
git push --follow-tags             # triggers CI
```

No CI jobs run on feature branch pushes or MRs. There is no automated lint/test gate in CI — those are expected to be run locally before tagging.

**Docker:** `Dockerfile` at root. Node 22 + pnpm 10. Image pushed to private registry.

---

## 10. Where to Ask / Team Workflow

**Ticket prefix:** `POPS-XXX` (seen throughout git log, commit messages, branch names like `feat/POPS-236`)

**Branch convention:** `feat/POPS-<number>` — feature branches are merged into the main integration branch

**Team docs in `.claude/`:**
- `.claude/CLAUDE.md` — project-specific Claude Code instructions
- `.claude/PLAYBOOK.md` — development playbook
- `.claude/JIRA_WORKFLOW.md` — Jira ticket workflow
- `.claude/agents/` — specialized AI agent configs (code-reviewer, qa-tester, security-auditor)

**Key documentation:**
- `docs/testing/RUNBOOK.md` — full environment setup, E2E scenarios, troubleshooting
- `docs/testing/TEST-ACCOUNTS.md` — test user credentials
- `docs/testing/SEED-DATA.md` — seed data documentation
- `docs/rbac-backend-design/rbac-design.html` — RBAC architecture (interactive HTML)
- `docs/qa-report/qa-report.html` — QA dashboard (open directly in browser)

**Module completion status** (as of last README update):

| Module | Status |
|---|---|
| Patient / Pet, Owner | 90% |
| Queue | 85% |
| Appointments | 80% |
| Dashboard, Vet/Staff | 75% |
| Auth, User Profile | 70% |
| Notifications, Settings | 30% |
| Reports | 25% |
| Medical Records, Billing | 0% |
