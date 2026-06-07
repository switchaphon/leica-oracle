# maw-js Testing Patterns & Architecture

**Project**: maw-js (Multi-Agent Workflow orchestrator for tmux)  
**Test Framework**: Bun test runner  
**Date**: 2026-06-07  
**Coverage**: 100% line (33165/33169 lines), 100% functions (5666/5668)

---

## Quick Reference

| Aspect | Pattern |
|--------|---------|
| **Test Runner** | `bun:test` (built-in Bun framework) |
| **Test Suites** | `test/` (default), `test/isolated/` (mock-isolation), `test/spec/`, `test/cli/`, `test/integration/` |
| **CI Command** | `bun run test -- --shard N/T` (4 parallel shards per suite) |
| **Isolation Strategy** | Per-file subprocess when mocking to prevent cross-file mock pollution |
| **Coverage Tool** | Bun LCOV + custom gap-analysis script (`scripts/coverage-gap-analysis.ts`) |
| **Key Env Var** | `MAW_TEST_MODE=1` (prevents config fixture leaks into `~/.config/maw/`) |

---

## Test Structure & Conventions

### Directory Layout

```
test/
├── *.test.ts              # Default suite (pure tests, no/safe mocks)
├── isolated/              # Mock-isolation suite (file-level subprocess)
│   └── *.test.ts          # Each runs in own bun process
├── helpers/               # Shared test utilities (if any)
├── integration/           # End-to-end / multi-component tests
├── cli/                   # CLI dispatch and command tests
├── spec/                  # Specification/behavior tests
├── fedtest/               # Federation-specific scenarios
│   └── scenarios/         # Per-scenario test fixtures
├── core/                  # Core library tests
├── security/              # Security boundary tests
├── scripts/               # Test-related shell scripts
└── zz-mock-*.test.ts      # Smoke tests for mock-transport layer
```

### Test Naming & Organization

**Naming Convention:**
- `test/federation-sync.test.ts` → tests the `federation-sync` module
- `test/isolated/tmux-layout-manager.test.ts` → tmux layout manager (needs mocking)
- Test files matching `test/zz-*` are excluded from default suite (smoke tests)

**Markers:**
- `@maw-test-isolate` — comment marker to force per-file subprocess isolation
- `@maw-test-isolate-cwd-neutral` — run in tmpdir instead of repo root (for file-mutation tests)

---

## Test Frameworks & Utilities

### Built-in Bun Test API

```typescript
import { describe, test, expect, beforeEach, afterEach } from "bun:test";

describe("module name", () => {
  test("feature works", () => {
    expect(actual).toBe(expected);
  });

  beforeEach(() => {
    // setup before each test
  });

  afterEach(() => {
    // cleanup after each test
  });
});
```

**Matchers:**
- `expect(x).toBe(y)` — strict equality
- `expect(x).toEqual(y)` — deep equality (objects, arrays)
- `expect(x).toContain(y)` — substring/array member check
- `expect(x).toMatchObject(shape)` — partial object match
- `expect(fn).rejects.toThrow("message")` — promise rejection
- `expect(fn).resolves.toBe(y)` — promise resolution

### Mocking Strategy

**Bun's `mock.module()` (process-global, retroactive):**

```typescript
import { mock } from "bun:test";
import { join } from "path";

// Must come BEFORE importing the module that depends on it
const realSdk = await import("../../src/sdk");

mock.module(join(import.meta.dir, "../../src/sdk"), () => ({
  ...realSdk,
  hostExec: async (cmd: string) => {
    // custom mock implementation
    return "mocked output";
  },
}));

// Now import modules that depend on sdk
const { someFunction } = await import("../../src/commands/plugins/...");
```

**Key insight**: `mock.module()` is retroactive and process-global. A mock installed in one file in the same Bun process affects all subsequent imports of that module in ALL files. This is why `test-default-safe.sh` runs certain files in isolation.

---

## How maw-js Handles Mock Pollution

