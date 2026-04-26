# VetsHub — Architecture Document

**Generated:** 2026-04-26  
**Version:** 1.5.1  
**Repo:** `/Users/switchaphon/_POPs_/vets-hub`  
**Description:** National veterinary clinic annual health-reporting platform for กรมปศุสัตว์ (Department of Livestock Development), Thailand. Digitizes สสป. (สถิติสัตว์ป่วย) Excel submissions from ~3,000 vet clinics into a web application with real-time dashboards and geospatial analytics.

---

## 1. Monorepo Structure

```
vets-hub/                          # Turborepo root (pnpm workspaces)
├── apps/
│   ├── web/                       # @vets-hub/web — Next.js 15 frontend
│   └── api/                       # @vets-hub/api — NestJS 10 backend
├── packages/
│   ├── shared/                    # @vets-hub/shared — Types, constants, validation, utils
│   └── db/                        # @vets-hub/db — Prisma client + schema + seed scripts
├── docs/
│   ├── specs/                     # 13 technical spec files
│   ├── examples/                  # Sample สสป. Excel files
│   ├── manuals/, roadmaps/, ideas/
│   └── API.md, MANUAL.md, DB-SEED_MANUAL.md
├── scripts/
│   ├── generate-district-geojson.ts
│   └── split-district-geojson.ts
├── tokens/
│   ├── figma-tokens.json
│   └── components-preview.html
├── PRPs/                          # Product Requirement Plans (active + archived)
├── turbo.json                     # Turborepo pipeline
├── pnpm-workspace.yaml            # pnpm workspace roots: apps/*, packages/*
├── package.json                   # Root (version 1.1.0, Node >=20, pnpm 9.15.0)
├── docker-compose.yml             # Local dev: postgres:16-alpine + api service
├── render.yaml                    # Render.com deployment config (api only)
├── .vercel/project.json           # Vercel project ID prj_KnBMEJoMjYGMnuZdN5GWkXGYBcEH
├── .env.example / .env.production.example
└── tsconfig.json                  # Root TypeScript config
```

---

## 2. Apps

### 2.1 `apps/web` — `@vets-hub/web`

**What it is:** Next.js 15 App Router frontend. Public-facing dashboard, clinic portal for submitting annual health reports, and admin officer panel. Version: 1.5.1. Runs on port 3000.

**Framework & Key Dependencies:**

| Concern | Library |
|---|---|
| Framework | Next.js 15 (`^15.1.0`), React 19 |
| Language | TypeScript 5.7 (strict) |
| Styling | Tailwind CSS 3.4, `tailwind-merge`, `tailwindcss-animate` |
| UI components | shadcn/ui (Radix UI primitives — 20+ components) |
| Forms | React Hook Form 7.54 + `@hookform/resolvers` + Zod 3.24 |
| GraphQL client | Apollo Client (via `@apollo/client`) |
| REST client | SWR 2.3 |
| Charts | Recharts 2.15 |
| Maps | Mapbox GL JS 3.9 + `react-map-gl` 7.1 |
| Auth | NextAuth.js v5 beta (`next-auth@^5.0.0-beta.25`) |
| Excel parsing | SheetJS (`xlsx@^0.18.5`) |
| Toast | Sonner 1.7 |
| Font | Noto Sans Thai (Google Fonts via `next/font`) |
| Unit tests | Vitest 2.1 + React Testing Library 16 + MSW 2.7 |
| E2E tests | Playwright 1.49 |

**Entry Points:**

- `apps/web/app/layout.tsx` — Root layout (font, providers)
- `apps/web/app/page.tsx` — Root redirect (→ `/dashboard` or `/clinic`)
- `apps/web/lib/apollo-client.ts` — Apollo Client singleton
- `apps/web/lib/auth.ts` — NextAuth configuration
- `apps/web/vitest.config.ts` — Vitest configuration
- `apps/web/playwright.config.ts` — Playwright configuration (3 projects: chromium, mobile-chrome 375px, tablet-chrome 768px)

**Route Groups & Pages (Next.js App Router):**

