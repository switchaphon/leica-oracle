# VetsHub — Quick Reference for New Developers

> Last updated: 2026-04-26 | Version: 1.5.1 (web) / 1.1.0 (api)

---

## 1. What is VetsHub?

VetsHub (ศูนย์กลางสถานพยาบาลสัตว์แห่งชาติ) is a Thai government web platform that digitizes the annual **สสป. (สถิติสัตว์ป่วย)** animal health reporting process. It serves ~3,000 veterinary clinics under **กรมปศุสัตว์** (Department of Livestock Development, Thailand), replacing Excel-based submissions with a modern web application.

**Live URLs:**
- Frontend: https://vets-hub.vercel.app (MVP domain: https://vets-hub.pops.vet)
- Backend API: https://vets-hub.onrender.com
- Swagger UI: https://vets-hub.onrender.com/api/docs
- GraphQL Playground: https://vets-hub.onrender.com/graphql

**Three user types:**
1. **Clinic owners** — submit monthly สสป.1-4 reports (daily or monthly summary mode)
2. **Government officers (SUPER_ADMIN)** — review submissions, manage clinics, view analytics, import Excel data
3. **Public** — view the national dashboard with geospatial analytics (no login required)

---

## 2. Monorepo Apps and Packages

### Apps

| App | Package name | Port | Purpose |
|-----|-------------|------|---------|
| `apps/web` | `@vets-hub/web` | 3000 | Next.js 15 (App Router) frontend |
| `apps/api` | `@vets-hub/api` | 4000 | NestJS 10 backend — GraphQL + REST v1 |

#### `apps/web` — Next.js Frontend

Route groups under `app/`:

| Group | Routes | Auth |
|-------|--------|------|
| `(auth)` | `/login`, `/register` | None |
| `(public)` | `/dashboard`, `/map` | None |
| `(portal)` | `/clinic/[id]/...` | JWT (clinic owners) |
| `(admin)` | `/admin/dashboard`, `/admin/clinics`, `/admin/submissions`, `/admin/import`, `/admin/reports`, `/admin/users` | JWT + SUPER_ADMIN |

Key frontend tech: Next.js 15, React 19, TypeScript strict, Tailwind CSS 4, shadcn/ui, Apollo Client (GraphQL), SWR (REST), React Hook Form + Zod, Recharts, Mapbox GL JS, NextAuth.js v5.

#### `apps/api` — NestJS Backend

Key modules under `src/`:

| Module | Endpoints | Notes |
|--------|-----------|-------|
| `auth/` | JWT auth, guards, strategies | |
| `clinics/` | CRUD + search | Authorization guards required |
| `submissions/` | Full-year สสป.1-4 forms | |
| `daily-entries/` | 22 REST endpoints `/api/v1/daily-entries/` | Also `external.controller.ts` — 8 endpoints `/api/v1/external/` for third-party integrations |
| `reports/` | 40+ aggregation/analytics endpoints | |
| `admin/` | Review, bulk ops | Submission review is read-only (bypassed for MVP) |
| `import/` | Excel (SheetJS) parsing | |
| `api-keys/` | API key management | bcrypt-hashed, prefix stored |

### Packages

| Package | Name | Purpose |
|---------|------|---------|
| `packages/shared` | `@vets-hub/shared` | Zod schemas, TypeScript types, constants (สสป. form data, animal types, diseases), shared utils |
| `packages/db` | `@vets-hub/db` | Prisma schema + generated client — used by both apps |
| `packages/config` | — | Shared ESLint, TSConfig, Tailwind configs |

**Critical**: `packages/shared` must be **built** before running `apps/web`. The `packages/db` auto-generates the Prisma client on `postinstall`.

---

## 3. Setup and Installation

### Prerequisites

- **Node.js** >= 20.x
- **pnpm** 9.15.0 — `npm install -g pnpm`
- **Docker** (recommended for local DB) — macOS with Colima: run `colima start` before `docker-compose up`
- **Git**

### Step-by-step

