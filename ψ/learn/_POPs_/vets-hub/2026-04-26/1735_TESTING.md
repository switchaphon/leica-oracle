# TESTING — vets-hub monorepo
> Explored: 2026-04-26 | Branch: main | Package manager: pnpm 9 + Turborepo 2

---

## 1. Test Structure

The monorepo has two testable apps. Neither `packages/db` nor `packages/shared` carries its own test suite — shared logic is tested through the consumers.

```
vets-hub/
├── apps/
│   ├── api/          NestJS backend  — Jest (unit + e2e)
│   └── web/          Next.js 15 frontend — Vitest (unit + integration) + Playwright (e2e)
├── packages/
│   ├── db/           Prisma schema + seeds  — no tests
│   └── shared/       Types / utils / validation — no tests (covered by web unit tests)
```

### apps/api — directory layout

```
apps/api/test/
├── unit/         *.spec.ts  — 43 files
│   ├── auth.service.spec.ts
│   ├── auth.controller.spec.ts
│   ├── clinics.service.spec.ts / controller
│   ├── daily-entries.service.spec.ts / controller
│   ├── reports.controller.spec.ts
│   ├── analytics-reports.service.spec.ts
│   ├── dashboard-reports.service.spec.ts
│   ├── geography-reports.service.spec.ts
│   ├── surveillance-reports.service.spec.ts
│   ├── vaccination-reports.service.spec.ts
│   ├── surgical-reports.service.spec.ts
│   ├── import.service.spec.ts
│   ├── monthly-submission.service.spec.ts
│   ├── monthly-summary.service.spec.ts
│   ├── guards.spec.ts
│   ├── jwt.strategy.spec.ts
│   ├── rate-limit.spec.ts
│   ├── security-fixes.spec.ts
│   ├── api-key.service.spec.ts / controller
│   ├── audit.service.spec.ts
│   ├── feedback.service.spec.ts / controller
│   ├── prisma.service.spec.ts
│   ├── zod-validation-pipe.spec.ts
│   ├── all-exceptions-filter.spec.ts
│   └── external.controller.spec.ts
└── e2e/          *.e2e-spec.ts  — 8 files
    ├── auth.e2e-spec.ts
    ├── clinics.e2e-spec.ts
    ├── daily-entries.e2e-spec.ts
    ├── excel-import-flow.e2e-spec.ts
    ├── reference.e2e-spec.ts
    ├── reports.e2e-spec.ts
    ├── rest-api-v1.e2e-spec.ts
    └── swagger.e2e-spec.ts
```

### apps/web — directory layout

```
apps/web/__tests__/
├── setup.ts                   global setup (jest-dom matchers)
├── unit/                      ~110 files
│   ├── components/            component-level tests mirroring src/components tree
│   │   ├── dashboard/         chart components + modules + intelligence widgets
│   │   ├── daily/             daily-entry UI components
│   │   ├── clinic/            clinic landing components
│   │   ├── forms/             form components + helpers
│   │   ├── import/            importer components
│   │   ├── layout/            header / sidebar / breadcrumb
│   │   ├── loading/           skeleton components
│   │   ├── maps/              map metric toggle
│   │   ├── providers/         SessionProvider
│   │   └── ui/                searchable select components
│   ├── hooks/                 7 custom-hook test files
│   ├── pages/                 3 page-level render tests (admin)
│   ├── shared/                import-validation + ssp-section-names
│   ├── utils/                 excelParser, thaiYear, clinic-page-helpers, template-generator
│   └── validation/            zod-schemas
├── integration/               3 files — full page renders with mocked API
│   ├── AdminDashboardPage.test.tsx
│   ├── DashboardPage.test.tsx
│   └── daily-entry.test.tsx
└── e2e/                       ~15 spec files + 2 setup files + fixtures/
    ├── auth.setup.ts           admin auth setup (saves .auth/admin.json)
    ├── auth-clinic.setup.ts    clinic auth setup (saves .auth/clinic.json)
    ├── fixtures/
    │   ├── auth.ts             adminTest / clinicTest fixtures (storageState reuse)
    │   ├── clinic-import-test.xlsx
    │   └── ssp-import-test.xlsx
    └── *.spec.ts               feature specs (admin-*, portal-*, cross-role-access, responsive-layout, etc.)
```

---

## 2. Frameworks Per App/Package

| Location | Framework | Version | Runner |
|---|---|---|---|
| `apps/api` unit | Jest + ts-jest | 29.7 / 29.2 | `jest` (default config) |
| `apps/api` e2e | Jest + ts-jest + supertest | same | `jest --config jest.e2e.config.ts` |
| `apps/web` unit + integration | Vitest + @vitejs/plugin-react | ~2.1 | `vitest run` |
| `apps/web` coverage | Vitest + @vitest/coverage-v8 | ~2.1 | `vitest run --coverage` |
| `apps/web` e2e | Playwright | ^1.49 | `playwright test` |
| `packages/db` | — | — | no tests |
| `packages/shared` | — | — | no tests |

