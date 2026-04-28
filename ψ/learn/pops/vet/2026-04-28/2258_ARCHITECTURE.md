# POPS Vet — Architecture Reference

**Generated:** 2026-04-28
**Source:** `/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/ψ/learn/pops/vet/origin/`
**Author:** Leica (Oracle)

---

## 1. Project Identity

**POPS Vet** is the veterinary clinic management frontend for the POPS platform — a Thai multi-tenant SaaS product serving veterinary clinics. A single running instance can serve multiple clinics (tenants), each with multiple branches. The UI is in Thai/English mixed.

**Package name:** `pop` (v1.0.1-12)
**Production URL:** `https://pops.vet`
**Backend target (dev):** `https://api-dev.pops.vet`

### Stack Versions

| Dependency | Version | Purpose |
|---|---|---|
| Next.js | ^15.3.9 | Framework (App Router) |
| React | ^19.0.0 | UI runtime |
| TypeScript | ^5 | Language |
| Tailwind CSS | ^3.4.1 | Styling |
| next-auth | ^4.24.13 | Auth session management |
| graphql-request | ^7.2.0 | GraphQL client |
| swr | ^2.3.6 | Data fetching + cache |
| zod | ^4.1.12 | Schema validation |
| react-hook-form | ^7.65.0 | Forms |
| lucide-react | ^0.575.0 | Icons |
| recharts | ^2.15.3 | Charts |
| luxon | ^3.7.2 | Date handling (preferred) |
| moment | ^2.30.1 | Date handling (legacy — being phased out) |
| Vitest | ^4.1.0 | Unit + component tests |
| Playwright | ^1.58.2 | E2E tests |
| Storybook | ^8.6.18 | Component catalogue |

**Backend connection:** Apollo Federation GraphQL gateway at `{NEXT_PUBLIC_POPS_API_URL}/service`. The FE never calls microservices directly — everything goes through the gateway.

---

## 2. Directory Structure

### Top-Level

```
/
├── src/                    # All application source
├── tests/                  # E2E tests (Playwright)
├── docs/                   # Design docs, QA report, perf baseline
├── scripts/                # Seed, cleanup, Lighthouse, bundle check, QA report
├── public/                 # Static assets
├── next.config.ts          # Next.js config
├── tailwind.config.ts      # Tailwind config
├── tsconfig.json           # TypeScript config
├── codegen.ts              # GraphQL codegen config
├── vitest.config.ts        # Vitest config
├── playwright.config.ts    # Playwright config
├── lighthouserc.json       # Lighthouse CI config (public routes)
├── lighthouserc.full.json  # Lighthouse CI config (all routes, needs auth)
├── components.json         # shadcn/ui config
└── Dockerfile
```

### `src/` Structure