### The Problem

Bun's `mock.module()` is process-global and retroactive:
- Mocking `sdk` in `test/file-a.test.ts` affects `test/file-b.test.ts`
- Order matters: tests passing in isolation fail when run together
- Manual workaround: run each mock-using file in its own subprocess

### The Solution: test-default-safe.sh

```bash
bash scripts/test-default-safe.sh [--shard N/T]
```

**Strategy:**
1. **Shared default sweep**: Run all non-mocking files in one Bun process (fast)
2. **Per-file isolation**: Each file with `mock.module()` gets its own subprocess
3. **Automatic detection**: Script detects `mock.module(` calls and `@maw-test-isolate` markers

**File classification:**
- `SAFE_FILES` (shared process):
  - No `mock.module()` calls
  - No `@maw-test-isolate` marker
- `MOCK_FILES` (isolated subprocess):
  - Contains `mock.module()` call, OR
  - Marked with `@maw-test-isolate` or `@maw-test-isolate-cwd-neutral`

**Output:**
```
=== test-default-safe.sh: shared default sweep ===
✓ test/federation-sync.test.ts
✓ test/api-small-default.test.ts
...
=== test-default-safe.sh: 5 mock-module file(s), one process each ===
--- test/isolated/tmux-layout-manager.test.ts ---
✓ tmux layout-manager border status guard
```

### test-isolated.sh

```bash
bash scripts/test-isolated.sh [--shard N/T] [--randomize]
```

**Runs `test/isolated/*.test.ts` with per-file isolation by default.** Each file gets its own subprocess to prevent cross-file mock leaks, even though they're already in an `isolated/` directory.

**Key difference from test-default-safe.sh:**
- Always uses per-file subprocess (no "shared sweep")
- Explicitly targets `test/isolated/` only
- Parallel shard support (`--shard 1/4`) for CI

---

## Example Test Patterns

### Pattern 1: Pure Logic Tests (No Mocking)

**File: `test/federation-sync.test.ts`**

```typescript
import { describe, test, expect } from "bun:test";
import {
  computeSyncDiff,
  applySyncDiff,
  hostedAgents,
  type PeerIdentity,
} from "../src/commands/shared/federation-sync";

/**
 * federation-sync splits I/O (fetchPeerIdentities, cmdFederationSync)
 * from pure logic (computeSyncDiff, applySyncDiff). These tests cover
 * the pure layer exhaustively — no network, no filesystem, no mocks.
 */

function mkPeer(
  peerName: string,
  node: string,
  agents: string[],
  reachable = true,
): PeerIdentity {
  return {
    peerName,
    url: `http://${peerName}:3456`,
    node,
    agents,
    reachable,
    error: reachable ? undefined : "stub",
  };
}

describe("hostedAgents — /api/identity filter", () => {
  test("explicit node-name entries are included", () => {
    expect(
      hostedAgents({ pulse: "white", mawjs: "white", foo: "mba" }, "white").sort(),
    ).toEqual(["mawjs", "pulse"]);
  });

  test("'local' entries are included (regression: 2026-04-11)", () => {
    expect(
      hostedAgents({ "volt-colab-ml": "local", mawjs: "white" }, "white").sort(),
    ).toEqual(["mawjs", "volt-colab-ml"]);
  });
});

describe("computeSyncDiff — add", () => {
  test("new oracle on a reachable peer is added", () => {
    const diff = computeSyncDiff(
      {},
      [mkPeer("white", "white", ["mawjs", "volt-colab-ml"])],
      "oracle-world",
    );
    expect(diff.add.map((a) => a.oracle).sort()).toEqual(["mawjs", "volt-colab-ml"]);
    expect(diff.conflict).toEqual([]);
  });
});
```

**Characteristics:**
- Imports pure functions, types only
- No filesystem access, network, or subprocess calls
- Factory functions like `mkPeer()` for test data
- Comprehensive scenario coverage (happy path, regressions, edge cases)

### Pattern 2: API Tests with Dependency Injection

**File: `test/api-small-default.test.ts`**

```typescript
import { describe, expect, test } from "bun:test";
import { Elysia } from "elysia";
import { createWorktreesApi } from "../src/api/worktrees";