### Key supporting libraries

- **`@testing-library/react` v16** + **`@testing-library/user-event` v14** — DOM interaction in Vitest
- **`@testing-library/jest-dom` v6** — custom matchers (imported via `__tests__/setup.ts`)
- **`msw` v2** — present in web devDependencies (available for request mocking)
- **`supertest` v7** — HTTP assertions in API e2e tests
- **`@nestjs/testing`** — NestJS `TestingModule` factory for API unit tests

---

## 3. Shared Test Utilities and Mock Patterns

### apps/api unit tests

All unit tests follow the same NestJS pattern:

```ts
// Inline provider mock objects — one per dependency
const mockPrismaService = {
  user: { findUnique: jest.fn(), create: jest.fn(), update: jest.fn().mockResolvedValue({}) },
};

beforeEach(async () => {
  const module: TestingModule = await Test.createTestingModule({
    providers: [
      TestedService,
      { provide: PrismaService, useValue: mockPrismaService },
      { provide: JwtService,    useValue: mockJwtService },
    ],
  }).compile();
  jest.clearAllMocks();  // always reset between cases
});
```

Module-level mocks are used for side-effectful packages (`jest.mock('bcryptjs')`).

`guards.spec.ts` provides a reusable `makeHttpContext(overrides)` helper that builds NestJS `ExecutionContext` mocks for guard testing — a pattern repeated across guard-related specs.

### apps/api e2e tests

All e2e specs spin up the full `AppModule` via `INestApplication` + supertest. They use a timestamp-scoped `testId = Date.now()` to namespace test data and clean up in `afterAll`:

```ts
afterAll(async () => {
  await prisma.user.deleteMany({ where: { email: { contains: `${testId}` } } });
  await app.close();
});
```

### apps/web unit tests

Common vi.mock() stubs used across many component tests:

- `next-auth/react` → `useSession()` returns a stable mock session object
- `next/navigation` → `useRouter`, `useSearchParams`, `usePathname` stubs
- `react-intersection-observer` → `useInView` returns `{ ref: vi.fn(), inView: true }`
- `recharts` → `ResponsiveContainer` is shimmed to a plain div (avoids SVG in jsdom)
- `react-map-gl` + `mapbox-gl` → replaced with lightweight div mocks
- `@/lib/mapbox` → token + center constants stubbed

These mocks are defined inline per file (no shared mock factory), but the patterns are consistent enough to replicate.

Hook tests use `@testing-library/react`'s `renderHook` + `vi.useFakeTimers()` for debounce/timing assertions.

### apps/web E2E fixtures

`__tests__/e2e/fixtures/auth.ts` exports two typed fixtures:

- `adminTest` — `browser.newContext({ storageState: .auth/admin.json })`, navigates to `/admin/dashboard`
- `clinicTest` — navigates to `/clinic`, waits for redirect to `/clinic/:id`, exposes `clinicId` derived from URL

XLSX fixture files are present for import-flow specs.

---

## 4. E2E Test Setup

### Playwright (apps/web)

Config: `apps/web/playwright.config.ts`

| Setting | Value |
|---|---|
| `testDir` | `./__tests__/e2e` |
| `baseURL` | `http://localhost:3000` |
| `fullyParallel` | `true` |
| `retries` | 2 on CI, 0 locally |
| `workers` | 1 on CI, `undefined` (auto) locally |
| `reporter` | `html` |
| `trace` | `on-first-retry` |
| `forbidOnly` | `true` on CI |

**Projects:**

| Project | Device | Condition |
|---|---|---|
| `admin-setup` | — | auth setup only (`auth.setup.ts`) |
| `clinic-setup` | — | auth setup only (`auth-clinic.setup.ts`) |
| `chromium` | Desktop Chrome | default (depends on both setups) |
| `mobile-chrome` | iPhone 14 | `@responsive` tag only |
| `tablet-chrome` | 768×1024 viewport | `@responsive` tag only |

**Auth strategy:** setup projects log in once and serialize session to `.auth/admin.json` and `.auth/clinic.json` (gitignored). Test specs import from `fixtures/auth.ts` and reuse stored `storageState` — no repeated login per test.

**Web server:** `pnpm dev` is started automatically; existing servers are reused locally, always fresh on CI.

**Run commands:**

```bash
# From apps/web/
pnpm test:e2e                        # all specs, Chromium only
pnpm test:e2e:responsive             # @responsive specs, mobile + tablet, single worker
pnpm test:e2e:ui                     # Playwright UI mode
```