```
apps/web/app/
├── layout.tsx                          # Root layout
├── page.tsx                            # Root (redirect)
├── components-showcase/page.tsx        # Dev: component gallery
│
├── (auth)/                             # Unauthenticated layout
│   ├── layout.tsx
│   ├── login/page.tsx                  # /login
│   └── register/page.tsx              # /register
│
├── (public)/                           # No-auth public routes
│   └── dashboard/page.tsx             # /dashboard — Public choropleth map + KPI cards
│
├── (portal)/                           # JWT-authenticated clinic routes
│   ├── layout.tsx                      # Portal layout (sidebar + overdue banner)
│   ├── clinic/
│   │   ├── page.tsx                    # /clinic — Clinic picker list
│   │   └── [id]/
│   │       ├── page.tsx                # /clinic/[id] — MAIN HUB: year nav + 12-month calendar
│   │       └── report/
│   │           ├── page.tsx            # Redirect shim → /clinic/[id]
│   │           └── [year]/
│   │               ├── page.tsx        # Redirect shim → /clinic/[id]?year=
│   │               ├── full/           # Full-year สสป. wizard (card deck mode)
│   │               └── [month]/        # Month mode chooser (daily | summary)
│   │                   └── day/[date]  # Single-day entry form
│   ├── daily/                          # Legacy daily entry routes (pre-v1.0.2)
│   │   ├── page.tsx
│   │   ├── [msId]/[date]/page.tsx
│   │   └── review/[monthlySubmissionId]/page.tsx
│   ├── submit/page.tsx                 # /submit — Original full-year wizard
│   ├── history/page.tsx               # /history — Submission history & status
│   └── reports/page.tsx               # /reports — Clinic's own analytics
│
└── (admin)/                            # SUPER_ADMIN role-guarded routes
    ├── layout.tsx                      # Admin layout (sidebar + breadcrumbs)
    ├── admin/
    │   ├── dashboard/page.tsx          # /admin/dashboard — Command Center (10 modules)
    │   ├── clinics/
    │   │   ├── page.tsx               # /admin/clinics — Clinic list (REST + Bearer auth)
    │   │   ├── [id]/page.tsx          # /admin/clinics/[id]
    │   │   └── new/page.tsx           # /admin/clinics/new
    │   ├── submissions/page.tsx        # /admin/submissions — Read-only submission log
    │   ├── import/page.tsx            # /admin/import — Excel bulk import stepper
    │   ├── monthly-log/page.tsx       # /admin/monthly-log — ประวัติการส่งรายงาน
    │   ├── users/
    │   │   ├── page.tsx               # /admin/users — User management
    │   │   └── new/page.tsx
    │   └── audit-logs/page.tsx        # /admin/audit-logs — Audit log viewer
```

**Key Component Directories:**

```
apps/web/components/
├── ui/                         # shadcn/ui components (20+: Button, Card, Table, Dialog, etc.)
├── forms/
│   ├── UnifiedEntryForm.tsx    # Single form: daily + monthly entry (สสป.1-4)
│   ├── CollapsibleSummary.tsx  # Collapsible section totals
│   ├── CardDeckWizard.tsx      # Card-based full-year wizard
│   └── unified-entry-helpers.ts
├── daily/
│   ├── AppendModeTable.tsx     # Tap-to-increment UI
│   ├── DailyAnimalCount.tsx
│   ├── InlineEntryModal.tsx    # 3 modes: daily / monthly / batch-daily
│   ├── MonthlyReviewPanel.tsx  # Day-by-day month table
│   ├── SubmitConfirmDialog.tsx
│   └── UnfilledDaysPopup.tsx
├── charts/                     # Dashboard chart components
├── maps/                       # Mapbox GL JS map components
├── dashboard/
│   └── ChartCard.tsx           # Chart wrapper (tooltip, expand modal, inline legend)
├── loading/                    # Skeleton loaders
└── layout/                     # Navigation, sidebar (overdue badge), ClinicBreadcrumb
```

**Key Hooks (`apps/web/lib/hooks/`):**

- `useDailyEntries` — Daily entry CRUD with SWR
- `useAutoSave` — Debounced 500ms Apollo mutation auto-save
- `useReportQuery` — Stabilized Apollo query (dep array via `useMemo` + sorted JSON)
- `useDistrictGeoJSON` — Mapbox GeoJSON loader
- `useAnnualSubmitFlow` — Full-year submission state machine
- `useMonthlySubmitFlow` — Monthly submission lifecycle