```bash
# 1. Clone
git clone https://github.com/switchaphon/vets-hub.git
cd vets-hub

# 2. Install all dependencies
pnpm install
# (packages/db postinstall hook auto-runs prisma generate)

# 3. Build the shared package — REQUIRED before running the frontend
pnpm --filter @vets-hub/shared build

# 4. Copy and fill environment variables
cp .env.example .env
# Edit .env — see Section 5 for required variables

# 5. Start local database
docker-compose up -d
# Wait for postgres to be healthy, then:

# 6. Run migrations
pnpm --filter @vets-hub/db prisma:migrate

# 7. Seed the database (choose one scenario)
pnpm --filter @vets-hub/db prisma:seed          # Full demo with 3 years of history
pnpm --filter @vets-hub/db prisma:seed:clean    # Clinics only, no history
pnpm --filter @vets-hub/db prisma:seed:minimal  # Single demo account only

# 8. Start both apps
pnpm dev
```

After starting:
- Frontend: http://localhost:3000
- Backend: http://localhost:4000
- Swagger: http://localhost:4000/api/docs
- GraphQL: http://localhost:4000/graphql
- Prisma Studio: `pnpm --filter @vets-hub/db prisma:studio`

---

## 4. Key Turbo Commands

All commands run from the monorepo root.

### Development

```bash
pnpm dev                          # Start both apps (hot reload)
pnpm --filter web dev             # Frontend only (:3000)
pnpm --filter api dev             # Backend only (:4000)
```

### Build

```bash
pnpm build                        # Build all (respects turbo dependency order)
pnpm --filter web build           # Frontend only
pnpm --filter api build           # Backend only
```

### Test

```bash
pnpm test                         # All unit + integration tests
pnpm test:all                     # All tests + coverage + E2E

# Frontend (Vitest)
pnpm --filter web test            # Unit + integration
pnpm --filter web test:coverage
pnpm --filter web test:e2e        # Playwright E2E
pnpm --filter web test:e2e:ui     # Playwright UI mode
pnpm --filter web test:e2e:responsive   # Responsive tests (375px + 768px viewports)

# Run a single frontend test file
pnpm --filter web test -- __tests__/unit/components/MyComponent.test.tsx

# Backend (Jest)
pnpm --filter api test            # Unit tests
pnpm --filter api test:integration
pnpm --filter api test:e2e        # Supertest E2E
pnpm --filter api test:coverage

# Run a single backend test file
pnpm --filter api test -- test/unit/some.service.spec.ts
```

### Lint and Format

```bash
pnpm lint                         # ESLint across all workspaces
pnpm --filter web lint
pnpm --filter api lint:fix        # With auto-fix
pnpm format                       # Prettier (all TS/TSX/JSON/MD files)
pnpm format:check                 # Dry-run check
```

### Database

```bash
pnpm --filter @vets-hub/db prisma:generate    # Regenerate Prisma client
pnpm --filter @vets-hub/db prisma:migrate     # Run pending migrations
pnpm --filter @vets-hub/db prisma:studio      # Open Prisma Studio UI

# Seed scenarios
pnpm --filter @vets-hub/db prisma:seed         # Full: geography + 343 clinics + 3-year history
pnpm --filter @vets-hub/db prisma:seed:clean   # Clinics only, no historical data
pnpm --filter @vets-hub/db prisma:seed:minimal # Single demo account, no data
pnpm seed:bulk                                 # 221 clinics across all 77 provinces
pnpm seed:fresh:test                           # Fresh reset: 226 clinics, no reports
pnpm seed:fresh:test-full                      # Fresh reset with generated reports
pnpm seed:fresh:master                         # Fresh reset: 117 Bangkok clinics only
```

### Utilities

```bash
pnpm clean                        # Clean all build artifacts + node_modules
pnpm generate:api-types           # Fetch OpenAPI spec → apps/web/types/api.d.ts (requires api running)
```

---

## 5. Environment Variables

### Minimal `.env` for local development

```env
# Database — Docker local
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/vets_hub"
DIRECT_URL="postgresql://postgres:postgres@localhost:5432/vets_hub"

# NextAuth
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="<openssl rand -base64 32>"

# Backend connection (frontend → backend)
API_URL="http://localhost:4000"
NEXT_PUBLIC_API_URL="http://localhost:4000/api/v1"

# JWT (backend)
JWT_SECRET="<openssl rand -base64 32>"
JWT_EXPIRATION="7d"

# Optional — required for map features
NEXT_PUBLIC_MAPBOX_TOKEN="pk.your-mapbox-public-token"
```

### Additional optional variables