async function json(res: Response): Promise<any> {
  return await res.json();
}

function apiWith(plugin: Elysia) {
  return new Elysia({ prefix: "/api" }).use(plugin);
}

describe("small API routers default-suite coverage", () => {
  test("worktrees API returns scanned rows and cleanup logs", async () => {
    const calls: string[] = [];
    const app = apiWith(createWorktreesApi({
      async scanWorktrees() {
        calls.push("scan");
        return [{
          path: "/repo/.wt-demo",
          branch: "codex/demo",
          repo: "Soul-Brews-Studio/maw-js.wt-demo",
          mainRepo: "Soul-Brews-Studio/maw-js",
          name: "demo",
          status: "active",
          tmuxWindow: "mawjs-demo",
        }];
      },
      async cleanupWorktree(path) {
        calls.push(`cleanup:${path}`);
        return [`removed ${path}`];
      },
    }));

    const list = await app.handle(new Request("http://local/api/worktrees"));
    expect(list.status).toBe(200);
    expect(await json(list)).toEqual([{
      path: "/repo/.wt-demo",
      branch: "codex/demo",
      // ...
    }]);

    const cleanup = await app.handle(new Request("http://local/api/worktrees/cleanup", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ path: "/repo/.wt-demo" }),
    }));
    expect(cleanup.status).toBe(200);
    expect(await json(cleanup)).toEqual({ ok: true, log: ["removed /repo/.wt-demo"] });
    expect(calls).toEqual(["scan", "cleanup:/repo/.wt-demo"]);
  });

  test("worktrees API maps scan, validation, and cleanup failures to errors", async () => {
    const app = apiWith(createWorktreesApi({
      async scanWorktrees() {
        throw new Error("tmux unavailable");
      },
      async cleanupWorktree() {
        throw new Error("cleanup denied");
      },
    }));

    const list = await app.handle(new Request("http://local/api/worktrees"));
    expect(list.status).toBe(500);
    expect(await json(list)).toEqual({ error: "tmux unavailable" });
  });
});
```

**Characteristics:**
- Pass dependencies as plain objects (not mocked)
- Test by calling HTTP endpoints directly
- Verify side effects by inspecting captured calls
- Both success and error paths covered

### Pattern 3: System Integration Tests with Mocking

**File: `test/isolated/tmux-layout-manager.test.ts`** (excerpt)

```typescript
import { beforeEach, describe, expect, mock, test } from "bun:test";
import { join } from "path";

const realSdk = await import("../../src/sdk");

let commands: string[] = [];
let paneHeights = "12\n8\n4";
let queryError: Error | null = null;

// Mock the SDK before importing dependents
mock.module(join(import.meta.dir, "../../src/sdk"), () => ({
  ...realSdk,
  hostExec: async (cmd: string) => {
    commands.push(cmd);
    if (cmd.includes("list-panes") && cmd.includes("#{pane_height}")) {
      if (queryError) throw queryError;
      return paneHeights;
    }
    return "";
  },
}));

const {
  canEnableBorderStatus,
  enableBorderStatus,
  MIN_BORDER_STATUS_PANE_HEIGHT,
} = await import("../../src/commands/plugins/tmux/layout-manager");