**Test Structure:**

```
apps/web/__tests__/
├── unit/       # 85 Vitest + RTL component unit tests
├── integration/ # 1 page-level integration test
└── e2e/        # 13 Playwright spec files (126 tests)
    └── responsive-layout.spec.ts  # @responsive tag, runs on mobile-chrome + tablet-chrome
```

---

### 2.2 `apps/api` — `@vets-hub/api`

**What it is:** NestJS 10 backend. Serves GraphQL (primary, code-first) and REST v1 (third-party adapter). Runs on port 4000. Deployed to Render.com via Docker.

**Framework & Key Dependencies:**

| Concern | Library |
|---|---|
| Framework | NestJS 10 |
| Language | TypeScript 5.7 (strict) |
| Primary API | GraphQL code-first (`@nestjs/graphql` + Apollo Server) |
| REST API | NestJS controllers under `/api/v1/` |
| ORM | Prisma 6 (client via `@vets-hub/db`) |
| Auth | JWT (`@nestjs/jwt`, `@nestjs/passport`, `passport-jwt`) + bcrypt |
| Validation | `class-validator` + `class-transformer` + Zod |
| API docs | `@nestjs/swagger` + `swagger-ui-express` (OpenAPI 3.0) |
| Rate limiting | `@nestjs/throttler` (100 req/min global) |
| Cache | `@nestjs/cache-manager` (5-min TTL, 200 items in-memory) |
| Security | `helmet` |
| Unit tests | Jest 29 + `@nestjs/testing` |
| E2E tests | Jest + Supertest |

**Entry Point:** `apps/api/src/main.ts`
- Binds port 4000 (env `PORT`)
- Enables URI versioning (`/api/v{n}/`)
- Sets global `ValidationPipe`, `AllExceptionsFilter`
- Enables Swagger when `NODE_ENV !== 'production'` OR `ENABLE_SWAGGER=true`
- CORS: comma-separated `FRONTEND_URL` env var
- Body parser limit: 10 MB (for base64 feedback images)
- `trust proxy`: true (behind Render reverse proxy)

**NestJS Module Tree:**

```
AppModule
├── ConfigModule (global, reads ../../.env)
├── ThrottlerModule (100 req/min)
├── CacheModule (global, 5 min TTL)
├── PrismaModule            → PrismaService (wraps @vets-hub/db PrismaClient)
├── AuthModule              → /api/v1/auth — login, register; /graphql mutations
├── ClinicsModule           → /api/v1/clinics + GraphQL resolvers
├── SubmissionsModule       → /api/v1/submissions + GraphQL resolvers
├── DailyEntriesModule      → /api/v1/daily-entries (22 endpoints)
│   └── external.controller → /api/v1/external (8 endpoints — third-party API)
├── ReportsModule           → /api/v1/reports (40+ endpoints)
│   ├── DashboardReportsService
│   ├── AnalyticsReportsService
│   ├── GeographyReportsService
│   ├── VaccinationReportsService
│   ├── SurveillanceReportsService
│   └── SurgicalReportsService
├── AdminModule             → /api/v1/admin
│   └── ImportService (Excel parsing)
├── ApiKeysModule           → /api/v1/api-keys
├── ReferenceModule         → /api/v1/reference (vaccines, diseases, procedures)
├── FeedbackModule          → /api/v1/feedback
└── AuditModule             → AuditService (write-only, no controller)
```

**REST API Surface:**

| Prefix | Controller | Endpoints | Auth |
|---|---|---|---|
| `/api/v1/auth` | AuthController | login, register, me | Public / JWT |
| `/api/v1/clinics` | ClinicsController | CRUD, link clinic | JWT + ownership guard |
| `/api/v1/submissions` | SubmissionsController | create-draft, auto-save, submit | JWT |
| `/api/v1/daily-entries` | DailyEntriesController | 22 endpoints (upsert, batch, submit-month, overdue) | JWT + ClinicMembershipGuard |
| `/api/v1/external` | ExternalController | 8 endpoints for clinic software push | API Key (`X-API-Key`) |
| `/api/v1/reports` | ReportsController | 40+ analytics endpoints | Public (read) / JWT (admin) |
| `/api/v1/admin` | AdminController | user mgmt, import | JWT + SUPER_ADMIN |
| `/api/v1/api-keys` | ApiKeysController | generate, list, revoke | JWT + SUPER_ADMIN |
| `/api/v1/reference` | ReferenceController | vaccines, diseases, procedures | Public |
| `/api/v1/feedback` | FeedbackController | submit feedback report | Public |
| `/graphql` | GraphQL (Apollo) | All primary data operations | JWT |
| `/api/docs` | Swagger UI | OpenAPI 3.0 spec | Public (enabled in prod via env) |