```env
# Supabase Storage (needed only if using file upload features)
NEXT_PUBLIC_SUPABASE_URL="https://[project].supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

### Per-app variable ownership

| Variable | Used by | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `apps/api`, `packages/db` | Add `?pgbouncer=true&connection_limit=5` in production |
| `DIRECT_URL` | `packages/db` | Direct connection — required for `prisma migrate` |
| `JWT_SECRET` | `apps/api` | Backend signs tokens |
| `JWT_EXPIRATION` | `apps/api` | Default `7d` |
| `NEXTAUTH_URL` | `apps/web` | |
| `NEXTAUTH_SECRET` | `apps/web` | |
| `NEXT_PUBLIC_API_URL` | `apps/web` | GraphQL endpoint in local dev: `http://localhost:4000/api/v1` |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | `apps/web` | Optional; map will not render without it |
| `FRONTEND_URL` | `apps/api` | CORS — comma-separated allowed origins |

### Generate secrets

```bash
openssl rand -base64 32   # for JWT_SECRET, NEXTAUTH_SECRET
```

---

## 6. Common Development Workflows

### Starting a new feature

1. Branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Write tests first (TDD — RED → GREEN → REFACTOR)
3. Implement the feature
4. Run relevant tests:
   ```bash
   pnpm --filter web test -- __tests__/unit/...
   pnpm --filter api test -- test/unit/...
   ```
5. Run lint and format:
   ```bash
   pnpm lint && pnpm format
   ```
6. Open a PR to `main`

### Adding a frontend component

- Place in `apps/web/components/ui/` (shadcn/ui primitives) or a feature subfolder
- Use `'use client'` only when the component needs interactivity or browser APIs — server components by default
- Use Apollo Client for GraphQL, SWR for REST
- All user-facing text must be in Thai (ภาษาทางการ)

### Adding a backend endpoint

- Add REST endpoints to the relevant module under `apps/api/src/`
- GraphQL is primary; REST (`/api/v1/`) is for third-party and some admin ops
- Use `@Roles()` + `RolesGuard` for role-protected routes
- Use `@ApiKeyAuth()` for third-party integrations
- Add Swagger decorators — the OpenAPI spec auto-generates

### Adding a Prisma model or migration

```bash
# 1. Edit packages/db/prisma/schema.prisma
# 2. Create migration
pnpm --filter @vets-hub/db prisma:migrate
# 3. Regenerate the client
pnpm --filter @vets-hub/db prisma:generate
```

The generated client is shared by both `apps/api` and `packages/db/src/index.ts`.

### Using the shared package

- Add TypeScript types to `packages/shared/src/types/`
- Add Zod schemas to `packages/shared/src/validation/`
- Add constants to `packages/shared/src/constants/`
- Export from `packages/shared/src/index.ts`
- **Rebuild after every change**:
  ```bash
  pnpm --filter @vets-hub/shared build
  ```
- Both `apps/web` and `apps/api` import via `@vets-hub/shared`

### Generating API types from OpenAPI spec

With `apps/api` running on `:4000`:
```bash
pnpm generate:api-types
# Outputs to apps/web/types/api.d.ts
```

### Thai year conversion

Never inline `+ 543` or `- 543`. Always use the helpers:
```typescript
import { getCurrentThaiYear, toThaiYear, formatThaiYear } from '@/lib/utils/thai-year'

getCurrentThaiYear()       // new Date().getFullYear() + 543
toThaiYear(2025)           // 2568
formatThaiYear(2025)       // "พ.ศ. 2568"
```

DB always stores Gregorian year. UI always displays Buddhist Era (พ.ศ.).

---

## 7. Notable Gotchas for New Developers

### Build order is mandatory

`packages/shared` must be built before running `apps/web`. If you see `TypeError: Cannot read properties of undefined` on the frontend, you almost certainly forgot:
```bash
pnpm --filter @vets-hub/shared build
```
Re-run this every time you change anything in `packages/shared/src/`.

### Prisma schema lives in `packages/db`, not `apps/api`

All Prisma commands (generate, migrate, seed, studio) target `packages/db`. The scripts in `apps/api/package.json` that reference prisma pass `--schema=../../packages/db/prisma/schema.prisma` explicitly.

### Production DATABASE_URL needs PgBouncer flags

```env
DATABASE_URL="postgresql://...?pgbouncer=true&connection_limit=5"
```
Without `pgbouncer=true`, Prisma sends prepared statements that PgBouncer rejects. With `connection_limit=1`, parallel queries (the dashboard fires ~10) starve the pool.

### Render does NOT auto-redeploy on env var changes