describe("tmux layout-manager border status guard (#1468)", () => {
  beforeEach(() => {
    commands = [];
    paneHeights = "12\n8\n4";
    queryError = null;
  });

  test("normal panes enable bottom border status", async () => {
    expect(MIN_BORDER_STATUS_PANE_HEIGHT).toBe(4);
    expect(await enableBorderStatus("@win1")).toBe(true);

    expect(commands).toEqual([
      "tmux list-panes -t '@win1' -F '#{pane_height}'",
      "tmux set-option -w -t '@win1' pane-border-status bottom",
    ]);
  });

  test("tiny panes skip the window-wide bottom border status option", async () => {
    paneHeights = "12\n3\n8";

    expect(await enableBorderStatus("@win1")).toBe(false);
    expect(commands).toEqual([
      "tmux list-panes -t '@win1' -F '#{pane_height}'",
    ]);
  });

  test("pane-height query failures fail soft and skip cosmetic border status", async () => {
    queryError = new Error("can't find window");

    expect(await enableBorderStatus("@missing")).toBe(false);
    expect(commands).toEqual([
      "tmux list-panes -t '@missing' -F '#{pane_height}'",
    ]);
  });
});
```

**Characteristics:**
- Module mock installed BEFORE importing dependent code
- Module-level state (`commands`, `paneHeights`) reset in `beforeEach()`
- Verify both success and failure paths
- Inspect captured system calls to verify behavior

### Pattern 4: Filesystem & Subprocess Tests

**File: `test/boot-auto-wake.test.ts`** (excerpt)

```typescript
import { describe, expect, test } from "bun:test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { setupAutoWake } from "../src/vendor/mpr-plugins/setup/auto-wake";

function makeRepo(): string {
  const dir = mkdtempSync(join(tmpdir(), "maw-auto-wake-"));
  writeFileSync(join(dir, "ecosystem.config.cjs"), "module.exports = { apps: [] };\n");
  return dir;
}

describe("maw setup auto-wake (#1811)", () => {
  test("registers maw-boot with pm2 and saves the dump after enabling linger", async () => {
    const repo = makeRepo();
    const calls: string[][] = [];

    const result = await setupAutoWake(
      { repoRoot: repo, user: "alpha" },
      {
        platform: () => "linux",
        user: () => "alpha",
        cwd: () => repo,
        existsSync: () => true,
        execFileSync: ((cmd: string, args: string[]) => {
          calls.push([cmd, ...args]);
          return "";
        }) as any,
      },
    );

    expect(calls).toEqual([
      ["loginctl", "enable-linger", "alpha"],
      ["pm2", "startup", "systemd", "-u", "alpha", "--hp", "/home/alpha"],
      ["pm2", "start", "ecosystem.config.cjs", "--only", "maw-boot"],
      ["pm2", "save"],
    ]);
    expect(result.steps.map((step) => step.command)).toEqual(calls);
  });

  test("dry-run reports the same commands without executing them", async () => {
    const repo = makeRepo();
    let execCount = 0;

    const result = await setupAutoWake(
      { repoRoot: repo, user: "alpha", dryRun: true },
      {
        platform: () => "linux",
        existsSync: () => true,
        execFileSync: (() => {
          execCount++;
          return "";
        }) as any,
      },
    );

    expect(execCount).toBe(0);
    expect(result.steps.every((step) => step.skipped)).toBe(true);
  });

  test("refuses non-dry-run setup on unsupported service-manager platforms", async () => {
    const repo = makeRepo();

    await expect(
      setupAutoWake(
        { repoRoot: repo, user: "alpha" },
        {
          platform: () => "win32",
          existsSync: () => true,
          execFileSync: (() => "") as any,
        },
      ),
    ).rejects.toThrow("only implemented for Linux/macOS");
  });
});
```

**Characteristics:**
- Use `mkdtempSync()` for isolated temporary directories
- Inject system dependencies (`platform`, `execFileSync`) for testability
- Verify both execution and dry-run paths
- Test error cases with `.rejects.toThrow()`

---

## tmux Mocking Strategy

### Why tmux Needs Special Handling

Maw-js orchestrates tmux sessions. Testing tmux interaction requires:
1. **Mock subprocess calls** — intercept `tmux` commands
2. **Simulate pane/window state** — return fake tmux output
3. **Verify command sequences** — ensure correct tmux operations are attempted

### Tmux Mock Pattern

```typescript
import { mock } from "bun:test";