**Common Infrastructure (`apps/api/src/common/`):**

- `guards/roles.guard.ts` — `@Roles(UserRole.SUPER_ADMIN)` decorator guard
- `guards/api-key.guard.ts` / `jwt-or-api-key.guard.ts` — Dual-auth for external API
- `daily-entries/guards/clinic-membership.guard.ts` — Ensures user belongs to target clinic
- `decorators/roles.decorator.ts` — `@Roles()` metadata
- `filters/all-exceptions.filter.ts` — Global REST exception formatting
- `pipes/zod-validation.pipe.ts` — Zod-based pipe (parallel to class-validator)
- `pipes/optional-parse-int.pipe.ts` — For optional `?provinceId` query params

**Docker build (`apps/api/Dockerfile`):**  
Multi-stage: `base` (node:20-alpine + pnpm 9.15.0) → `deps` (frozen install) → `build` (prisma:generate + shared build + nest build) → `production` (node dist/main, port 4000). Docker context is monorepo root.

**Test Structure:**

```
apps/api/test/
├── unit/       # 12 Jest spec files (service + resolver unit tests)
├── integration/ # Module integration tests
└── e2e/        # 8 Supertest API endpoint suites (105 tests)
```

---

## 3. Shared Packages

### 3.1 `packages/shared` — `@vets-hub/shared`

**What it is:** TypeScript-compiled library of constants, types, validation schemas, and utility functions shared between `apps/web` and `apps/api`.

**Package name:** `@vets-hub/shared`  
**Version:** 1.1.0  
**Build:** `tsc` → `dist/` (must run `pnpm --filter @vets-hub/shared build` before frontend dev)  
**Exports:** Root `./dist/index.js` plus sub-path exports for `./constants/*`, `./types/*`, `./validation/*`, `./utils/*`

**Source layout:**

```
packages/shared/src/
├── index.ts                # Re-exports all four sub-modules
├── constants/
│   ├── index.ts
│   └── ssp-forms.ts        # ANIMAL_TYPES, VACCINE_TYPES (7), MEDICAL_DISEASE_GROUPS (9),
│                           # SURGICAL_PROCEDURE_GROUPS (9), ANIMAL_SUB_TYPES, THAI_MONTHS,
│                           # THAI_MONTHS_SHORT, SSP_SECTION_NAMES, STATUS_LABELS
├── types/
│   ├── index.ts            # UserRole, ClinicType, ClinicStatus, DataSource,
│   │                       # MonthlySubmissionStatus, SubmissionStatus enums;
│   │                       # Province, District, SubDistrict, ClinicSummary,
│   │                       # SubmissionSummary, MonthlySubmission, DailyEntry,
│   │                       # DailyAnimalCountData, DailyVaccinationData,
│   │                       # DailyMedicalTreatmentData, DailySurgicalTreatmentData,
│   │                       # MonthProgress, CalendarDay, UnfilledDayAction
│   └── dashboard.ts        # Dashboard-specific types
├── validation/
│   ├── index.ts
│   ├── ssp-forms.ts        # Zod schemas for สสป. form validation
│   └── import-validation.ts # Zod schemas for Excel import
└── utils/
    └── index.ts            # Buddhist Era helpers: toThaiYear(), toGregorianYear(),
                            # getCurrentThaiYear(), formatThaiYear()
```

**Consumed by:**

- `apps/web` — imports constants, types, validation schemas, utils throughout form components and hooks
- `apps/api` — imports Zod validation schemas (via `ZodValidationPipe`), constants for reference data, types for DTO typing

---

### 3.2 `packages/db` — `@vets-hub/db`

