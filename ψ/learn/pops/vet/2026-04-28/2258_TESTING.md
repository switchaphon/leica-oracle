# POPS Vet — Testing Infrastructure
> Audited: 2026-04-28 · Source: `ψ/learn/pops/vet/origin/`

---

## 1. Test Stack

| Layer | Tool | Version |
|-------|------|---------|
| Unit runner | Vitest | ^4.1.0 |
| Component/integration runner | Vitest (same process) | ^4.1.0 |
| DOM environment | jsdom | ^28.1.0 |
| E2E runner | Playwright | ^1.58.2 |
| Component assertions | @testing-library/react | ^16.3.2 |
| User interaction | @testing-library/user-event | ^14.6.1 |
| DOM matchers | @testing-library/jest-dom | ^6.9.1 |
| Coverage provider | V8 (built into Vitest) | — |
| Schema validation testing | Zod `.safeParse()` directly | — |
| GraphQL mock (unit) | `vi.mock('graphql-request', ...)` | — |
| GraphQL mock (E2E) | Playwright `page.route()` intercepts | — |
| GraphQL codegen | @graphql-codegen/cli + client-preset | ^6.2.1 |
| Performance audits | @lhci/cli (Lighthouse CI) | ^0.15.1 |
| Component workbench | Storybook + @storybook/react-vite | ^8.6.18 |

**No MSW.** Mocking is done with `vi.mock()` at the module boundary for unit/component tests and with `page.route()` network interception for E2E.

---

## 2. Test Directory Structure

```
src/
  __tests__/
    unit/
      hooks/          ← custom React hook tests (*.test.ts)
      lib/            ← utility library tests (graphql-client, utils)
      schemas/        ← Zod schema validation tests
      utils/          ← pure utility function tests (date, common, etc.)
    component/
      shared/         ← shared UI component tests (*.test.tsx)
      admin/
      appointment/
      owner-pet/
      pet_profile/
      queue/
    integration/
      admin/          ← full component + context integration (*.integration.test.tsx)
  test/
    setup.ts          ← global Vitest setup file

tests/
  e2e/
    *.spec.ts         ← Playwright E2E specs
    global-setup.ts   ← mints NextAuth JWT sessions into .auth/
    global-teardown.ts← optional cleanup of dev-tenant seed data
    helpers/
      auth.ts         ← loginAs() helper, role-based credential loader
      graphql-mock.ts ← mockGraphQL() + all MOCK_* fixture constants
      seed.ts         ← database seeding for integration mode
  fixtures/
    images/           ← binary assets used by upload tests
    security/
    README.md
```

Unit and component tests are **not co-located** with source files. They live exclusively under `src/__tests__/`. E2E specs live under `tests/e2e/`.

Vitest `include` glob: `src/__tests__/**/*.test.{ts,tsx}` — only `.test.` files, no `.spec.` in this tree.

---

## 3. Unit Test Conventions (Vitest)

### File naming

- Unit and component tests: `*.test.ts` / `*.test.tsx`
- Integration tests (component + context rendered together): `*.integration.test.tsx`
- E2E: `*.spec.ts` (Playwright convention)

### Import pattern

```ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
```

Globals are enabled (`globals: true` in vitest.config.ts), but the team imports explicitly from `vitest` anyway — this is the convention in every test file observed.

### Setup / teardown

```ts
beforeEach(() => {
  vi.useFakeTimers();
  mockSignIn.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});
```

Pattern: always restore real timers and all mocks in `afterEach`. The global `setup.ts` installs an automatic `afterEach(() => cleanup())` from RTL, but individual tests reinforce it where needed.

### Mocking pattern — vi.hoisted + vi.mock

The team uses the `vi.hoisted()` + `vi.mock()` pattern when a mock must be both hoisted before imports and shared across describes:

```ts
// Hoisted — runs before any import
const { mockSignIn, mockGetSession } = vi.hoisted(() => ({
  mockSignIn: vi.fn(),
  mockGetSession: vi.fn(),
}));

vi.mock('next-auth/react', () => ({
  signIn: mockSignIn,
  getSession: mockGetSession,
  useSession: vi.fn(),
}));

// Then import the module under test
import useLogin from '@/_utils/hook/useLogin';
```

For complex third-party dependencies (e.g. `graphql-request`), a full factory function replaces the class:

```ts
vi.mock('graphql-request', () => {
  function GraphQLClient(this: FakeClient, url: string, options: { headers?: ... }) {
    // stores last instance so tests can inspect header state
    lastInstance = this;
  }
  return { GraphQLClient };
});
```