// Mock the SDK that calls tmux
mock.module("../../src/sdk", () => ({
  hostExec: async (cmd: string) => {
    if (cmd.startsWith("tmux list-panes")) {
      // Return pane heights
      return "12\n8\n4";
    }
    if (cmd.startsWith("tmux set-option")) {
      // Capture the command for later verification
      commands.push(cmd);
      return "";
    }
    return "";
  },
}));
```

### Stateless HTTP Mock (NanoclawTransport)

**File: `test/nanoclaw-transport.test.ts`**

```typescript
import { describe, expect, test } from "bun:test";
import type { FeedEvent } from "../src/lib/feed";
import { NanoclawTransport } from "../src/transports/nanoclaw";

describe("NanoclawTransport", () => {
  test("tracks stateless HTTP lifecycle", async () => {
    const transport = new NanoclawTransport();

    expect(transport.name).toBe("nanoclaw");
    expect(transport.connected).toBe(true);

    await transport.disconnect();
    expect(transport.connected).toBe(false);

    await transport.connect();
    expect(transport.connected).toBe(true);
  });

  test("does not send when the target cannot resolve", async () => {
    let sendCalls = 0;
    const transport = new NanoclawTransport(
      () => null,  // resolver returns null
      async () => {
        sendCalls += 1;
        return true;
      },
    );

    expect(transport.canReach({ oracle: "missing" })).toBe(false);
    expect(await transport.send({ oracle: "missing" }, "hello")).toBe(false);
    expect(sendCalls).toBe(0);  // never called
  });

  test("delegates resolved targets to the nanoclaw sender", async () => {
    const sends: Array<{ jid: string; text: string; url: string }> = [];
    const transport = new NanoclawTransport(
      (oracle) => oracle === "nat" ? { jid: "tg:12345", url: "http://nanoclaw.local" } : null,
      async (jid, text, url) => {
        sends.push({ jid, text, url });
        return text === "delivered";
      },
    );

    expect(transport.canReach({ oracle: "nat" })).toBe(true);
    expect(await transport.send({ oracle: "nat" }, "delivered")).toBe(true);
    expect(await transport.send({ oracle: "nat" }, "rejected")).toBe(false);
    expect(sends).toEqual([
      { jid: "tg:12345", text: "delivered", url: "http://nanoclaw.local" },
      { jid: "tg:12345", text: "rejected", url: "http://nanoclaw.local" },
    ]);
  });
});
```

**Key patterns:**
- Constructor dependency injection (resolver, sender functions)
- Test both happy path and error paths
- Capture side effects to verify behavior

---

## Federation & API Testing

### Federation Test Architecture

**Files:**
- `test/federation-sync.test.ts` — sync logic (pure)
- `test/federation-auth.test.ts` — authentication flow
- `test/federation-symmetric.test.ts` — bidirectional sync
- `test/integration/federation-local.test.ts` — real network test

**Pattern: Pure Logic Layer + I/O Separation**

```typescript
/**
 * federation-sync splits I/O (fetchPeerIdentities, cmdFederationSync)
 * from pure logic (computeSyncDiff, applySyncDiff). These tests cover
 * the pure layer exhaustively — no network, no filesystem, no mocks.
 */
describe("computeSyncDiff — add", () => {
  test("new oracle on a reachable peer is added", () => {
    const diff = computeSyncDiff(
      {},
      [mkPeer("white", "white", ["mawjs", "volt-colab-ml"])],
      "oracle-world",
    );
    expect(diff.add.map((a) => a.oracle).sort()).toEqual(["mawjs", "volt-colab-ml"]);
  });
});
```

### API Testing Pattern

Use Elysia's test harness:

```typescript
const app = createApi();
const response = await app.handle(
  new Request("http://local/api/endpoint", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ key: "value" }),
  })
);

