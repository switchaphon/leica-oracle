# oh-my-codex Testing & Quality Patterns

**Date**: 2026-06-19  
**Source**: 357 test files across Rust + TypeScript codebase  
**Focus**: Team runtime, state operations, HUD reconciliation/rendering, quality gates, release readiness

---

## Test Structure & Conventions

### Test Organization
- **357 test files** across the codebase (`.test.ts`, `.test.js`, `.spec.ts`)
- Tests organized by domain: `src/{domain}/__tests__/{feature}.test.ts`
- Key test lanes:
  - **team-state-runtime**: Core team coordination + state management
  - **hooks-notify-platform**: Hooks, notifications, HUD, verification
  - **cli-core-rest**: CLI, agents, catalog, config, modes, pipeline, planning
  - **smoke**: Cross-platform & packaged install validation

### Test Infrastructure
- **Test runner**: Node.js native `node:test` module (no external runner)
- **Assertion library**: Node.js native `node:assert/strict`
- **Concurrency**: Tests run with controlled concurrency via `run-test-files.js`
- **Platform support**: Linux/macOS primary, cross-platform gates on Node 22
- **Environment isolation**:
  - Temp directories per test: `mkdtemp()` + cleanup in `afterEach()`
  - State root isolation via `OMX_TEAM_STATE_ROOT` env var
  - Tmux session isolation with synthetic fixtures

### Test Mocking Patterns
- **Filesystem**: Uses real temp directories, not mocks — tests hit actual FS
- **Tmux interactions**: Mock with fixture objects providing `listCurrentWindowPanes()`, `createHudWatchPane()`, `resizeTmuxPane()` callbacks
- **Events**: Mock emission of structured events (question-created, dispatch-request, etc.)
- **Async operations**: Use standard `async/await`, not callbacks

---

## Key Test Files & Coverage

### Team Runtime Tests (`src/team/__tests__/`)

#### Tmux Test Fixture (`tmux-test-fixture.test.ts`)
- **Isolation**: Creates synthetic tmux server with isolated `TMUX` socket
- **Cleanup validation**: Verifies sessions are deleted after tests
- **Pane isolation**: Tests that fixture panes don't leak to ambient tmux server
- **Pattern**: Tests skip gracefully if tmux unavailable (`isRealTmuxAvailable()` check)

#### MCP Communication (`mcp-comm.test.ts`)
- **Write-before-notify protocol**: Validates inbox/mailbox written to disk before notification
- **Dead-state tracking**: Tests that messages retain `notified_at` status
- **Deferred requests**: Tests missing-pane scenarios where requests stay pending
- **Intent classification**: Tests intents like `followup-relaunch`, `pending-mailbox-review`
- **Pattern**: Full state initialization + assertion on file existence + request querying

#### Coordination Protocol (`coordination-protocol.test.ts`)
- **Team consensus**: Tests autopilot gate decisions across workers
- **Lifecycle transitions**: Tests state progression (proposing → consensus → executing)
- **Broadcast semantics**: Tests mailbox message broadcasting to all workers

#### Shutdown & Fallback (`shutdown-fallback.test.ts`)
- **Graceful degradation**: Tests behavior when tmux unavailable or pane missing
- **Recovery mechanisms**: Tests fallback to postman-assist when send-keys fails

#### Delivery E2E Smoke (`delivery-e2e-smoke.test.ts`)
- **Full-stack flow**: Tests end-to-end message delivery from worker to worker
- **Transport verification**: Validates delivery trace (queued → notified → executed)

### State Operation Tests (`src/state/__tests__/`, `src/team/__tests__/`)

#### State Lifecycle
- **Dead-state transitions**: Tests team state initialization, worker registration, phase tracking
- **Resume semantics**: Tests resuming from persisted state, identifying live workers vs dead
- **Persistence verification**: Tests that state changes are durably written before continuing

#### Worker Runtime Identity (`worker-runtime-identity.test.ts`)
- **Worker identity stability**: Tests that worker IDs don't change across resume cycles
- **Pane lifecycle**: Tests pane creation, binding, rebinding on resume
- **Index consistency**: Tests that worker indices remain stable even when workers die