### Fake timers with async hooks

A recurring pattern for hooks that contain async state transitions:

```ts
vi.useFakeTimers();

await act(async () => {
  await result.current.login({ email: 'a@b.com', password: 'pw' });
  await vi.runAllTimersAsync();   // flush all pending timers + microtasks
});
```

`vi.runAllTimersAsync()` is preferred over `waitFor` when fake timers are active — avoids the `waitFor`/fake-timer deadlock.

### Path aliases

All source imports use the `@/` alias defined in `tsconfig.json` and resolved by `vite-tsconfig-paths` in `vitest.config.ts`:

```ts
import useLogin from '@/_utils/hook/useLogin';
import { loginSchema } from '@/_pages/Login.schema';
```

---

## 4. Component Testing (React Testing Library)

All component tests use RTL's `render` + `screen` API and `userEvent.setup()`.

### Render helper pattern

```ts
const setup = (overrides?: Partial<typeof defaultProps>) => {
  const user = userEvent.setup();           // setup() not userEvent.click() directly
  const props = { ...defaultProps, ...overrides };
  render(<ConfirmAlertContainer {...props} />);
  return { user, props };
};
```

The `setup()` factory is defined at the top of each test file. This avoids repeating render logic and makes prop overrides easy per test.

### Querying

- `screen.getByTestId('modal-wrapper')` for structural elements
- `screen.getByRole('button', { name: /…/ })` for interactive elements
- `screen.getByPlaceholderText('...')` for inputs
- `screen.getByText('...')` for content assertions
- `screen.queryByTestId(...)` for absent elements (`not.toBeInTheDocument()`)

### Jest-dom matchers in use

```ts
expect(el).toBeInTheDocument();
expect(el).not.toBeInTheDocument();
expect(el).toBeDisabled();
expect(el).not.toBeDisabled();
expect(el).toHaveTextContent('...');
```

These are enabled globally by `import '@testing-library/jest-dom'` in `src/test/setup.ts`.

### userEvent pattern

```ts
const { user } = setup({ confirmKeyword: 'ลบ' });
await user.type(getKeywordInput(), 'ลบ');    // type character-by-character
await user.click(getActionButton());         // fire click with real event bubbling
```

Always `await` userEvent calls. `userEvent.setup()` (v14) replaces the old `userEvent.type()` directly.

### Mocking child components

When a component depends on a complex modal wrapper, the team mocks the child at the module level and exposes a simplified `data-testid` interface:

```ts
vi.mock('@/_components/shared/Modals', () => ({
  Modals: ({ children, onNextAction, disabled, open }) => {
    if (!open) return null;
    return (
      <div data-testid='modal-wrapper'>
        <div data-testid='modal-content'>{children}</div>
        <button data-testid='modal-next-action' onClick={onNextAction} disabled={disabled}>
          ยืนยัน
        </button>
      </div>
    );
  },
}));
```

---

## 5. E2E Testing (Playwright)

### Configuration: playwright.config.ts

| Setting | Value |
|---------|-------|
| Test directory | `tests/e2e/` |
| Browsers | Chromium only (`devices['Desktop Chrome']`) |
| Workers in CI | 1 (sequential) |
| Workers locally | undefined (auto — parallel) |
| Retries in CI | 2 |
| Base URL | `process.env.BASE_URL \|\| 'http://localhost:3000'` |
| Trace | `on-first-retry` |
| Screenshot | `only-on-failure` |
| Video | `on` (preserved for all runs by default) |
| Output preservation | `always` (overridable via `PLAYWRIGHT_PRESERVE_OUTPUT`) |
| Reporter | HTML |

### Two test modes

**Mock mode** (default, no backend required):
```bash
pnpm test:e2e
```
Uses `.auth/staff.json` (minted by `global-setup.ts`) and intercepts GraphQL via `mockGraphQL()`.

**Integration mode** (hits real `api-dev.pops.vet`):
```bash
pnpm e2e:integration    # sets BACKEND_RUNNING=true automatically
```
Requires real credentials in `.env.test`. Most tests are guarded with `test.skip(!process.env.BACKEND_RUNNING, '...')`.

### Auth state strategy

`global-setup.ts` runs before every suite and mints **two** NextAuth JWT sessions without a running backend:

- `.auth/staff.json` — `role: 'staff'`, `tenantCode: TC001`
- `.auth/admin.json` — `role: 'OWNER'`, `tenantCode: TC001`