```
src/
├── middleware.ts                    # Route protection + RBAC gate
├── app/
│   ├── layout.tsx                   # Root layout — providers, fonts, metadata
│   ├── (auth)/                      # Public route group
│   │   ├── layout.tsx
│   │   ├── login/page.tsx
│   │   └── activate/page.tsx
│   ├── (routes)/                    # Protected route group
│   │   ├── layout.tsx               # Shell: NavBar + SideBar + GlobalContext
│   │   ├── page.tsx                 # Root redirect (→ /dashboard)
│   │   ├── dashboard/page.tsx
│   │   ├── appointment/page.tsx
│   │   ├── queue/page.tsx
│   │   ├── owner-pet/
│   │   │   ├── page.tsx
│   │   │   └── [petId]/page.tsx     # Dynamic pet profile
│   │   ├── veterinarian/
│   │   │   ├── page.tsx
│   │   │   └── [veterinarianId]/page.tsx
│   │   ├── report/
│   │   │   ├── page.tsx
│   │   │   ├── [category]/page.tsx
│   │   │   └── [category]/[reportId]/page.tsx
│   │   ├── setting/admin/
│   │   │   ├── user/page.tsx
│   │   │   ├── roles/page.tsx       # RBAC role management (POPS-226)
│   │   │   └── help/page.tsx
│   │   ├── lab/page.tsx
│   │   ├── ipd/page.tsx
│   │   ├── shop/page.tsx
│   │   └── help/page.tsx
│   ├── api/
│   │   └── auth/
│   │       ├── [...nextauth]/route.ts
│   │       ├── authOptions.ts       # Full NextAuth config
│   │       ├── select-tenant/route.ts
│   │       ├── select-branch/route.ts
│   │       └── branch-list/route.ts
│   ├── _assets/                     # Static-ish shared assets
│   │   ├── lib/
│   │   │   ├── graphql-client.ts    # GraphQLClientManager singleton
│   │   │   ├── graphql-operations.ts # All gql`` strings
│   │   │   ├── swr-config.tsx       # SWRProvider with global config
│   │   │   └── utils.ts             # cn() helper (clsx + tailwind-merge)
│   │   ├── shadcn/ui/               # shadcn/ui components (vendored)
│   │   ├── hooks/use-toast.ts
│   │   ├── icons/svg.tsx
│   │   └── images/index.tsx
│   ├── _components/                 # Feature + shared components
│   │   ├── admin/
│   │   │   ├── rbac/                # RBAC UI (PermissionMatrix, SeatEdit, RolesSidebar)
│   │   │   └── setting/             # User management UI
│   │   ├── appointment/             # Appointment modals + table
│   │   ├── dashboard/               # Dashboard widgets
│   │   ├── login/                   # Login form
│   │   ├── owner-pet/               # Owner + pet CRUD
│   │   ├── pet_profile/             # Pet profile
│   │   ├── providers/               # SessionProviderWrapper, WebVitalsReporter
│   │   ├── queue/                   # Queue management
│   │   ├── reports/                 # Report viewer components
│   │   ├── shared/                  # Reusable: DateOfBirthSelect, GenderSelect, etc.
│   │   ├── veterinarian/            # Vet profile
│   │   ├── NavBar.tsx
│   │   └── SideBar.tsx
│   ├── _config/
│   │   ├── config.ts                # Env-var helpers (getApiUrl, getGraphQLEndpoint)
│   │   └── reports/                 # ~50 report definition files grouped by category
│   ├── _constants/
│   │   ├── rbacFeatures.ts          # SYSTEM_ROLES, FEATURE_CATALOG, default permissions
│   │   ├── rbacFeatureSentences.ts  # Human-readable permission descriptions (Thai)
│   │   ├── enum.ts
│   │   └── __mocks__/               # Mock data for tests
│   ├── _pages/                      # Page-level components (rendered by page.tsx files)
│   ├── _styles/globals.css
│   ├── _types/
│   │   ├── pops.ts                  # Core domain types (Pet, Owner, Vet, Queue, etc.)
│   │   ├── rbac.ts                  # RBAC types (Role, UserSeat, Permission, etc.)
│   │   ├── graphql.ts               # GraphQL response shapes
│   │   ├── state.ts                 # UI state types (ProfileMode, RecordMode)
│   │   └── types.ts
│   └── _utils/
│       ├── context/GlobalContext.tsx  # Global UI state (drawer, modal, loading)
│       ├── hook/                      # SWR data hooks + auth hooks
│       │   ├── userAuth.ts            # Server-safe auth functions (login, refresh, selectTenant)
│       │   ├── useLogin.ts
│       │   ├── useSelectTenant.ts
│       │   ├── useSelectBranch.ts
│       │   ├── useRbac.ts             # useRoles(), useUserSeats()
│       │   ├── pet.ts / owner.ts / vet.ts / appointment.ts / queue.ts / room.ts
│       │   └── userAdmin.ts
│       ├── initGraphQL/initGraphQLClient.ts  # Auth-aware GQL client factory
│       └── rbac/
│           ├── computeEffectivePermissions.ts
│           └── mockStore.ts           # localStorage RBAC store (prototype)
```

### Organizational Philosophy

The project uses **Next.js App Router** with a **feature-based component organization** layered inside `_components/`. The underscore-prefix convention (`_assets`, `_components`, `_pages`, `_utils`, etc.) is a deliberate pattern to keep shared/private directories visually distinct from route segments in the file system.