If you update environment variables in the Render dashboard, you must click "Manual Deploy" — changing env vars alone does not trigger a redeploy.

### `vercel --prod` must run from the monorepo root

Deploy frontend from the repo root, not from `apps/web`:
```bash
cd /path/to/vets-hub && vercel --prod --yes
```

### Daily entry mode is mutually exclusive

A monthly submission is either in daily-entry mode or summary mode — never both. The guards in `apps/api/src/daily-entries/daily-entries.service.ts` throw `ConflictException` if you mix them. Mode is determined at runtime: summary record exists → summary mode; daily calendar entries exist → daily mode; neither → mode chooser.

### Sidebar breakpoint is `lg` (1024px), not `md`

The sidebar switches from mobile overlay drawer to static fixed at `lg`. Tablets at 768px (`md`) see the mobile drawer. Responsive E2E tests use mobile-chrome (375px) and tablet-chrome (768px) viewports with `@responsive` tag.

### `orderBy` on relation fields can fail through PgBouncer

Avoid `orderBy: { clinic: { name: 'asc' } }` through PgBouncer in production — fetch data and sort in JS instead.

### Apollo Client is for GraphQL; SWR is for REST

- GraphQL mutations + subscriptions → Apollo Client
- REST endpoints (`/api/v1/`) + simple fetches → SWR
- Admin clinics page fetches from REST with Bearer auth token, not GraphQL

### Overdue endpoint uses พ.ศ. year in the URL

`GET /api/v1/daily-entries/overdue/:clinicId/:year` — the `:year` param is Buddhist Era (e.g. `2568`). The service converts to Gregorian internally.

### Colima users on macOS

Run `colima start` before `docker-compose up -d`. Otherwise Docker daemon won't be available.

---

## Demo Accounts

All clinic account passwords: `clinic123456`

| Account | Password | Role | Clinics |
|---------|----------|------|---------|
| `admin@vets-hub.pops.vet` | `admin123456` | SUPER_ADMIN | — |
| `clinic1@vets-hub.pops.vet` | `clinic123456` | CLINIC_OWNER | DEMO-BKK-001 |
| `clinic2@vets-hub.pops.vet` | `clinic123456` | CLINIC_OWNER | DEMO-CM-001, DEMO-PKT-001 |
| `clinic3@vets-hub.pops.vet` | `clinic123456` | CLINIC_OWNER | DEMO-KK-001 |
| `clinic4@vets-hub.pops.vet` | `clinic123456` | CLINIC_OWNER | DEMO-NR-001 |
| `demo@vets-hub.pops.vet` | `clinic123456` | CLINIC_OWNER | DEMO-TEST-001 (minimal seed only) |

---

## Infrastructure Summary

| Layer | Service | Deploy trigger |
|-------|---------|----------------|
| Frontend | Vercel | Auto from `main` (or `vercel --prod --yes` from root) |
| Backend | Render (Docker) | Auto from `main` push; config in `render.yaml` |
| Database | Supabase PostgreSQL 16 (aws-1-ap-southeast-1) | Managed |

Health check endpoint (Render): `GET /api/v1/reference/vaccines`

---

## Key File Locations

| What | Where |
|------|-------|
| Prisma schema | `packages/db/prisma/schema.prisma` |
| Seed scripts | `packages/db/prisma/seed*.ts` |
| Shared types/constants/validation | `packages/shared/src/` |
| Thai year helpers | `apps/web/lib/utils/thai-year.ts` |
| NextAuth config | `apps/web/lib/auth.ts` |
| Apollo Client config | `apps/web/lib/apollo-client.ts` |
| Mapbox config | `apps/web/lib/mapbox.ts` |
| Chart description constants (Thai) | `apps/web/lib/constants/chart-descriptions.ts` |
| NestJS app entry | `apps/api/src/app.module.ts` |
| Swagger config | `apps/api/src/swagger/swagger.config.ts` |
| External API controller | `apps/api/src/daily-entries/external.controller.ts` |
| สสป. form constants | `packages/shared/src/constants/ssp-forms.ts` |
| Turbo pipeline config | `turbo.json` |
| Render deployment config | `render.yaml` |
| Docker local dev | `docker-compose.yml` |
| Environment variable template | `.env.example` |
| Production env template | `.env.production.example` |
| Tech specs | `docs/specs/` (13 spec files) |
| PRPs (feature plans) | `PRPs/` |
