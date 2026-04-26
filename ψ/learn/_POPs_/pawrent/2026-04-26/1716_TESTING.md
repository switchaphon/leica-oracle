# Pawrent Testing & Quality Patterns

## Overview

Pawrent is a Next.js 16.2.2 pet care application with comprehensive unit, integration, and E2E testing. The project uses **Vitest** for unit/integration tests and **Playwright** for E2E tests, with strict coverage thresholds (90% statements/functions/lines, 85% branches).

Test files: **68 test files** containing ~1,120 test cases across the `__tests__/` and `e2e/` directories.

---

## 1. Test Structure and Conventions

### File Organization

```
pawrent/
├── __tests__/                      # Unit & integration tests (68 files)
│   ├── api-*.test.ts              # API route handlers
│   ├── *.test.tsx                 # React components
│   ├── *.test.ts                  # Utilities, validations, helpers
│   ├── db.test.ts                 # Database layer
│   └── validations.test.ts         # Zod schema validation
├── e2e/                            # End-to-end tests (12 files)
│   ├── *.spec.ts                  # Playwright specs
│   ├── auth.setup.ts              # Authentication setup
│   └── .auth/user.json            # Saved session state
├── vitest.config.ts               # Unit test config
├── vitest.setup.ts                # Global test setup
├── playwright.config.ts           # E2E test config
└── package.json                   # Test scripts
```

### Naming Conventions

- **Unit/Integration tests**: `{module}.test.ts` or `{component}.test.tsx`
- **E2E tests**: `{feature}.spec.ts`
- **API route tests**: `api-{resource}.test.ts` (e.g., `api-post.test.ts`, `api-alerts-push.test.ts`)
- **Component tests**: `{ComponentName}.test.tsx`
- **Utility/validation tests**: `{utility-name}.test.ts`

### Test File Structure Pattern

Every test file follows this pattern:

```typescript
/**
 * Test description and strategy
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ───────────────────────────────────────────────────
// Mocks (in order: external deps, APIs, DB, subcomponents)
// ───────────────────────────────────────────────────

vi.mock("@/lib/module", () => ({ ... }));

// ───────────────────────────────────────────────────
// Import tested module AFTER mocks
// ───────────────────────────────────────────────────

import { functionToTest } from "@/lib/module";

// ───────────────────────────────────────────────────
// Test setup and helpers
// ───────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
});

// ───────────────────────────────────────────────────
// Tests grouped by functionality
// ───────────────────────────────────────────────────

describe("Feature Name", () => {
  it("should do something", () => {
    expect(...).toBe(...);
  });
});
```

---

## 2. Test Utilities and Helpers

### Mock Factory Pattern

The codebase uses a sophisticated **mock factory** pattern for chainable Supabase queries. This is critical for testing database-like operations.

#### Example: Database Chain Mock (`db.test.ts`)

```typescript
// Helper to build chainable mocks
function chain(terminalValue: unknown, terminalMethod = "single") {
  const obj: Record<string, unknown> = {};
  const methods = [
    "select",
    "insert",
    "update",
    "delete",
    "upsert",
    "eq",
    "gte",
    "in",
    "order",
    "limit",
  ];
  for (const m of methods) {
    obj[m] = vi.fn(() => obj);  // Each method returns the chain
  }
  obj[terminalMethod] = vi.fn(() => Promise.resolve(terminalValue));
  obj.maybeSingle = vi.fn(() => Promise.resolve(terminalValue));
  return obj;
}

// Usage in tests:
beforeEach(() => {
  const result = { id: "123", name: "Luna" };
  mockFrom.mockReturnValue({
    select: () => chain(result, "single"),
  });
});
```

#### Example: API Chain Mock (`api-post.test.ts`)

```typescript
const makeEqChain = () => {
  const capturedArgs: Array<[string, unknown]> = [];
  const chain: Record<string, unknown> = {
    _capturedArgs: capturedArgs,
  };
  chain.eq = vi.fn((...args: [string, unknown]) => {
    capturedArgs.push(args);  // Track filter conditions
    return chain;
  });
  chain.select = vi.fn(() => ({ single: mockSingle, maybeSingle: mockMaybeSingle }));
  chain.order = vi.fn(() => chain);
  chain.limit = vi.fn(() => chain);
  return chain;
};
```

### Helper Functions in Tests

Common patterns found across tests:

**1. NextRequest Factory** (for API route testing):
```typescript
function makeRequest(method: string, body: unknown, withAuth = true): NextRequest {
  return new NextRequest("http://localhost/api/post", {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(withAuth ? { Authorization: "Bearer fake-token" } : {}),
    },
    body: JSON.stringify(body),
  });
}

function makeGetRequest(params: Record<string, string> = {}, withAuth = true): NextRequest {
  const url = new URL("http://localhost/api/post");
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  return new NextRequest(url, { method: "GET", headers: { ... } });
}
```

**2. Test Data Generators**:
```typescript
const VALID_UUID = "123e4567-e89b-12d3-a456-426614174000";
const WEBHOOK_SECRET = "test-webhook-secret";
const VALID_URL = "https://example.com/photo.jpg";

const validLostAlert = {
  pet_id: VALID_UUID,
  lost_date: "2026-04-13",
  lost_time: "14:30:00",
  lat: 13.756,
  lng: 100.502,
  photo_urls: [VALID_URL],
  reward_amount: 5000,
};
```

### Global Setup (`vitest.setup.ts`)

Provides DOM mocks for all tests:

```typescript
import "@testing-library/jest-dom";

// ResizeObserver mock — needed by shadcn/ui components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// matchMedia mock — needed by responsive/PWA components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
```

---

## 3. Mocking Patterns

### 1. External API Mocking (Supabase, LINE)

**Supabase Client Mock** (used in `db.test.ts`, `api-post.test.ts`):
```typescript
vi.mock("@/lib/supabase", () => ({
  supabase: {
    from: (...args: unknown[]) => mockFrom(...args),
    rpc: (...args: unknown[]) => mockRpc(...args),
    storage: {
      from: (...args: unknown[]) => mockStorageFrom(...args),
    },
  },
}));
```

**LINE Messaging Mock** (used in `api-alerts-push.test.ts`):
```typescript
const mockMulticastMessage = vi.fn().mockResolvedValue(3);
const mockIsQuietHours = vi.fn().mockReturnValue(false);

vi.mock("@/lib/line-messaging", () => ({
  multicastMessage: (...args: unknown[]) => mockMulticastMessage(...args),
  isQuietHours: (...args: unknown[]) => mockIsQuietHours(...args),
}));
```

### 2. Rate Limiting Bypass

All API tests bypass rate limiting for predictability:
```typescript
vi.mock("@/lib/rate-limit", () => ({
  createRateLimiter: () => ({}),
  checkRateLimit: async () => null,  // Always allow
  getClientIp: () => "127.0.0.1",
}));
```

### 3. Component Mocking

React component tests mock child components:

```typescript
// From create-pet-form.test.tsx
vi.mock("@/components/image-cropper", () => ({
  ImageCropper: ({
    onCropComplete,
    onCancel,
  }: {
    onCropComplete: (b: Blob) => void;
    onCancel: () => void;
  }) => (
    <div data-testid="image-cropper">
      <button onClick={() => onCropComplete(new Blob(["img"], { type: "image/jpeg" }))}>
        Crop
      </button>
      <button onClick={onCancel}>Cancel Crop</button>
    </div>
  ),
}));

vi.mock("@/components/searchable-select", () => ({
  SearchableSelect: ({ value, onChange, placeholder }: any) => (
    <select
      data-testid={`searchable-select-${placeholder}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
    </select>
  ),
}));
```

### 4. Authentication Context Mocking

```typescript
vi.mock("@/components/liff-provider", () => ({
  useAuth: () => ({
    user: {
      id: "user-1",
      email: null,
      full_name: null,
      avatar_url: null,
      line_user_id: "U123",
      line_display_name: "Test",
      created_at: "",
    },
    loading: false,
    isInLiff: false,
    signOut: vi.fn(),
  }),
}));
```

### 5. Mock Clearing Strategy

All tests use `beforeEach` with `vi.clearAllMocks()`:
```typescript
beforeEach(() => {
  vi.clearAllMocks();  // Reset all mock call counts and implementations
});
```

This ensures test isolation — each test starts fresh without mock state from previous tests.

---

## 4. Coverage Approach

### Configuration (`vitest.config.ts`)

```typescript
export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["lib/**", "app/api/**"],
      exclude: [
        "node_modules",
        "e2e",
        "**/*.d.ts",
        // Pure type declarations — no runtime code
        "lib/types/**",
        // Barrel re-exports
        "lib/validations/index.ts",
        // Below thresholds
        "app/api/posts/route.ts",
        "app/api/profile/route.ts",
        // Edge runtime — not testable in jsdom
        "app/api/og/**",
      ],
      thresholds: {
        statements: 90,
        branches: 85,
        functions: 90,
        lines: 90,
        perFile: true,  // Each file must meet thresholds
      },
    },
  },
});
```

### Coverage Strategy

**What's tested:**
- All database layer functions (`lib/db.ts`)
- All API route handlers (`app/api/**`)
- Validation schemas (Zod)
- Utility functions
- Complex React components

**What's excluded:**
- Type-only files (`lib/types/**`)
- Barrel exports (`lib/validations/index.ts`)
- Edge runtime code (`app/api/og/**`)
- Routes below the 85% branch threshold (noted in comments for future improvement)

**Coverage reports** are generated as LCOV format and uploaded as CI artifacts.

---

## 5. E2E Testing

### Test Framework: Playwright

Located in `/e2e` directory with configuration in `playwright.config.ts`.

#### Configuration

```typescript
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,  // Fail if .only() left in CI
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,  // Serial in CI
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",  // Save traces on failure
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
    {
      name: "firefox",
      use: { browserName: "firefox" },
    },
  ],
  webServer: {
    command: "npm run dev -- --webpack",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

#### Test Files (12 total)

| File | Purpose |
|------|---------|
| `auth-flow.spec.ts` | LIFF authentication, route loading |
| `authenticated-flows.spec.ts` | Logged-in user workflows |
| `lost-pet-flow.spec.ts` | Community hub, lost pet wizard navigation |
| `home-dashboard.spec.ts` | Home page content and layout |
| `hospital-map.spec.ts` | Hospital locator feature |
| `profile-page.spec.ts` | User profile editing |
| `public-pages.spec.ts` | Static/public page loads |
| `pet-passport.spec.ts` | Pet vaccination/health records |
| `bottom-nav.spec.ts` | Navigation menu |
| `feedback-page.spec.ts` | Feedback form submission |
| `offline-page.spec.ts` | Offline mode behavior |
| `auth.setup.ts` | Session persistence (setup fixture) |

#### Example E2E Test: Auth Flow

```typescript
// From auth-flow.spec.ts
import { test, expect } from "@playwright/test";

async function expectRouteLoads(page: import("@playwright/test").Page, route: string) {
  // waitUntil: "commit" avoids racing LIFF redirect
  const res = await page.goto(route, { waitUntil: "commit" });
  expect(res?.status() ?? 0).toBeLessThan(500);
  await expect(page.locator("body")).toBeVisible();
}

test.describe("Authentication flow (unauthenticated via LIFF)", () => {
  test("home page loads without crashing", async ({ page }) => {
    await expectRouteLoads(page, "/");
  });

  test("/pets loads without crashing when unauthenticated", async ({ page }) => {
    await expectRouteLoads(page, "/pets");
  });
});
```

#### Example E2E Test: Lost Pet Flow

```typescript
// From lost-pet-flow.spec.ts
test.describe("Lost Pet Flow — Community Hub", () => {
  test("/sos redirects to /post", async ({ page }) => {
    await page.goto("/sos");
    await expect(page).toHaveURL(/\/post/);
  });

  test("community hub shows tab navigation", async ({ page }) => {
    await page.goto("/post");
    await expect(page.getByText(/หาย|lost/i).first()).toBeVisible({ timeout: 10000 });
  });

  test("tab switching between Lost and Found tabs", async ({ page }) => {
    await page.goto("/post");
    await expect(page.locator("body")).toBeVisible({ timeout: 10000 });

    const foundTab = page.getByText(/พบ|found/i).first();
    if (await foundTab.isVisible()) {
      await foundTab.click();
      await expect(page.locator("body")).toBeVisible();
    }
  });

  test("floating CTA button is visible on community hub", async ({ page }) => {
    await page.goto("/post");
    const fab = page.locator('a[href="/post/lost"], button').filter({
      hasText: /ประกาศ|report|แจ้ง|lost/i,
    });
    const fabCount = await fab.count();
    expect(fabCount).toBeGreaterThanOrEqual(0);
  });
});
```

#### Authentication Setup (`auth.setup.ts`)

For authenticated E2E tests:

```typescript
import { test as setup, expect } from "@playwright/test";

const authFile = path.join(__dirname, ".auth", "user.json");

setup("authenticate", async ({ page }) => {
  const email = process.env.E2E_TEST_EMAIL;
  const password = process.env.E2E_TEST_PASSWORD;

  if (!email || !password) {
    setup.skip();
    return;
  }

  await page.goto("/");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page.locator('nav, [data-testid="feed"]')).toBeVisible({ timeout: 15000 });

  // Save session for reuse across tests
  await page.context().storageState({ path: authFile });
});
```

**Note:** To enable authenticated tests:
1. Create test account in Supabase
2. Set `E2E_TEST_EMAIL` and `E2E_TEST_PASSWORD` environment variables
3. Uncomment "setup" project in `playwright.config.ts`

---

## 6. CI/CD Testing

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

The CI pipeline has **4 sequential jobs**:

#### 1. Static Analysis
```yaml
static-analysis:
  name: Static Analysis
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: 20
        cache: npm
    - run: npm ci
    - run: npm run format:check    # Prettier
    - run: npm run lint            # ESLint
    - run: npx tsc --noEmit        # TypeScript
```

#### 2. Unit & Integration Tests
```yaml
test:
  name: Unit & Integration Tests
  needs: [static-analysis]
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: 20
        cache: npm
    - run: npm ci
    - run: npm run test:coverage   # Vitest with coverage
    - name: Upload coverage
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: coverage-report
        path: coverage/
```

#### 3. Build
```yaml
build:
  name: Build
  needs: [test]
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - name: Cache Next.js build
      uses: actions/cache@v4
      with:
        path: .next/cache
        key: nextjs-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    - run: npm run build
```

#### 4. E2E Tests
```yaml
e2e:
  name: E2E Tests
  runs-on: ubuntu-latest
  needs: [build]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - name: Cache Playwright browsers
      uses: actions/cache@v4
      with:
        path: ~/.cache/ms-playwright
        key: playwright-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    - name: Install Playwright
      run: npx playwright install --with-deps chromium firefox
    - run: npx playwright test --project=chromium --project=firefox
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: playwright-report
        path: playwright-report/
```

### Test Scripts (`package.json`)

```json
{
  "scripts": {
    "test": "vitest run",                    // Single run
    "test:coverage": "vitest run --coverage", // With coverage report
    "test:watch": "vitest",                  // Watch mode
    "test:e2e": "playwright test",           // E2E tests
    "lint": "eslint",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

### CI Environment Setup

**Dummy Supabase credentials** are provided for build-time:
```yaml
env:
  NEXT_PUBLIC_SUPABASE_URL: https://placeholder.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY: placeholder-anon-key
```

This allows the build to succeed even without real Supabase credentials (tests use mocks).

### Test Execution

**Concurrency Control:**
```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true  # Cancel old runs on new push
```

**Playwright in CI:**
- Runs with serial worker (`workers: 1`)
- Retries failed tests up to 2 times
- Captures traces on first retry for debugging
- Tests run against both Chromium and Firefox

---

## Key Patterns & Best Practices

### 1. Test Isolation
- Every test uses `beforeEach(() => vi.clearAllMocks())` to reset mocks
- No shared state between tests
- Tests can run in any order

### 2. Chainable Mock Builder
The `chain()` function pattern is used throughout for complex Supabase query chains. This enables fluent API mocking while maintaining control over the final return value.

### 3. Mock-First Strategy
Tests mock all external dependencies (Supabase, LINE, rate limiters) before importing the code under test. This ensures:
- Tests are deterministic
- No network calls during tests
- Fast execution
- Easy to test error paths

### 4. Validation-Driven Testing
Zod schemas are tested exhaustively with boundary cases:
```typescript
it("should accept weight of exactly 500 (max boundary)", () => {
  const result = petSchema.safeParse({ ...validPet, weight_kg: 500 });
  expect(result.success).toBe(true);
});

it("should reject weight above 500", () => {
  const result = petSchema.safeParse({ ...validPet, weight_kg: 500.1 });
  expect(result.success).toBe(false);
});
```

### 5. Component Testing
React components are tested with:
- User event simulation (`@testing-library/user-event`)
- DOM queries via accessible roles
- Mock child components for focus testing
- Mock API/context providers

### 6. E2E Testing Strategy
- Tests are **smoke tests** (page loads without crashing)
- No authentication required (public routes tested by default)
- Authenticated tests can be enabled via environment variables
- Tests use Thai language selectors matching i18n keys
- Timeouts are generous (10s) to account for network latency

---

## Coverage Summary

- **68 unit/integration test files**
- **12 E2E test files**
- **~1,120 test cases**
- **90% statement/function/line coverage** (required per file)
- **85% branch coverage** (required per file)
- **Test execution time:** ~30-60s locally, <5m in CI with retries

Tests provide confidence for:
- Database operations
- API route handling
- User input validation
- Component rendering
- Cross-browser compatibility
- Public-facing page loads