Key separation:
- Route files (`page.tsx`, `layout.tsx`) are thin shells — they import from `_pages/`
- `_pages/` holds the actual page-level React components
- `_components/` holds feature-specific and shared components
- `_utils/hook/` is the data layer — all SWR hooks live here

---

## 3. Entry Points

### App Router Pages (Protected)

| Route | File |
|---|---|
| `/` (redirects to /dashboard) | `(routes)/page.tsx` |
| `/dashboard` | `(routes)/dashboard/page.tsx` |
| `/appointment` | `(routes)/appointment/page.tsx` |
| `/queue` | `(routes)/queue/page.tsx` |
| `/owner-pet` | `(routes)/owner-pet/page.tsx` |
| `/owner-pet/[petId]` | `(routes)/owner-pet/[petId]/page.tsx` |
| `/veterinarian` | `(routes)/veterinarian/page.tsx` |
| `/veterinarian/[veterinarianId]` | `(routes)/veterinarian/[veterinarianId]/page.tsx` |
| `/report` | `(routes)/report/page.tsx` |
| `/report/[category]` | `(routes)/report/[category]/page.tsx` |
| `/report/[category]/[reportId]` | `(routes)/report/[category]/[reportId]/page.tsx` |
| `/setting/admin/user` | `(routes)/setting/admin/user/page.tsx` |
| `/setting/admin/roles` | `(routes)/setting/admin/roles/page.tsx` |
| `/lab`, `/ipd`, `/shop`, `/help` | `(routes)/*/page.tsx` (placeholders) |

### App Router Pages (Public)

| Route | File |
|---|---|
| `/login` | `(auth)/login/page.tsx` |
| `/activate` | `(auth)/activate/page.tsx` |

### API Routes

| Endpoint | File | Purpose |
|---|---|---|
| `POST /api/auth/[...nextauth]` | `api/auth/[...nextauth]/route.ts` | NextAuth handler |
| `POST /api/auth/select-tenant` | `api/auth/select-tenant/route.ts` | Exchanges login token for tenant-scoped JWT |
| `POST /api/auth/select-branch` | `api/auth/select-branch/route.ts` | Exchanges tenant token for branch-scoped JWT |
| `GET /api/auth/branch-list` | `api/auth/branch-list/route.ts` | Lists branches available to current user |

### Layouts

| File | Role |
|---|---|
| `app/layout.tsx` | Root: `<html>`, fonts, SWRProvider, SessionProvider, WebVitals, `<PublicEnvScript>` |
| `app/(auth)/layout.tsx` | Auth shell (login UI wrapper) |
| `app/(routes)/layout.tsx` | Protected shell: NavBar + SideBar + GlobalContextProvider + Toaster |

### Middleware

`src/middleware.ts` — runs on all routes except `_next/static`, `_next/image`, `favicon.ico`.

Three guards in order:
1. Skip API routes entirely
2. Redirect unauthenticated users to `/login` with `callbackUrl`
3. RBAC gate: `/setting/admin/*` requires `role` in `['clinic-owner', 'admin', 'OWNER', 'ADMIN']`

### Root Config Files

| File | Purpose |
|---|---|
| `next.config.ts` | reactStrictMode, lodash tree-shaking, remote image patterns (minio), bundle analyzer |
| `tailwind.config.ts` | Tailwind config |
| `components.json` | shadcn/ui component registry config |
| `codegen.ts` | GraphQL code generation (not yet wired to auto-generated types — operations defined manually in `graphql-operations.ts`) |
| `vitest.config.ts` | Unit + component test config |
| `playwright.config.ts` | E2E test config (mock mode default; integration mode via `BACKEND_RUNNING`) |
| `lighthouserc.json` | Lighthouse CI — public routes only |
| `lighthouserc.full.json` | Lighthouse CI — all routes (requires `.auth/staff.json` from Playwright global-setup) |
| `tsconfig.json` | TypeScript config with `@/` alias pointing to `src/app/` |

---

## 4. Core Abstractions

### 4.1 Data Fetching

**Pattern:** Client Components + SWR hooks + `graphql-request`