#### State Server Integration (`src/mcp/__tests__/state-server.test.ts`)
- **MCP tool contract**: Tests state-read/state-write tools via MCP
- **Atomic updates**: Tests that state mutations are atomic (write happens or doesn't, no partials)
- **Query semantics**: Tests filtering (list-by-kind, list-by-phase, etc.)

### HUD Tests (`src/hud/__tests__/`)

#### Reconciliation (`reconcile.test.ts`)
- **Authority checks**: Verifies OMX ownership via `OMX_TMUX_HUD_OWNER_ENV`
- **Session binding**: Tests HUD recreates with correct `OMX_SESSION_ID`
- **Skipping conditions**: Tests that non-OMX-owned tmux is left alone
- **Pane lifecycle**: Tests HUD pane creation, sizing, registration with resize hook

#### Rendering (`render.test.ts`)
- **Color handling**: Tests ANSI SGR codes are stripped correctly, colors disabled when needed
- **Component rendering**: Tests Ralph status, Ultrawork status, Git branch, version display
- **Empty state**: Tests "No active modes." message when nothing active
- **Boundary conditions**: Tests empty context, null values, version parsing (strips "v" prefix)

#### State & Watch (`state.test.ts`, `watch.test.ts`)
- **State persistence**: Tests HUD state written to `.omx/state/hud/`
- **Watch loop**: Tests file watching for mode changes, reconciliation triggers on state change

#### Authority (`authority.test.ts`)
- **Session ownership**: Tests that HUD respects OMX_SESSION_ID as source of truth
- **Pane binding**: Tests leader pane ownership prevents other panes from controlling HUD

### Question/UI Tests (`src/question/__tests__/`)

#### Question State (`state.test.ts`)
- **Record creation**: Tests question records created under session-scoped namespace
- **Event correlation**: Tests structured events emitted with correlation IDs (run_id, session_id)
- **Terminal state**: Tests question reaches answered/error terminal state

#### Renderer (`renderer.test.ts`)
- **ANSI output**: Tests question prompts rendered with colors, alignment
- **Multi-select logic**: Tests option selection, validation, boundary conditions

#### Client (`client.test.ts`)
- **Submission validation**: Tests answer validation against schema
- **Retry logic**: Tests retry on validation failure

### Verification & Quality Gates (`src/verification/__tests__/`)

#### Verifier (`verifier.test.ts`)
- **Task sizing**: Determines verification depth (small/standard/large) based on file count + line changes
  - **Small**: <4 files, <100 lines → typecheck only
  - **Standard**: 4–15 files, 100–499 lines → lint + typecheck + basic regression
  - **Large**: >15 files or >500 lines → security review + perf analysis + API compat
- **Verification instructions**: Task-specific checklists for verification
- **Fix loop**: Tests retry mechanics (max 3 attempts before escalation)

#### Ralph Persistence Gate (`ralph-persistence-gate.test.ts`)
- **Session persistence**: Tests Ralph state survives shutdown + resume
- **Tracing**: Tests trace server records all state mutations

#### CI Rust Gates (`ci-rust-gates.test.ts`)
- **Clippy**: Tests clippy warnings are treated as errors
- **Format**: Tests cargo fmt compliance

#### Harness Release Workflow (`explore-harness-release-workflow.test.ts`)
- **Native asset validation**: Tests explore binary + sparkshell are built
- **Manifest integrity**: Tests release manifest lists all assets

#### PR Check Workflow (`pr-check-workflow.test.ts`)
- **Size labeling**: Tests PR labels (size/S, size/M, size/L, size/XL) based on additions + deletions
- **Draft warning**: Tests draft PR detection + warning

#### Dev Merge Issue Close (`dev-merge-issue-close-workflow.test.ts`)
- **Automation**: Tests issue closure automation on merge to main

---

## CI/CD Pipeline Architecture

### Multi-Lane Design (`ci.yml`)

**Lane Classification** (pre-run decision):
- **full_suite**: All gates if pushing to main, PRing to main, or ambiguous
- **docs_only**: Skip build/test if only docs changed
- **ts_changed**: Run lint, typecheck, test, coverage if src/ modified
- **rust_changed**: Run clippy, rustfmt, rust-tests if crates/ modified
- **native_changed**: Run all Rust gates if native packages affected
- **shared_config_changed**: Run all gates if package.json, Cargo.toml, .github/, biome.json, tsconfig changed

**Lane Selector Logic** (bash script in CI step):
- Maps file paths to categories (isDocs, isTs, isRust, isNative, isSharedConfig)
- Outputs classification to `GITHUB_OUTPUT`
- Handles first-push edge case (full suite)

### Build Jobs

1. **changes** (mandatory): Detects modified paths, outputs lane decisions
2. **docs-check**: Whitespace validation (git diff --check)
3. **rustfmt**: Cargo format check
4. **clippy**: Clippy lints as errors
5. **rust-tests**: Cargo tests + coverage via cargo-llvm-cov
6. **lint**: Biome linting
7. **typecheck**: tsc + check:no-unused (unused type exports)
8. **build-dist**: Compile TypeScript → dist/
9. **test**: Grouped test lanes (team-state-runtime, hooks-notify-platform, cli-core-rest, smoke)
10. **coverage-team-critical**: c8 coverage gate for team/ + state/ (78% lines, 90% functions, 70% branches)
11. **ralph-persistence-gate**: Verify Ralph state persistence across team operations
12. **build**: Full source build (explore:release, sparkshell, api)
13. **ci-status**: Final gate aggregator — checks all active lanes passed

### Coverage Gates (`coverage:team-critical`)
- **Scope**: `dist/team/**` + `dist/state/**` only (team runtime critical paths)
- **Thresholds**:
  - Lines: 78%
  - Functions: 90%
  - Branches: 70%
  - Statements: 78%
- **Tool**: c8 with lcov reporter
- **Failure mode**: Blocks CI if thresholds not met

### Quality Gates (`.github/workflows/`)

| Gate | Trigger | Fail Condition |
|------|---------|---|
| **changes** | always | Failure → CI failed |
| **rustfmt** | rust_changed OR full_suite | Non-zero exit → error |
| **clippy** | rust_changed OR full_suite | Warnings treated as errors |
| **rust-tests** | rust_changed OR full_suite | Test failure → error |
| **lint** | ts_changed OR shared_config OR full_suite | Biome errors → failure |
| **typecheck** | ts_changed OR shared_config OR full_suite | tsc errors → failure |
| **test** | ts_changed OR shared_config OR full_suite | Test failure → error |
| **coverage-team-critical** | ts_changed OR shared_config OR full_suite | Thresholds not met → error |
| **ralph-persistence-gate** | ts_changed OR shared_config OR full_suite | Persistence violated → error |

### Test Lane Breakdown
```
Team-State-Runtime Lane:
├── dist/team/__tests__
├── dist/state/__tests__
├── dist/ralph/__tests__
└── dist/ralplan/__tests__

Hooks-Notify-Platform Lane:
├── dist/hooks/__tests__
├── dist/hooks/code-simplifier/__tests__
├── dist/notifications/__tests__
├── dist/mcp/__tests__
├── dist/hud/__tests__
└── dist/verification/__tests__

CLI-Core-Rest Lane:
├── dist/cli/__tests__
├── dist/agents/__tests__
├── dist/catalog/__tests__
├── dist/config/__tests__
├── dist/modes/__tests__
├── dist/planning/__tests__
├── dist/scripts/__tests__
├── dist/utils/__tests__
└── dist/visual/__tests__

Smoke Lane (Node 22):
├── dist/cli/__tests__/packaged-script-resolution.test.js
├── dist/cli/__tests__/sparkshell-cli.test.js
├── dist/hooks/__tests__/explore-routing.test.js
└── Cross-rebase smoke test
```

---

## Release Protocol & Readiness

### Release Sequence (RELEASE_PROTOCOL.md)

**Phase 1: Freeze & Inventory**
1. Identify `PREV=v0.X.Y` (last released tag), `NEXT=v0.X.Z` (candidate)
2. Verify ancestry: `git merge-base --is-ancestor "$PREV" "$CANDIDATE"`
3. Generate PR inventory: `git log "$PREV..$CANDIDATE" | grep -Eo '#[0-9]+'`
4. Cross-check every PR in notes or mark as internal-only

**Phase 2: Documentation**
- Mandatory files:
  - `CHANGELOG.md`
  - `docs/release-notes-<version>.md`
  - `docs/qa/release-readiness-<version>.md`
  - `RELEASE_BODY.md`
- Sections: Highlights, Fixes, PR inventory, validation evidence, full changelog link

**Phase 3: Validation**
1. Generate release body: `node dist/scripts/generate-release-body.js --template RELEASE_BODY.md --out /tmp/RELEASE_BODY.generated.md --current-tag "$NEXT" --previous-tag "$PREV" --repo Yeachan-Heo/oh-my-codex`
2. Verify contributors list accuracy (not just shortlog)
3. Record CI run IDs, local gate results in release-readiness doc

**Phase 4: Publish**
1. Merge to main, wait for main CI green
2. Push annotated tag (triggers release workflow)
3. Verify GitHub release non-draft, npm version correct, native assets attached
4. Fast-forward dev to main, wait for final CI green

**Phase 5: Post-Publish Corrections**
- Never retag npm; instead fix docs in dev, promote to main via normal CI
- Update GitHub release body via `gh release edit "$NEXT" --notes-file /tmp/RELEASE_BODY.generated.md`

### Release-Readiness Gate
- **Owner**: Maintainer
- **Evidence required**:
  - Compare range + PR inventory
  - Local gates passed (rustfmt, clippy, typecheck, lint, test)
  - CI run IDs (main, dev)
  - Known gaps documented
- **Blocker**: Missing compare-range evidence or failing CI

---

## Reliability Patterns

### State Operation Reliability

#### Dead-State & Resume Design
- **Premise**: Team members can die (pane killed, process crashed, network gone)
- **Detection**: HUD watches for dead workers via missing pane ID
- **Recovery**: Persisted state allows resume — workers come back with same identity
- **Tests verify**:
  - State written durably before notification
  - Dead workers detected by missing pane
  - Resume reconstructs team from disk
  - Worker IDs stable across resume cycles

#### Tmux Isolation
- **Synthetic fixtures**: Each test gets isolated `TMUX` socket + session
- **Cleanup guarantee**: All tmux resources deleted after test (verified by checking `tmuxSessionExists()` returns false post-test)
- **Ambient safety**: Fixture sessions don't appear on default tmux server, preventing cross-test pollution

#### Inbox/Mailbox Protocol
- **Write-first**: Message written to disk in `workers/{name}/inbox.md` before any notification
- **Idempotent notify**: Notification callback may fail; message persists in queue until acked
- **Intent tracking**: Request records `intent` (followup-relaunch, pending-mailbox-review, etc.) for recovery

### HUD Reliability

#### Authority & Ownership
- **Single source of truth**: `OMX_SESSION_ID` + `OMX_TMUX_HUD_OWNER_ENV` determine authority
- **Lease model**: HUD pane bound to session; if session dies, HUD can be recreated
- **Non-OMX tmux**: Left untouched; if run outside OMX, HUD skips reconciliation

#### Reconciliation on Prompt Submit
- **Trigger**: Every user prompt checks if HUD window still exists
- **Action**: If missing but session is live, recreates HUD pane with correct env vars
- **Atomic**: Pane creation + resizing + hook registration happen together

#### Rendering Robustness
- **Color handling**: Tests verify ANSI SGR codes stripped when colors disabled
- **Null safety**: All context fields nullable; rendering handles empty state gracefully
- **No crashes**: Render tests verify no exceptions on empty context, boundary values

### Test Coverage as Reliability Signal

**Team/State coverage gates** (78% lines, 90% functions):
- High function coverage (90%) ensures critical state transitions are tested
- 78% line coverage allows untested error paths (graceful degradation)
- Branches (70%) target critical decision points

**What this reveals about reliability**:
- Team coordination paths are heavily tested (high function coverage)
- Resume/persistence paths are tested (ralph-persistence-gate is separate)
- Error handling is tested but not exhaustively (70% branch coverage is selective)

---

## Quality Gates Summary

### Automated Gates (Run on Every Commit)

| Gate | Metric | Threshold | Fail = Blocks |
|------|--------|-----------|---|
| Lint (Biome) | Syntax + style | 0 errors | Yes |
| Typecheck (tsc) | Type safety | 0 errors | Yes |
| Unused exports | Dead code | 0 exports | Yes |
| Clippy | Rust lints | 0 warnings | Yes |
| Rustfmt | Rust format | auto-fixed | Yes |
| Unit tests (Node) | Functionality | All pass | Yes |
| Coverage (team) | Lines | 78% | Yes |
| Coverage (team) | Functions | 90% | Yes |
| Coverage (team) | Branches | 70% | Yes |
| Ralph persist | State durability | 100% | Yes |
| Build (dist) | Compilation | Success | Yes |
| Build (native) | Cargo + native | Success | Yes |

### Manual Gates (Pre-Release)

| Gate | Verifier | Evidence |
|------|----------|----------|
| Release collateral | Maintainer | CHANGELOG, release-notes, release-readiness docs |
| Compare range audit | Maintainer | PR inventory vs compare-range logs |
| Contributors list | Maintainer | Authors match merged PRs, not just shortlog |
| GitHub release body | Maintainer | Generated from RELEASE_BODY.md, accurate changelog link |

---

## Key Insights

### 1. **357 Tests = Comprehensive Coverage**
- Not just unit tests — includes E2E flows (delivery-e2e-smoke)
- Tests cover happy path, error paths, recovery paths (resume, dead-state, reconcile)

### 2. **Multi-Lane CI Prevents Over-Testing**
- Docs-only changes skip build/test entirely (fast feedback)
- Targeted lanes (ts_changed, rust_changed) run relevant gates only
- Reduces feedback loop from ~10min (full suite) to ~2min (targeted)

### 3. **State Persistence is Mission-Critical**
- Ralph persistence gate runs separately (not bundled with unit tests)
- Dead-state + resume is tested extensively (worker-runtime-identity, cross-rebase-smoke)
- Write-before-notify protocol enforced in every MCP communication test

### 4. **HUD Reliability via Reconciliation**
- Authority model (OMX_SESSION_ID) prevents cross-talk
- Reconciliation on prompt submit ensures HUD can recover from transient failures
- Tests verify pane is recreated with correct env vars, not assumed pre-existing

### 5. **Release Protocol Prevents Changelog Drift**
- Mandatory diff-based inventory (not memory-based)
- Contributors list reviewed against actual merged PRs
- Release-readiness doc is persistent evidence, not ephemeral

### 6. **Layered Verification**
- **Automated**: Lint, type, unit tests, coverage gates (run on all commits)
- **Semi-automated**: Native build + smoke tests (run on all commits to main)
- **Manual**: Release collateral audit (run once per release)
- This layering catches bugs early (lint, type, unit) and prevents subtle regressions (coverage, smoke)

---

## Files for Future Reference

| Document | Purpose |
|----------|---------|
| `.github/workflows/ci.yml` | Lane detection logic, test organization |
| `RELEASE_PROTOCOL.md` | Release sequence, mandatory evidence |
| `COVERAGE.md` | Feature parity matrix (oh-my-claudecode compatibility) |
| `src/team/__tests__/` | Team coordination, state, delivery patterns |
| `src/hud/__tests__/` | HUD authority, reconciliation, rendering |
| `src/verification/__tests__/` | Quality gate logic, task sizing |
| `package.json` | Test scripts, coverage config, build targets |