**What it is:** Prisma schema definition, generated Prisma client re-export, and all seed scripts. The single source of truth for the database schema.

**Package name:** `@vets-hub/db`  
**Version:** 0.1.0  
**Main:** `./src/index.ts` (re-exports `PrismaClient` and all Prisma types from `@prisma/client`)  
**Postinstall:** runs `prisma generate` automatically

**Prisma Schema:** `packages/db/prisma/schema.prisma`  
Provider: PostgreSQL. Uses both `DATABASE_URL` (PgBouncer pooled, port 6543) and `DIRECT_URL` (session pooler direct, port 5432 — required for migrations).

**Database Models (22 total):**

| Group | Models |
|---|---|
| Geography | `Province`, `District`, `SubDistrict` |
| Auth & Users | `User`, `Session` |
| Clinics | `Clinic`, `ClinicUser` |
| Annual Submissions | `Submission`, `AnimalCount` (สสป.1), `Vaccination` (สสป.2), `MedicalTreatment` (สสป.3), `SurgicalTreatment` (สสป.4) |
| Daily Entry | `MonthlySubmission`, `DailyEntry`, `DailyAnimalCount`, `DailyVaccination`, `DailyMedicalTreatment`, `DailySurgicalTreatment` |
| Operational | `AuditLog`, `ApiKey`, `ImportJob`, `FeedbackReport` |

**Key Schema Design Decisions:**

- Clinic identified by `licenseNumber` (unique, from official license)
- Annual `Submission` is unique per `(clinicId, year)`; year stored as พ.ศ. (Thai Buddhist Era)
- `MonthlySubmission` unique per `(clinicId, year, month)` — tracks daily-entry vs. summary mode via `isSummaryMode`
- `DailyEntry` unique per `(monthlySubmissionId, date, isSummary)` — mutual exclusivity enforced in service layer
- Soft delete via `deletedAt` on `Clinic`
- DB columns: snake_case mapped to camelCase via `@map`
- Performance indexes (migration `20260307174311`): `districts_province_id_idx`, `sub_districts_district_id_idx`, `submissions_year_status_idx`, `monthly_submissions_clinic_id_year_idx`, `daily_entries_monthly_submission_id_is_summary_idx`, `audit_logs_created_at_idx`

**Migrations (chronological):**

| Migration | Date | Description |
|---|---|---|
| `20260209145048_init` | 2026-02-09 | Initial schema |
| `20260218004248_add_daily_entries` | 2026-02-18 | Add MonthlySubmission + DailyEntry models |
| `20260218112344_add_is_summary_to_daily_entries` | 2026-02-18 | Add `isSummary` flag |
| `20260307174311_add_performance_indexes` | 2026-03-07 | 6 performance indexes |
| `20260308000000_unified_entry_unique_constraint` | 2026-03-08 | Unique constraint on DailyEntry |
| `20260316233042_add_import_job_model` | 2026-03-16 | ImportJob model |
| `20260317073805_add_feedback_report` | 2026-03-17 | FeedbackReport model |
| `20260326034718_add_user_last_login_at` | 2026-03-26 | `lastLoginAt` on User |

**Seed Scripts:**

| Script | File | What it creates |
|---|---|---|
| `prisma:seed` | `seed.ts` | Geography + admin + 5 demo clinics (3-yr history) + Bangkok Excel clinics |
| `prisma:seed:minimal` | `seed-minimal.ts` | Geography + admin + 1 demo clinic (blank) |
| `prisma:seed:clean` | `seed-clean.ts` | Geography + admin + 5 demo + 221 bulk clinics (no data) |
| `seed:bulk` | `seed-bulk-demo.ts` | 221 clinics across 77 provinces with MonthlySubmission/DailyEntry data |
| `seed:blank` | `seed-blank-clinics.ts` | Blank clinic batch |
| `seed:fresh` | `seed-fresh.ts` | Configurable reset: `--mode=test`, `--mode=test-full`, `--mode=master` |
| `seed-utils.ts` | (utility) | Mulberry32 PRNG, seasonal factors, data generators, `makeDateUTC()` |

**Consumed by:**

- `apps/api` — imports `PrismaClient` and all Prisma-generated types for all ORM operations
- Seed scripts run directly via `tsx` (not imported at runtime by web)