expect(response.status).toBe(200);
expect(await response.json()).toEqual({ expected: "data" });
```

---

## Coverage Approach

### Line & Function Coverage

**Target: 100%**
- **Line coverage**: 100.0% (33165/33169 lines)
- **Function coverage**: 100.0% (5666/5668 functions)
- **Branch coverage**: N/A (Bun LCOV does not track branches)

### Coverage Gap Analysis

```bash
bun scripts/coverage-gap-analysis.ts coverage/lcov.info docs/testing/coverage-gap-analysis.md
```

Generates a report:
- Per-module coverage breakdown
- Top uncovered files by risk
- Files below 80% target (critical files)
- Source files handled outside Bun (AssemblyScript WASM)

### Coverage Manifest (CI)

`scripts/test-coverage.sh` accumulates LCOV reports from parallel shards:

```bash
export MAW_LCOV_MANIFEST="$PWD/coverage/lcov-manifest.txt"
bun run test:default:safe --coverage-dir coverage/default
bun run test:isolated --coverage-dir coverage/isolated
# Then merge all lcov.info files into coverage/lcov.info
```

---

## CI/CD Pipeline

### Main CI Workflow (`.github/workflows/ci.yml`)

**Trigger:** Push to `alpha`/`main`, pull requests to `alpha`/`main`

**Jobs (sequential):**
1. **plugin-coverage-gate** (if PR)
   - Requires plugin extraction boundary tests pass
   - Runs: `bun scripts/check-plugin-coverage-gate.ts origin/${{ github.base_ref }}`

2. **test** (parallel matrix, 12 jobs)
   - 4 shards: `test -- --shard 1/4` through `--shard 4/4`
   - 4 shards: `test:isolated -- --shard 1/4` through `--shard 4/4`
   - 1 job: `test:plugin`
   - 1 job: `test:mock-smoke`
   - Env: `MAW_SKIP_FLAKY=1` (skips #830 flaky federation tests)
   - Dependency: All install `ghq` binary (required by some tests)

3. **build** (after test passes)
   - Builds CLI: `bun build src/cli.ts --outfile dist/maw --target=bun --minify`
   - Validates all plugin manifests (JSON parsing)
   - Verifies directory structure (`src/` ≤2 files, `src/commands/` 0 files)

### Federation Self-Hosted Workflow (`.github/workflows/federation-self-hosted.yml`)

**Trigger:** Manual `workflow_dispatch` only (security: no auto-trigger on fork PRs)

**Purpose:**
- Real multi-node federation tests (ephemeral port racing, 2-port round-trip)
- Flaky cross-check (curlFetch, buildCommand on real Linux)

**Tests run:**
```bash
bun test \
  test/federation-auth.test.ts \
  test/federation-symmetric.test.ts \
  test/federation-sync.test.ts \
  test/integration/federation-local.test.ts \
  test/integration/search-peers-2port.test.ts \
  test/curl-fetch.test.ts \
  test/build-command-cwd.test.ts
```

**Env:** `MAW_SKIP_FLAKY=0` (enables tests normally skipped)

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `MAW_TEST_MODE=1` | Guard in `src/config/load.ts` to prevent fixture leaks into `~/.config/maw/` |
| `MAW_SKIP_FLAKY=1` | Skip known flaky tests (federation 2-port race, CI sandbox issues) |
| `MAW_LCOV_MANIFEST` | Path to file accumulating lcov.info paths from coverage runs |
| `MAW_TEST_ISOLATED_VERBOSE` | If `1`/`true`, print full output from isolated test runs |

---

## Running Tests Locally

### Quick Test Run

```bash
# Run all default-suite tests (mixed shared + per-file isolation)
bun run test

# Run isolated tests only
bun run test:isolated

# Run plugin tests
bun run test:plugin

# Run mock-transport smoke tests
bun run test:mock-smoke
```

### Shard & Randomize

```bash
# Run shard 1 of 4 from default suite
bash scripts/test-default-safe.sh --shard 1/4