All data fetching is **client-side**. There are no Next.js Server Components doing data fetching. The app is effectively a client-rendered SPA wrapped in Next.js App Router.

The data flow is:
```
Component
  → SWR hook (e.g. usePetList())
    → initGraphQLClient()       # reads NextAuth session token, attaches to header
      → GraphQLClientManager    # singleton graphql-request client
        → GraphQL gateway at {POPS_API_URL}/service
```

Key file: `src/app/_utils/initGraphQL/initGraphQLClient.ts`

```ts
// Client-side: caches token for 30s to avoid session reads on every request
// Server-side (SSR): reads token per-request (no module-level cache)
export const initGraphQLClient = async (requireAuth = true): Promise<GraphQLClient>
```

SWR is configured globally in `src/app/_assets/lib/swr-config.tsx` with `revalidateOnFocus: false` as the default.

All GraphQL operation strings (queries + mutations) live in a single file:
`src/app/_assets/lib/graphql-operations.ts` — organized as a tree: `GraphQLOperations.pets.queries.GET_PET_LISTS`, `GraphQLOperations.auth.user.selectTenant.mutations.USER_SELECT_TENANT`, etc.

### 4.2 State Management

Three layers:

| Layer | Mechanism | Scope |
|---|---|---|
| Server state / cache | SWR | Per-hook, global SWR cache |
| Auth + session | NextAuth (JWT strategy) | App-wide via `SessionProvider` |
| UI state | React Context (`GlobalContext`) | Protected layout — drawer, modal, loading, profileMode |

**`GlobalContext`** (`src/app/_utils/context/GlobalContext.tsx`) is deliberately minimal — it holds UI-only flags like `isOpenDrawer`, `isLoading`, `profileMode`. Split into two contexts (`GlobalContext` + `GlobalContextUpdate`) to prevent unnecessary re-renders when only setters are needed.

Feature-level state (form state, modal open/closed, optimistic updates) is handled locally in components with `react-hook-form` + `useState`.

### 4.3 Authentication Flow

Full implementation: `src/app/api/auth/authOptions.ts`

**Providers:** Credentials (email + password) and Google OAuth.

**Token architecture (three token types in JWT):**

| Token | Purpose |
|---|---|
| `loginAccessToken` | Non-tenant-scoped — used only for `select-tenant` call |
| `tenantAccessToken` | Tenant-scoped — used for all protected API calls |
| `accessToken` | The "active" token — replaced on each tenant/branch selection and refresh |

**Login sequence:**
1. User submits credentials → `CredentialsProvider.authorize()` → GraphQL `UserLogin` mutation
2. JWT callback stores `accessToken`, `refreshToken`, `tenants[]`, `loginAccessToken`, `rememberMe`, `loginAt`
3. User picks clinic (tenant) → `POST /api/auth/select-tenant` → `UserSelectTenant` mutation → tenant-scoped token
4. (Optional) User picks branch → `POST /api/auth/select-branch` → branch-scoped token
5. `session.update()` is called from the client with the new token → JWT callback stores `tenantCode`, `branchId`, `role`
6. All subsequent GraphQL calls use `tenantAccessToken` (read by `initGraphQLClient`)

**Token refresh:**
- Access token TTL: 15 min (decoded from JWT `exp` claim, 60s buffer)
- Refresh token TTL: 30 days (backend)
- Session lifetime: 1 day (no remember) / 30 days (remember)
- On expiry: `refreshAndRescope()` in `authOptions.ts` — refresh token → new access token → re-call `selectTenant` + `selectBranch` (workaround for backend bug where `refresh_tokens` table lacks tenant context)

**Known architectural note:** The backend `UserRefreshToken` mutation returns a non-tenant-scoped token because the `refresh_tokens` table doesn't persist `tenantCode`. The frontend works around this via `refreshAndRescope()`. Backend fix is tracked as Path B in `docs/auth-session-design/`.

**RBAC gate (middleware):** `src/middleware.ts` reads the `role` claim from the NextAuth JWT and blocks non-admin users from `/setting/admin/*`.

### 4.4 RBAC System

**Current state:** Frontend prototype only — backend implementation is in planning (POPS-228).