---

## 4. Dependency Graph

```
apps/web  ──────────────────────────────────────────────────────→  @vets-hub/shared
apps/web  ──(HTTP: GraphQL /graphql + REST /api/v1/)──────────→  apps/api
apps/api  ──────────────────────────────────────────────────────→  @vets-hub/shared
apps/api  ──────────────────────────────────────────────────────→  @vets-hub/db
@vets-hub/db  ──────────────────────────────────────────────────→  @prisma/client
@vets-hub/shared  (no internal workspace deps, only zod)
```

**Workspace dependency declarations:**

```
apps/web/package.json:    "@vets-hub/shared": "workspace:*"
apps/api/package.json:    "@vets-hub/db": "workspace:*"
                          "@vets-hub/shared": "workspace:*"
```

`apps/web` does **not** directly import `@vets-hub/db`. All database access is server-side in `apps/api`; the frontend communicates exclusively over the network.

---

## 5. Build Pipeline (turbo.json)

```json
{
  "tasks": {
    "build":        { "dependsOn": ["^build"], "outputs": [".next/**", "!.next/cache/**", "dist/**"] },
    "dev":          { "cache": false, "persistent": true },
    "lint":         { "dependsOn": ["^build"] },
    "test":         { "dependsOn": ["^build"], "cache": false },
    "test:coverage":{ "dependsOn": ["^build"], "cache": false },
    "test:e2e":     { "dependsOn": ["^build"], "cache": false },
    "clean":        { "cache": false }
  }
}
```

**Build order enforced by `^build` (upstream-first):**

```
1. @vets-hub/shared  (tsc → dist/)       ← no workspace deps
2. @vets-hub/db      (tsc + prisma:generate → dist/)
3. @vets-hub/api     (nest build → dist/main.js)
4. @vets-hub/web     (next build → .next/)
```

**Turbo cache inputs for `build`:** The `env` array in `turbo.json` lists all env vars that affect the build cache: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_MAPBOX_TOKEN`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `DATABASE_URL`, `DIRECT_URL`.

**Root scripts:**

```bash
pnpm dev          # turbo dev (both apps in parallel, no cache, persistent)
pnpm build        # turbo build (topological order above)
pnpm lint         # turbo lint (after build)
pnpm test         # turbo test (after build, no cache)
pnpm test:all     # turbo test test:coverage test:e2e
pnpm format       # prettier --write (all ts/tsx/js/json/md)
pnpm clean        # turbo clean + rm -rf node_modules
# Seed convenience scripts delegated to @vets-hub/db:
pnpm seed:bulk
pnpm seed:fresh:test
pnpm seed:fresh:master
# API type generation (requires running api on :4000):
pnpm generate:api-types   # curl openapi.json → openapi-typescript → apps/web/types/api.d.ts
```

---

## 6. Tech Stack Per App

### `apps/web`

| Layer | Technology |
|---|---|
| Framework | Next.js 15.1, App Router, React 19 |
| Language | TypeScript 5.7 strict |
| Styling | Tailwind CSS 3.4 + shadcn/ui (Radix UI) |
| Data (GraphQL) | Apollo Client |
| Data (REST) | SWR 2.3 |
| Auth | NextAuth.js v5 (Email/Password; ThaID OAuth planned) |
| Forms | React Hook Form 7.54 + Zod 3.24 |
| Charts | Recharts 2.15 (`<ResponsiveContainer>` always) |
| Maps | Mapbox GL JS 3.9 (`mapbox://styles/mapbox/light-v11`) + react-map-gl |
| Excel | SheetJS (client-side parsing of uploaded สสป. Excel) |
| Font | Noto Sans Thai (Thai subset, via `next/font/google`) |
| Design tokens | `#1A3B6E` (DLD blue), `#C5A34E` (gold accent), `#0D9488` (teal) |
| Testing | Vitest 2.1 + RTL 16 + MSW 2.7 (unit); Playwright 1.49 (E2E) |
| Runtime | Vercel (Node.js runtime, no Edge) |

### `apps/api`