# Run isolated tests with random order
bash scripts/test-isolated.sh --randomize

# Run specific test file
bash scripts/test-default-safe.sh test/federation-sync.test.ts
```

### Coverage Report

```bash
bun run test:coverage
# Generates coverage/lcov.info and docs/testing/coverage-gap-analysis.md
```

### Full Test Suite (All Modes)

```bash
bun run test:all
# = test:default:safe + test:isolated + test:mock-smoke + test:plugin
```

---

## Test Isolation Best Practices

### When to Use Isolation

**Use `test/isolated/` or `@maw-test-isolate` when:**
- You call `mock.module()` anywhere in the file
- You mock global state (module-level variables)
- You need to reset mocks between tests
- You depend on import order guarantees

**Use default suite when:**
- Pure functions, no mocks
- Dependency injection via parameters
- No side effects on global state
- Safe to run alongside other tests

### Markers & Directives

```typescript
// Force per-file subprocess isolation
// @maw-test-isolate

// Force tmpdir execution (for file-mutation tests)
// @maw-test-isolate-cwd-neutral

describe("test name", () => {
  // test code
});
```

### Manual Subprocess Control

If `mock.module()` escapes detection:
```typescript
// Add marker at top of file
// @maw-test-isolate
```

Then run with explicit isolation:
```bash
bash scripts/test-isolated.sh test/my-file.test.ts
```

---

## Key Learnings & Patterns

### 1. Mock Pollution is Dangerous

Bun's `mock.module()` affects all subsequent code in the same process. The script-based isolation strategy (`test-default-safe.sh` + per-file subprocess) is the team's battle-tested solution.

### 2. Dependency Injection > Direct Mocking

Prefer passing deps as function parameters:
```typescript
// Good: testable
async function setupAutoWake(
  opts: Options,
  sys: { platform: () => string; execFileSync: (...) => string },
) { ... }

// Less ideal: requires mock.module()
async function setupAutoWake(opts: Options) {
  os.platform()  // hard-coded dependency
}
```

### 3. 100% Coverage is Achievable

The codebase achieves 100% line + function coverage through:
- Pure logic layer separation (test logic without I/O)
- Comprehensive error path testing
- Excluding only pre-compiled code (WASM) from instrumentation

### 4. Flaky Tests Get Skipped, Not Fixed With Sleeps

Known flaky tests (#830, #813) are explicitly skipped in CI (`MAW_SKIP_FLAKY=1`). Root-cause mitigation (SO_REUSEADDR, retry logic) lives in the test. Self-hosted runner re-tests with `MAW_SKIP_FLAKY=0` to validate fixes.

### 5. Test Fixtures Don't Leak to User Config

The `MAW_TEST_MODE=1` guard in `src/config/load.ts` prevents `saveConfig()` from writing to `~/.config/maw/` during tests. Critical for developer experience (no fixture pollution).

---

## Related Documentation

- `docs/testing/coverage-gap-analysis.md` — Most recent coverage report
- `docs/testing/fedtest-phase1.md` — Federation test harness design
- `docs/federation/docker-testing.md` — Docker-based multi-node testing
- `.github/workflows/ci.yml` — Main CI gate logic
- `scripts/test-default-safe.sh` — Default-suite smart isolation
- `scripts/test-isolated.sh` — Isolated test runner

---

## Summary

**maw-js testing architecture** is optimized for:
1. **Safety**: Per-file subprocess isolation prevents mock pollution
2. **Speed**: Smart shared sweep + selective isolation (not all-or-nothing)
3. **Coverage**: 100% line coverage via pure logic layer + exhaustive error testing
4. **Developer experience**: Fast local runs, reproducible CI, no config pollution
5. **Federation resilience**: Separate self-hosted runner for real multi-node scenarios

The key innovation is the **automatic detection + per-file isolation** strategy in `test-default-safe.sh`, which sidesteps Bun's process-global mocks without requiring code changes.