The RBAC system is fully modeled on the frontend using `localStorage` as a mock backend. The data model and computation logic are production-ready; only the persistence layer (localStorage → backend database) is pending.

**Types:** `src/app/_types/rbac.ts`

Core model:
- `Role` — id, key, name, `Permission[]`, `isSystem` flag, optional `derivedFrom` (for combined roles)
- `Permission` — `feature: FeatureKey`, `actions: CrudAction[]`, optional `extras` (scope, extendedActions, maxAmount)
- `UserSeat` — `userId`, `roleId`, `grants: Permission[]`, `revokes: Permission[]`, `branches: string[]`

13 feature keys across 7 groups: Clinical (owners, pets, medical_records), Operations (queue, appointments), Staff (veterinarians, staff), Inventory, Finance (pos, financial_report), Insights (dashboard), Admin (settings.users, settings.roles).

4 system roles: `vet`, `staff`, `admin`, `clinic-owner` — defined in `src/app/_constants/rbacFeatures.ts`.

**Permission computation** (`src/app/_utils/rbac/computeEffectivePermissions.ts`):
```
effectivePermissions = (role.permissions ∪ seat.grants) − seat.revokes
```
Supports: `can(perms, action, feature)`, `diffPermissions(base, effective)`, `unionPermissions(roles[])`.

**UI components** live in `src/app/_components/admin/rbac/`:
- `PermissionMatrix` / `PermissionMatrixV2` / `PermissionMatrixV3` — versioned iterations
- `SeatEditDrawer` / `SeatEditDrawerV2` / `SeatEditDrawerV3` — user seat editor
- `RolesSidebar`, `CombineRolesModal`, `InviteUserModal`

**Mock store:** `src/app/_utils/rbac/mockStore.ts` — persists to `localStorage` under keys `pops-vet:rbac:*`. Initialized with seed data of 7 Thai users, 3 Bangkok clinic branches (สุขุมวิท, ลาดพร้าว, สีลม), and `SYSTEM_ROLES`.

**Backend design document:** `docs/rbac-backend-design/` — full schema, migration plan, GraphQL API shape. Epic POPS-226, Phase 2 POPS-228.

---

## 5. Dependencies — Categorized

### Framework
- `next` ^15.3.9, `react` ^19.0.0, `react-dom` ^19.0.0, `typescript` ^5

### UI Components
- `@radix-ui/*` (20+ primitives) — base for shadcn/ui
- shadcn/ui components vendored into `src/app/_assets/shadcn/ui/`
- `lucide-react` ^0.575.0 — icons
- `class-variance-authority` + `clsx` + `tailwind-merge` — variant styling
- `lottie-react` — animation (cat paw loading state)
- `embla-carousel-react` — carousel
- `vaul` — drawer primitive
- `cmdk` — command palette
- `input-otp` — OTP input field
- `react-easy-crop` — image crop for avatars
- `@stepperize/react` — multi-step form wizard

### State + Data
- `swr` ^2.3.6 — data fetching cache
- `graphql-request` ^7.2.0 — GraphQL client
- `next-auth` ^4.24.13 — auth session
- `next-runtime-env` ^3.3.0 — runtime env var injection (avoids build-time baking)

### Forms + Validation
- `react-hook-form` ^7.65.0
- `@hookform/resolvers` ^5.2.2
- `zod` ^4.1.12

### Charts + Dates
- `recharts` ^2.15.3
- `luxon` ^3.7.2 (preferred), `moment` ^2.30.1 (legacy, being phased out)

### Fonts
- `@fontsource/ibm-plex-sans-thai` — local font, weights 400/600/700

### Notifications
- `sonner` ^2.0.5, `react-hot-toast` ^2.6.0 (both present — being consolidated)

### Utilities
- `lodash` ^4.17.21 (tree-shaken via `modularizeImports` in `next.config.ts`)
- `js-cookie` + `@types/js-cookie`
- `axios` ^1.11.0 (present but usage appears secondary to graphql-request)