| Layer | Technology |
|---|---|
| Framework | NestJS 10, Express platform |
| Language | TypeScript 5.7 strict |
| Primary API | GraphQL code-first (Apollo Server, `@nestjs/graphql`) |
| REST adapter | NestJS controllers, URI versioning (`/api/v1/`) |
| ORM | Prisma 6 (via `@vets-hub/db`) |
| Database | PostgreSQL 16 (Supabase, `aws-1-ap-south-1`) |
| Auth | JWT 7d expiry (bcryptjs hashing, `passport-jwt` strategy) |
| API key auth | bcrypt-hashed keys with 8-char prefix, `X-API-Key` header |
| Rate limiting | `@nestjs/throttler` 100 req/min global |
| Cache | In-memory (cache-manager, 5-min TTL) |
| Validation | class-validator + Zod (dual validation) |
| Documentation | `@nestjs/swagger` OpenAPI 3.0 at `/api/docs` |
| Security | `helmet` (HTTP headers) |
| Testing | Jest 29 (unit); Jest + Supertest (E2E) |
| Runtime | Docker (node:20-alpine), deployed on Render.com |

---

## 7. Deployment Configuration

### Production Infrastructure

```
Vercel (Frontend)                Render.com (Backend)              Supabase (Database)
─────────────────                ────────────────────              ───────────────────
apps/web                         apps/api (Docker)                 PostgreSQL 16
  → vets-hub.vercel.app            → vets-hub.onrender.com           aws-1-ap-south-1
  → vets-hub.pops.vet (MVP)          /graphql                         Port 6543 (PgBouncer)
  → vets-hub.dld.go.th (future)      /api/v1/*                        Port 5432 (direct migrations)
                                     /api/docs (Swagger)
                                     Health: /api/v1/reference/vaccines
```

### `render.yaml`

```yaml
services:
  - type: web
    name: vets-hub-api
    runtime: docker
    dockerfilePath: ./apps/api/Dockerfile
    dockerContext: .                        # monorepo root
    branch: main
    healthCheckPath: /api/v1/reference/vaccines
    envVars:
      NODE_ENV: production
      JWT_EXPIRATION: 7d
      ENABLE_SWAGGER: 'true'               # enabled in production via env override
      DATABASE_URL, DIRECT_URL, JWT_SECRET, FRONTEND_URL: (sync: false — set in Render dashboard)
```

**Render caveat:** Changing env vars in the Render dashboard does NOT auto-trigger a redeploy — must click "Manual Deploy".

### `docker-compose.yml` (local dev only)

```yaml
services:
  postgres:  postgres:16-alpine, port 5432, volume postgres_data
  api:       apps/api/Dockerfile (context: monorepo root), port 4000
             depends_on: postgres (healthcheck)
```

### Vercel (Frontend)

- Linked via `.vercel/project.json` (`projectId: prj_KnBMEJoMjYGMnuZdN5GWkXGYBcEH`, `orgId: team_222ZtuysPAxfEx3wGzFLXZXX`)
- Deploy command: `vercel --prod --yes` run from **monorepo root** (not `apps/web`)
- Auto-deploys from GitHub `main` branch

### CI/CD

- **`.github/workflows/issue-triage.yml`** — Only workflow. Runs on `issues` events and daily at 02:00 UTC (09:00 Bangkok) on weekdays. Lists open issues in GitHub step summary. Does not run tests or deploy.
- **No automated test CI pipeline** — tests run locally or manually.
- Frontend deploys: Vercel GitHub integration (auto on push to `main`)
- Backend deploys: Render GitHub integration (auto on push to `main`)

### Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `DATABASE_URL` | api, db seeds | Supabase PgBouncer pooled URL (port 6543, `?pgbouncer=true&connection_limit=5`) |
| `DIRECT_URL` | api, db seeds | Supabase direct URL (port 5432, for Prisma migrations) |
| `JWT_SECRET` | api | JWT signing secret |
| `JWT_EXPIRATION` | api | Token TTL (default `7d`) |
| `FRONTEND_URL` | api | Comma-separated CORS allowed origins |
| `NEXTAUTH_URL` | web | NextAuth base URL |
| `NEXTAUTH_SECRET` | web | NextAuth signing secret |
| `NEXT_PUBLIC_API_URL` | web | GraphQL/REST endpoint (`http://localhost:4000/api/v1`) |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | web | Mapbox public token (50,000 map loads/month free tier) |
| `NEXT_PUBLIC_SUPABASE_URL` | web | Supabase project URL (storage) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | web | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | web | Supabase service role (server-side storage ops) |
| `ENABLE_SWAGGER` | api | `'true'` to expose `/api/docs` in production |
| `PORT` | api | Server port (default 4000) |