### Jest e2e (apps/api)

Config: `apps/api/jest.e2e.config.ts`

- `testRegex`: `test/e2e/.*\.e2e-spec\.ts$`
- `testEnvironment`: `node`
- Requires a live database connection (uses real `PrismaService` via `AppModule`)

```bash
# From apps/api/
pnpm test:e2e
```

---

## 5. Lint and Code Quality

### ESLint

| App | Config file | Extends |
|---|---|---|
| `apps/web` | `.eslintrc.json` | `next/core-web-vitals`, `@typescript-eslint/recommended`, `prettier` |
| `apps/api` | `.eslintrc.js` | `@typescript-eslint/recommended`, `prettier` |

Both configs use `@typescript-eslint/parser` with `project: ./tsconfig.json` (type-aware linting).

Shared rule profile:
- `@typescript-eslint/no-unused-vars`: **warn** (args prefixed `_` are ignored)
- `@typescript-eslint/no-explicit-any`: **warn**
- `@typescript-eslint/explicit-function-return-type` / `explicit-module-boundary-types`: **off** (api only)
- `react/no-unescaped-entities`: **off** (web only)

Both disable the flat config flag at invocation time (`ESLINT_USE_FLAT_CONFIG=false`) to stay on the legacy `.eslintrc` format.

### Prettier

Root-level Prettier covers all `ts,tsx,js,jsx,json,md` files:

```bash
pnpm format         # write
pnpm format:check   # CI-safe check
```

### TypeScript

- Root `typescript ^5.7` as shared devDependency
- Both apps use `"project": "./tsconfig.json"` in ESLint for full type-aware rules
- No `strict: false` overrides visible — strict mode is the default

### No commitlint config found.

---

## 6. CI/CD Pipeline

Only one GitHub Actions workflow exists: `.github/workflows/issue-triage.yml`.

This workflow **does not run tests**. It is a housekeeping utility that:
- Triggers on new/labeled issues, on a weekday schedule (2am UTC / 9am Bangkok), and manually via `workflow_dispatch`
- Fetches open issues with `gh issue list` and writes a markdown summary to the GitHub Actions job summary
- Produces no artifacts, runs no builds, and has no test steps

**There is no CI workflow that builds, lints, or tests the codebase automatically.** Tests are run locally or manually.

Turbo tasks are defined to support a CI pipeline when one is eventually added:

```jsonc
// turbo.json tasks relevant to testing
"lint":          { "dependsOn": ["^build"] }
"test":          { "dependsOn": ["^build"], "cache": false }
"test:coverage": { "dependsOn": ["^build"], "cache": false }
"test:e2e":      { "dependsOn": ["^build"], "cache": false }
```

Root script `pnpm test:all` runs `turbo test test:coverage test:e2e` across all workspaces in one command.

---

## 7. Coverage Configuration and Thresholds

Coverage is configured only in `apps/web`. `apps/api` collects coverage but sets no thresholds.

### apps/web — vitest.config.ts

```ts
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html'],
  include: ['components/**', 'lib/**'],
  exclude: ['**/*.d.ts', 'node_modules/**'],
  thresholds: {
    statements: 88,
    branches:   83,
    functions:  68,
    lines:      88,
  },
},
```

Run coverage: `pnpm --filter @vets-hub/web test:coverage`

Output: `apps/web/coverage/` (html, json, text to stdout).

### apps/api — jest.config.ts

```ts
collectCoverageFrom: ['src/**/*.ts', '!src/main.ts', '!src/**/*.module.ts'],
coverageDirectory: './coverage',
```

No thresholds set. Run coverage: `pnpm --filter @vets-hub/api test:coverage` (alias: `jest --coverage`).

---

## Quick Reference — All Test Commands

```bash
# Root — runs turbo across all workspaces
pnpm test          # vitest run + jest (unit only)
pnpm test:all      # test + coverage + e2e

# apps/web
pnpm --filter @vets-hub/web test             # vitest unit + integration
pnpm --filter @vets-hub/web test:coverage    # vitest + v8 coverage
pnpm --filter @vets-hub/web test:e2e         # playwright (Chromium)
pnpm --filter @vets-hub/web test:e2e:responsive  # @responsive tag, mobile + tablet
pnpm --filter @vets-hub/web test:e2e:ui      # Playwright UI mode
pnpm --filter @vets-hub/web lint

# apps/api
pnpm --filter @vets-hub/api test             # jest unit (43 specs)
pnpm --filter @vets-hub/api test:coverage    # jest --coverage
pnpm --filter @vets-hub/api test:e2e         # jest e2e (8 specs, needs live DB)
pnpm --filter @vets-hub/api lint
```