### Testing (devDependencies)
- `vitest` ^4.1.0 + `@testing-library/react` ^16.3.2 + `jsdom` ^28.1.0
- `@playwright/test` ^1.58.2
- `@storybook/react` ^8.6.18 + `@storybook/react-vite`
- `pg` ^8.20.0 — PostgreSQL client (used by seed scripts)

### Build / Quality
- `@next/bundle-analyzer` — via `pnpm build:analyze`
- `@lhci/cli` ^0.15.1 — Lighthouse CI
- `@graphql-codegen/cli` + `@graphql-codegen/client-preset` — type generation (configured but not fully integrated — operations currently hand-typed in `graphql-operations.ts`)
- `storybook` ^8.6.18

### Notable Observations
- **Two date libraries**: `luxon` (new standard) and `moment` (legacy). See `src/app/_utils/ConvertDay.ts` and `date.ts`.
- **Two toast libraries**: `sonner` (shadcn-standard) and `react-hot-toast`. The protected layout uses `react-hot-toast`'s `<Toaster>`.
- **axios** is present but all observed API calls use `graphql-request`. Likely a remnant or used for REST endpoints not yet seen.

---

## 6. Build and Deploy Shape

### Dockerfile

`Dockerfile` at repo root — simple single-stage build (no multi-stage):

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY . .
RUN npm install -g pnpm@10
RUN pnpm install --strict-peer-dependencies=false
RUN pnpm build
EXPOSE 3000
CMD ["pnpm", "start"]
```

**Node version:** 22-slim (upgraded from 18 in v1.0.1-9, from 18→22 in v1.0.1-11).
**Package manager:** pnpm 10.
**Build output:** Standard Next.js `.next/` — not `output: 'standalone'` (no Docker multi-stage optimization).

No `Dockerfile.dev` found. Local development uses `pnpm dev` directly.

### CI/CD

No `.gitlab-ci.yml` found at the path searched. The `CHANGELOG.md` references a GitLab CI pipeline:
> "Release flow: `npm version <patch|minor|major>` → push tag → GitLab CI runs test → build → deploy to pops.vet"

Lighthouse CI is configured to run via `@lhci/cli`:
- `lighthouserc.json` — public route (`/login`) only, desktop preset, 3 runs
- `lighthouserc.full.json` — all routes, requires `scripts/lighthouse-auth.js` to seed a valid `.auth/staff.json` session (blocked on CI integration — POPS-207)

### Environment Variables

| Variable | Side | Purpose |
|---|---|---|
| `NEXT_PUBLIC_POPS_API_URL` | Client + Server | GraphQL gateway base URL |
| `NEXTAUTH_SECRET` | Server | JWT signing secret |
| `NEXT_PUBLIC_POPS_MOCK` | Client | Enable mock mode (no backend) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Server | Google OAuth |
| `NEXT_PUBLIC_WEB_VITALS_ENDPOINT` | Client | Web Vitals beacon destination |
| `NEXT_PUBLIC_WEB_VITALS_DEBUG` | Client | Enable CWV debug logging in production |
| `NEXT_PUBLIC_POPS_VERSION` | Client | Injected from `package.json` version at build |

Client-side env vars use `next-runtime-env` (`env()` + `<PublicEnvScript>`) so they can be injected at container start rather than baked at build time. Server-side uses `process.env` directly.

### Secrets management

Referenced as "Infisical CLI" in code comments (`getApiUrlServer` docstring mentions `docker-entrypoint.sh` + Infisical). No Infisical config files found in the explored paths.

---

## 7. Internal Documentation

The `docs/` directory contains rich, self-contained HTML design documents (no build required — open in browser). There is no `.planning/` directory visible at top-level.

### `docs/auth-session-design/`
Auth session design discussion document. Covers:
- Root causes of "user logs out after 15-60 minutes" bug (5 bugs: B1–B5)
- `refreshAndRescope()` workaround (Path A — already implemented)
- Proposed backend fix: persist `tenant_code/role/branch_id` in `refresh_tokens` (Path B — pending)
- Remember-me 1d/30d implementation
- Test plan T1–T8

Key files: `auth-session-design.html` (technical), `auth-session-explained.html` (learning path), `README.md`.

### `docs/rbac-backend-design/`
RBAC backend schema + API design for POPS-226 / POPS-228. Covers:
- Full ER diagram (roles, tenant_users, grants/revokes, branches, invite_tokens, tenant_logs)
- GraphQL API shape (queries + mutations)
- 5-step migration plan with `RBAC_ENFORCE` feature flag
- 11 open decisions for team sign-off
- Redis cache strategy (TTL 5m, `rbac:effective:{userId}:{tenantId}`)

Key files: `rbac-design.html` (full report), `rbac-explained.html` (learning path), `rbac-diagrams.md` (Mermaid diagrams, GitLab-renderable).

### `docs/qa-report/`
Self-contained HTML QA dashboard. Covers:
- Test pyramid (unit 58% / component 25% / E2E 17%)
- Module × test matrix
- RBAC grid
- Coverage tiers: Critical 95%, Core 85%, UI 70%
- Gaps & Blockers section with 4 tiered groups (Blockers, Schema Gaps, Infrastructure, Planned Modules)

Key files: `qa-report.html`, `data.js` (single source of truth for metrics), `README.md`.
Scanner: `scripts/qa-report/generate.mjs` — auto-updates metrics from live repos.

### `docs/hn-vetcode-design/`
HN (Hospital Number) + Vet Code design — clinic patient ID system.

### `docs/reports-design/`
Reports module design — full report catalog, data pipeline design.

### `docs/performance/BASELINE-2026-04-19.md`
Lighthouse CI baseline captured 2026-04-19 (POPS-206). Key findings:
- `/login` scores 100/100 on Performance, Accessibility, Best Practices; 92/100 SEO
- 9 of 9 protected routes exceed 250KB gzip budget (optimization backlog, non-blocking for soft-launch)
- Web Vitals runtime reporting implemented via `WebVitalsReporter.tsx`

### `docs/testing/`
- `RUNBOOK.md` — testing runbook (environment setup, running tests, mock vs integration mode)
- `SEED-DATA.md` — seed flags, data pools, idempotency
- `TEST-ACCOUNTS.md` — role matrix for E2E test accounts

### `docs/ci-runner-decision/`
Decision document for CI runner choice (self-hosted vs shared).

---

## 8. Multi-Tenancy and RBAC Architecture

### Multi-Tenancy Model

POPS Vet is a **multi-tenant + multi-branch** application.

**Tenant** = one veterinary business / clinic group (e.g. "Happy Paws Clinic"). A tenant has:
- A `tenant_code` (string key in JWT)
- One or more `hospital_branches` (physical locations)

**Auth hierarchy:**
1. Login returns a non-scoped token + `tenants[]` list
2. User selects a tenant → tenant-scoped JWT (`tenantCode` claim in token)
3. (Optional) User selects a branch → branch-scoped JWT (`branchId` + `role` claims)

The same user account can be a member of multiple tenants with different roles per tenant. After tenant selection, all API calls are automatically scoped to that tenant by the JWT claim — the backend gateway enforces this.

**Selected tenant/branch** is stored in the NextAuth JWT (not just a cookie) so it survives page refreshes. The `selected_tenant` cookie is advisory — the middleware uses it only for the OAuth edge case.

### RBAC Model (Current: FE Prototype)

Source: `src/app/_types/rbac.ts`, `src/app/_constants/rbacFeatures.ts`, `src/app/_utils/rbac/`

**Data model:**
```
Role
  id, key, name, isSystem
  permissions: Permission[]   ← feature + CRUD actions + optional extras