---

## 8. Data Flow

### Clinic Annual Report Submission (primary flow)

```
Browser
  → Next.js (portal route /clinic/[id])
    → SWR fetches MonthlySubmission status from /api/v1/daily-entries/...
    → User enters daily data → UnifiedEntryForm
      → Apollo mutation / SWR POST → /api/v1/daily-entries/upsert
        → DailyEntriesController → DailyEntriesService
          → ClinicMembershipGuard validates user ∈ clinic
          → Prisma upsert DailyEntry + DailyAnimalCount/Vaccination/MedicalTreatment/SurgicalTreatment
          → PgBouncer (port 6543) → PostgreSQL 16 (Supabase)
    → User clicks "ส่งรายงาน" for month
      → POST /api/v1/daily-entries/submit-month
        → 4 parallel Prisma groupBy SQL aggregations (ReadCommitted isolation)
        → Creates annual Submission record (SUBMITTED status, no review workflow)
```

### Public Dashboard (analytics flow)

```
Browser (no auth)
  → Next.js /dashboard
    → SWR fetches from /api/v1/reports/...
      → ReportsController → DashboardReportsService / GeographyReportsService
        → Prisma aggregate queries (with 5-min cache)
        → Returns KPIs, choropleth data, chart data
    → Mapbox GL JS renders choropleth from /geo/thailand-provinces.geojson (static)
```

### Third-party Clinic Software Integration

```
Clinic OS / external software
  → POST /api/v1/external/{endpoint}
    → X-API-Key header → ApiKeyGuard (bcrypt hash verify)
    → ExternalController → DailyEntriesService (same logic as web portal)
    → Rate limited to 100 req/min per key
```

---

## 9. Key Architectural Decisions

1. **GraphQL primary + REST adapter:** GraphQL for all first-party data operations (Apollo Client in web); REST `/api/v1/` only for third-party clinic software and admin operations that need simpler auth (Bearer token).

2. **Daily Entry mutual exclusivity:** `MonthlySubmission` enforces one mode per month — either daily-entry mode (multiple `DailyEntry` rows per day) or summary mode (single `DailyEntry` with `isSummary=true`). `ConflictException` thrown if mixing.

3. **Buddhist Era (พ.ศ.) throughout UI:** All years displayed as พ.ศ. (Gregorian + 543). DB stores Gregorian. Conversion via `toThaiYear()` / `toGregorianYear()` in `@vets-hub/shared`. Never inline `+ 543`.

4. **PgBouncer compatibility:** `DATABASE_URL` includes `?pgbouncer=true&connection_limit=5`. `DIRECT_URL` bypasses PgBouncer for Prisma migrations. `submitMonth` uses `ReadCommitted` isolation (not `Serializable`) to avoid deadlocks through the pooler.

5. **Submission review workflow bypassed (v1.2.3):** `UNDER_REVIEW / APPROVED / REJECTED / REVISION_REQUESTED` statuses exist in schema and service but are not wired in any active controller. Submissions auto-approved on submit.

6. **Admin clinics page uses REST not GraphQL:** Uses Bearer token auth (not NextAuth session) to call `/api/v1/clinics` directly. Reason: GraphQL clinics resolver was added authorization guards in v1.0.2 that required re-architecture.

7. **`@vets-hub/shared` must be built before web dev:** `dist/` is the consumed artifact. If source changes, re-run `pnpm --filter @vets-hub/shared build`.

8. **Monorepo Docker build:** Docker context is the monorepo root (not `apps/api/`). The Dockerfile explicitly copies only the packages needed by the API (`packages/db`, `packages/shared`, `apps/api`) to minimize image size.

9. **No `packages/config`:** Although listed in CLAUDE.md architecture diagram, `packages/config` does not exist on disk. ESLint configs live in each app (`apps/web/.eslintrc.json`, `apps/api/.eslintrc.js`). Prettier config is at the root (`.prettierrc`).