The JWT is encoded using `next-auth/jwt`'s `encode()` with the same `NEXTAUTH_SECRET` as the server. The embedded `accessToken` is a hand-crafted fake JWT with `exp: 9_999_999_999` (year 2286) — the frontend only reads `exp` via base64 decode, it does not verify the signature.

Tests opt in via:
```ts
test.use({ storageState: '.auth/staff.json' });
```

For integration tests that need a real session, the `loginAs(browser, role)` helper performs a full UI login and caches the result in `.auth/<role>.json` for **10 minutes** (guards against stale JWT_ACCESS_TTL of 15 min on staging).

### GraphQL mocking pattern (E2E)

```ts
import { mockGraphQL, MOCK_QUEUES, MOCK_QUEUE_SUMMARY } from './helpers/graphql-mock';

test('renders stat cards', async ({ page }) => {
  // Must be called BEFORE page.goto()
  await mockGraphQL(page, {
    QueueList: MOCK_QUEUES,
    QueueSummary: MOCK_QUEUE_SUMMARY,
  });
  await page.goto('/dashboard');
  await expect(page.getByText('คิวบริการวันนี้')).toBeVisible({ timeout: 5_000 });
});
```

`mockGraphQL()` uses `page.route('**/service', ...)` to intercept POST requests to the GraphQL gateway and return in-memory fixture objects. Supports `{ delay: ms }` option to simulate loading states.

### Annotated representative E2E test

```ts
// tests/e2e/dashboard.spec.ts

import { test, expect } from '@playwright/test';
import { mockGraphQL, MOCK_QUEUES, MOCK_QUEUE_SUMMARY, ... } from './helpers/graphql-mock';

// Unauthenticated guard — no storageState
test.describe('Dashboard Page -- unauthenticated (smoke)', () => {
  test('redirects to /login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);  // middleware redirect check
  });
});

// Authenticated group — loads pre-minted session from global-setup
test.describe('Dashboard Page -- stat cards (smoke)', () => {
  test.use({ storageState: '.auth/staff.json' });

  test('renders 5 stat cards with correct headings', async ({ page }) => {
    // 1. Intercept GraphQL BEFORE navigation
    await mockGraphQL(page, {
      QueueList: MOCK_QUEUES,
      QueueSummary: MOCK_QUEUE_SUMMARY,
      AppointmentList: MOCK_APPOINTMENTS,
      AppointmentSummary: MOCK_APPOINTMENT_SUMMARY,
      OwnerSummary: MOCK_OWNER_SUMMARY,
    });

    // 2. Navigate
    await page.goto('/dashboard');

    // 3. Assert visible Thai-language UI strings
    await expect(page.getByText('คิวบริการวันนี้')).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('นัดหมายวันนี้')).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('พักรักษาตัว')).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('เจ้าของ').first()).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('สัตว์เลี้ยง').first()).toBeVisible({ timeout: 5_000 });
  });
});
```

### No Page Object Model

Tests are imperative — `page.getByRole(...)`, `page.getByText(...)`, `page.goto()` directly in the test body. The only abstraction layer is the `loginAs()` helper and `mockGraphQL()` helper. No POM classes exist.

### No visual regression

No screenshot comparison, no Percy, no Chromatic integration. Assertions are text/URL/role-based.

### Env var injection

```ts
// playwright.config.ts
try {
  process.loadEnvFile('.env.test');   // Node 22+ built-in; falls back silently in CI
} catch { /* file absent in CI */ }
```

The same `.env.test` is loaded in both the config process and in `global-setup.ts` (which runs in a separate worker and re-loads the file itself).

---

## 6. Storybook

### Commands

```bash
pnpm storybook          # dev server on :6006
pnpm build-storybook    # static build
```

### Configuration

- Framework: `@storybook/react-vite` (Vite, not Webpack)
- Stories glob: `src/**/*.stories.@(ts|tsx)` — co-located with source components
- Static assets: served from `public/`

### Story conventions (CSF3 + autodocs)

```ts
import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';

const meta: Meta<typeof Button> = {
  title: 'Shared/Button',
  component: Button,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],      // generates props table automatically
  args: { onClick: fn() }, // shared spied arg
};
export default meta;

type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: { children: 'นัดหมาย', variant: 'default' },
};
```

Format: CSF3 (`StoryObj`) with `args`. No MDX stories found. `tags: ['autodocs']` is used on shared components to generate the controls panel automatically.

### Addons