UserSeat
  userId, roleId
  grants: Permission[]        ← additive overrides per user
  revokes: Permission[]       ← subtractive overrides per user
  branches: string[]          ← [] means all branches

Permission
  feature: FeatureKey         ← one of 13 features
  actions: CrudAction[]       ← create | read | update | delete
  extras?
    scope: all | branch | assigned | own
    extendedActions: export | print | approve | share | sign | lock
    maxAmount: number | null
```

**System roles:** `vet`, `staff`, `admin`, `clinic-owner` — immutable, seeded at deployment.
**Custom roles:** Created by admins, optionally by combining system roles (`combineRoles()`).

**Effective permission computation** (`computeEffectivePermissions.ts`):
```
effective = (role.permissions ∪ seat.grants) − seat.revokes
```

**Current persistence:** `localStorage` (RBAC mock store). Keys: `pops-vet:rbac:roles:v1`, `pops-vet:rbac:seats:v2`, `pops-vet:rbac:users:v2`, `pops-vet:rbac:branches:v1`.

**Planned persistence:** PostgreSQL via backend GraphQL API (POPS-228, scheduled Q2 2026).

### Middleware RBAC Enforcement

`src/middleware.ts` enforces role checks at the route level for admin pages:

```ts
if (token && pathname.startsWith('/setting/admin')) {
  const adminRoles = ['clinic-owner', 'admin', 'OWNER', 'ADMIN'];
  if (!role || !adminRoles.includes(role)) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }
}
```

`role` is decoded from the `tenantAccessToken` JWT payload in the `session` callback of `authOptions.ts` (per design decision D-14 referenced in code comments).

### Backend RBAC Integration Plan (POPS-228)

Full design: `docs/rbac-backend-design/rbac-diagrams.md`

5-step migration gated by `RBAC_ENFORCE` feature flag:
1. Additive schema (roles table, alter tenant_users) — flag OFF
2. Backfill + role_id FK cutover
3. Read API (GraphQL queries, FE cutover POPS-229)
4. Enforcement on — 403 ForbiddenException, Redis cache live
5. Cleanup — drop legacy `role` STRING column

Redis cache key: `rbac:effective:{userId}:{tenantId}` (TTL 5m). Invalidated on: role update, seat update, branch change, deactivate/reactivate.

---

## 9. Module Completion Status

| Module | Status | Notes |
|---|---|---|
| Patient / Pet | 90% | Core CRUD working |
| Owner / Parent | 90% | Core CRUD working |
| Queue | 85% | Functional |
| Appointments | 80% | Functional |
| Dashboard | 75% | Partial data |
| Veterinarian / Staff | 75% | Partial |
| Auth | 70% | Backend integrated |
| RBAC / Admin | 60% | FE prototype shipped (POPS-230), backend pending (POPS-228) |
| User Profile | 70% | API integrated |
| Reports | 25% | Report catalog defined (~50 report configs), viewer placeholder |
| Notifications | 30% | Toast only |
| Settings | 30% | Placeholder |
| Medical Records | 0% | Backend API needed |
| Billing / POS | 0% | Not started |
| Lab / IPD / Shop | ~10% | Placeholder pages only |

---

## 10. Key File Reference

| Purpose | File |
|---|---|
| NextAuth full config | `src/app/api/auth/authOptions.ts` |
| Route protection middleware | `src/middleware.ts` |
| GraphQL client singleton | `src/app/_assets/lib/graphql-client.ts` |
| Auth-aware GQL client factory | `src/app/_utils/initGraphQL/initGraphQLClient.ts` |
| All GraphQL operation strings | `src/app/_assets/lib/graphql-operations.ts` |
| Auth functions (server-safe) | `src/app/_utils/hook/userAuth.ts` |
| Environment config helpers | `src/app/_config/config.ts` |
| Global UI state context | `src/app/_utils/context/GlobalContext.tsx` |
| RBAC type definitions | `src/app/_types/rbac.ts` |
| RBAC system roles + features | `src/app/_constants/rbacFeatures.ts` |
| RBAC computation logic | `src/app/_utils/rbac/computeEffectivePermissions.ts` |
| RBAC hooks (useRoles, useUserSeats) | `src/app/_utils/hook/useRbac.ts` |
| RBAC mock store (localStorage) | `src/app/_utils/rbac/mockStore.ts` |
| Next.js config | `next.config.ts` |
| Dockerfile | `Dockerfile` |
| Auth session design doc | `docs/auth-session-design/README.md` |
| RBAC backend design doc | `docs/rbac-backend-design/README.md` |
| QA dashboard | `docs/qa-report/qa-report.html` |
| Performance baseline | `docs/performance/BASELINE-2026-04-19.md` |
| Testing runbook | `docs/testing/RUNBOOK.md` |