| Addon | Purpose |
|-------|---------|
| `@storybook/addon-essentials` | Controls, Actions, Viewport, Docs, Backgrounds, Toolbars |
| `@storybook/addon-interactions` | `play()` function testing inside stories |
| `@storybook/addon-links` | Cross-story navigation |

No a11y addon (`@storybook/addon-a11y`) installed. No Storybook test runner (no `@storybook/test-runner` in devDependencies).

### Next.js module mocks

Storybook's Vite config aliases away Node-heavy Next.js modules so stories render in-browser:

```ts
'next/image'      → .storybook/mocks/next-image.tsx
'next/navigation' → .storybook/mocks/next-navigation.ts
'next/headers'    → .storybook/mocks/next-headers.ts
'next-auth/react' → .storybook/mocks/next-auth-react.ts
'next-runtime-env'→ .storybook/mocks/next-runtime-env.ts
```

`process.env` is polyfilled with `NEXT_PUBLIC_USE_MOCK=true` so stories render without a live backend.

---

## 7. Coverage Policy

Coverage is collected only over a targeted subset — not the entire codebase.

**Included paths:**
- `src/app/_utils/**/*.{ts,tsx}` — shared utilities
- `src/app/_assets/lib/graphql-client.ts` — GraphQL client singleton

**Explicitly excluded from coverage:**
- GraphQL hook wrappers (`hook/appointment.ts`, `hook/owner.ts`, etc.) — rationale: testing these reduces to verifying a mocked `request()` returns what the mock returned, which is not useful signal.
- React context providers — covered by component integration tests.
- `src/app/_utils/**/index.ts` (barrel files)
- `src/app/_utils/**/*.d.ts` (type declarations)

**Thresholds (global):**

| Metric | Threshold |
|--------|-----------|
| Lines | 70% |
| Statements | 70% |
| Functions | 60% |
| Branches | 60% |

Coverage reporters: `text` (console), `lcov`, `html`, `json-summary`. Output: `./coverage/`.

**Run coverage:**
```bash
pnpm test:coverage
```

No per-file thresholds are configured. Thresholds are enforced globally across the included paths only.

---

## 8. Lighthouse Budgets

Two configs. All assertions are `warn` severity — they fail the CI step with a warning but do not hard-block unless configured otherwise in the pipeline.

### lighthouserc.json — baseline (public routes only)

Audits `/login`, 3 runs, desktop preset.

| Metric | Budget |
|--------|--------|
| Performance score | ≥ 0.80 |
| Accessibility score | ≥ 0.90 |
| Best Practices score | ≥ 0.90 |
| SEO score | ≥ 0.85 |
| Largest Contentful Paint | ≤ 2500 ms |
| Cumulative Layout Shift | ≤ 0.1 |
| Total Blocking Time | ≤ 300 ms |
| Time to Interactive | ≤ 3800 ms |
| Speed Index | ≤ 3400 ms |
| First Contentful Paint | ≤ 1800 ms |

### lighthouserc.full.json — authenticated routes (requires backend)

Audits 7 routes: `/login`, `/dashboard`, `/owner-pet`, `/queue`, `/appointment`, `/veterinarian`, `/setting`. Uses `preset: 'lighthouse:recommended'` plus the same numeric budgets as above. Requires `.auth/staff.json` (from Playwright global-setup) and a running backend.

Disabled checks in full config: `csp-xss`, `uses-http2`, `bf-cache`, `errors-in-console`.

**Commands:**
```bash
pnpm lhci          # baseline only (/login)
pnpm lhci:full     # all authenticated routes
pnpm perf:baseline # build + bundle-size check + lhci baseline in one shot
```

---

## 9. Test Fixtures and Data Strategy

### Approach: inline MOCK_* constants, no faker

The team does not use faker or factory libraries. All fixture data is hand-authored as TypeScript constants in `tests/e2e/helpers/graphql-mock.ts`. Each constant matches the GraphQL type shapes from `@/_types/graphql`.

Example (from graphql-mock.ts):
```ts
export const MOCK_PETS = [
  {
    pet: {
      id: 'pet-001',
      hn_no: 'HN-001',
      name_th: 'มาวิน',
      name_en: 'Mawin',
      species: 'cat',
      breed: 'British shorthair',
      age: 3,
      // ...all fields typed to match PetGQL
    },
    primary_owner: {
      id: 'owner-001',
      first_name: 'สมชาย',
      last_name: 'ใจดี',
    },
  },
];
```

For unit tests, fixtures are declared locally inside the test file (no shared fixture registry for unit tests).

### GraphQL codegen

Types for all GQL operations are generated into `src/__generated__/` using:

```bash
pnpm codegen           # one-shot
pnpm codegen:watch     # watch mode
```

Config: `codegen.ts`. Schema is introspected from the live gateway (`NEXT_PUBLIC_POPS_API_URL/service` or `http://localhost:4000/service`). `namingConvention: 'keep'` preserves `snake_case` field names.

**Critical gotcha:** the codegen gateway must be reachable for generation. If offline, use a locally exported SDL file.

---

## 10. CI Pipeline

No `.gitlab-ci.yml` was found in this repository — the vet frontend does not have a committed CI pipeline config at the time of this audit. CI is referenced in docs (e.g., "POPS-207" for Lighthouse) but the pipeline definition is not in this repo.

**Scripts that CI would invoke (inferred from package.json + docs):**

```bash
# 1. Install
pnpm install
npx playwright install chromium

# 2. Lint
pnpm lint

# 3. Unit + component tests (always, no backend needed)
pnpm test:coverage     # runs Vitest + collects V8 coverage

# 4. E2E — mock mode (always, no backend needed)
pnpm test:e2e

# 5. E2E — integration mode (gated on BACKEND_RUNNING=true + credentials)
pnpm e2e:integration   # runs only in environments with api-dev access

# 6. Lighthouse baseline
pnpm lhci              # audits /login only

# 7. Lighthouse full (gated on backend + .auth/staff.json)
pnpm lhci:full
```

CI-specific Playwright flags:
- `forbidOnly: true` — `test.only()` causes the suite to fail
- `retries: 2` — each test retried twice on failure
- `workers: 1` — sequential execution (avoids api-dev rate limiting)
- `E2E_CLEANUP_AFTER=true` — triggers teardown cleanup of seed data

---

## 11. Known Gotchas

### Must run codegen before tests (when types change)
`src/__generated__/` is gitignored. If you pull schema changes from the backend, run `pnpm codegen` first. Missing generated types cause TypeScript compile errors in tests.

### Playwright auth session is fresh per run (mock mode)
`global-setup.ts` runs before every `pnpm test:e2e` and regenerates `.auth/staff.json` and `.auth/admin.json`. Sessions are not stale in mock mode because the JWT `exp` is set to year 2286. However:

### loginAs() cache expires in 10 minutes (integration mode)
When `loginAs(browser, role)` is called in integration mode, it caches the `.auth/<role>.json` file and reuses it for 10 minutes. After 10 minutes it performs a fresh UI login. This guards against stale JWT_ACCESS_TTL (15 min on staging). If you see unexplained 401s, delete `.auth/` and re-run.

### api-dev rate limiting
The dev backend throttles login attempts. Running integration tests with `workers > 1` will trigger the Thai rate-limit message (`ลองเข้าสู่ระบบบ่อยเกินไป`). Use `test.describe.configure({ mode: 'serial' })` on login-heavy specs and keep `workers: 1` in CI.

### waitFor + fake timers deadlock
Do not use `waitFor` inside tests that have `vi.useFakeTimers()` active. Use `vi.runAllTimersAsync()` inside `act()` instead. All hook tests in this codebase follow this pattern.

### NextAuth URL required in jsdom
Without `NEXTAUTH_URL` set, components using `useSession` will throw `TypeError: Failed to parse URL from /api/auth/_log`. The global `setup.ts` sets `NEXTAUTH_URL=http://localhost:3000` — do not remove this line.

### window.matchMedia not in jsdom
`jsdom` does not implement `window.matchMedia`. The global `setup.ts` installs a stub. Any component calling `useMediaQuery` or similar hooks will silently return `matches: false`. Tests that care about breakpoint behaviour must override `window.matchMedia` with a custom `vi.fn()` mock.

### GraphQL mock must precede page.goto()
In E2E tests, call `await mockGraphQL(page, {...})` before `await page.goto(...)`. The route handler is registered synchronously, but if you call `goto` first, the first GraphQL request will have already been made before the intercept is in place.

### Zod schemas tested as re-declarations
`forgotPasswordSchema` and `changePasswordSchema` are inlined in their component files and not exported. The unit tests re-declare minimal copies. If you change the schema in the component, you must also update the test copy, or the test will pass with a stale schema.

### Integration test label
Tests that need a real backend are marked `*.integration.test.tsx` (in `src/__tests__/integration/`) or contain explicit `test.skip(!process.env.BACKEND_RUNNING, ...)` guards (in E2E specs). Plain `*.test.ts` files should always pass with no external services.

---

*Generated by Leica — Static audit of origin source. No tests were run.*
