# TESTING — nodered-simulator

**Captured:** 2026-04-26  
**Project version:** 4.35.1  
**Repo:** `internal-server/nodered-simulator`

---

## Overview

This is a multi-component monorepo. Testing is present across three of the four sub-systems. There is no single unified test runner — each component uses its own toolchain.

| Component | Language | Framework | Test count |
|-----------|----------|-----------|------------|
| `functions/` (Node-RED function nodes) | Node.js | `node:test` (built-in, no deps) | 21 tests |
| `web-ui/` (Laravel config manager) | PHP + JS | PHPUnit 11 + Playwright | 305 PHPUnit (822 assertions) + 31 browser tests |
| `cctv-simulator/` (Python CCTV snapshotter) | Python 3.12 | pytest | 53 tests |
| `flows/` (Node-RED flow JSON) | — | none | no automated tests |

---

## 1. Function-Node Tests (Node.js `node:test`)

### What is tested

Pure JavaScript logic extracted from Node-RED function nodes. Because Node-RED's sandbox cannot `require()` user files at runtime, the tested code lives in `functions/lib/` — standalone modules that handlers import only in the test environment.

**Test files:**

- `scripts/test-function-nodes.js` — entry point; requires both suites
- `scripts/test-split-stations.js` — 8 tests for `functions/lib/splitStations.js`
- `scripts/test-command-handlers.js` — 13 tests for `functions/lib/resolveSimulateMode.js` + grep-lint on 5 command handlers

**Coverage:**

- `splitStations.js`: uniform station grouping, mixed simulate_mode splitting, station fallback, default-true path, disabled station skipped, offline device skipped, missing template fallback, offline_sensors filtering
- `resolveSimulateMode.js`: 5 resolution-order cases, 3 numeric type-preservation cases
- **Grep-lint** (Strategy B): asserts each `command-*.js` handler contains the canonical expression `deviceConfig.simulate_mode ?? stationConfig.simulate_mode ?? true` exactly once — catches silent divergence without requiring the full Node-RED runtime

**Test helpers** (`scripts/test-helpers/build-stubs.js`):

```js
makeFlowStub(initial = {})   // minimal flow.get / flow.set stub
makeNodeStub()               // node.send / warn / error stub with captured arrays
```

These are not used by the current suites (which test pure lib functions), but are available for any future test that needs to simulate the Node-RED function-node sandbox context.

### How to run

```bash
# From repo root
npm run test
# or equivalently:
npm run test:functions
# or directly:
node --test scripts/test-function-nodes.js
```

Requires Node.js >= 14.0.0. No `npm install` needed — only built-in modules are used (`node:test`, `node:assert/strict`, `node:fs`, `node:path`).

---

## 2. Web UI Tests (Laravel + Playwright)

The web-ui is a Laravel 12 / PHP 8.2+ application. It has three test layers.

### 2a. PHPUnit — Unit tests

**Location:** `web-ui/tests/Unit/`

| File | What it tests |
|------|--------------|
| `Unit/Models/StationTest.php` | Station model |
| `Unit/Models/DeviceTest.php` | Device model |
| `Unit/Models/DeviceTemplateTest.php` | DeviceTemplate model |
| `Unit/Services/CommuIdGeneratorTest.php` | `CommuIdGenerator` service — format, scoped running numbers, gap handling, uppercase enforcement, measurement key derivation (REQ-CID-001 to REQ-CID-007) |
| `Unit/Services/KubernetesLogServiceTest.php` | K8s log service |
| `Unit/Helpers/ResolveEnvVarsTest.php` | `resolve_env_vars()` helper |

### 2b. PHPUnit — Feature tests

**Location:** `web-ui/tests/Feature/`  
All use `RefreshDatabase` + in-memory SQLite (configured in `phpunit.xml`).

| Directory | Files | Domain |
|-----------|-------|--------|
| `Station/` | Create, Delete, Edit, Index, Show, Toggle | Station CRUD + validation + simulate_mode toggle |
| `Device/` | Create, Delete, Edit, Show, CommuIdFeature | Device CRUD + commu_id uniqueness |
| `Sensor/` | Display, Offline, Override, Situation | Sensor management |
| `Deploy/` | Deploy, DeployWithLogs, DeployCctv, SimulateModeExport | `managed_config.json` export shape, reload flags, simulate_mode serialization |
| `Cctv/` | DeviceCctvDisplay, DeviceCctvEdit, TemplateCctvDisplay | CCTV device UI |
| `Seed/` | SeedCctv, SeedMerge, SeedWaterPropulsion | Seeder idempotency |
| `Api/` | AuthApi, DeployApi, DeviceApi, DeviceTemplateApi, StationApi | REST API routes (Sanctum bearer tokens) |
| `Search/` | SearchController | Global search endpoint |
| `Security/` | SecurityTest | Mass-assignment protection (SEC-001–004), 404 handling (SEC-010–013), XSS escaping (SEC-020–023), HTTP method protection (SEC-030–031) |

**Test naming convention:** method names map to requirement IDs, e.g. `test_REQ_STA_020_redirect_after_edit`, `test_SEC_001_station_mass_assignment_ignores_id`.

**PHPUnit configuration** (`web-ui/phpunit.xml`):

- `APP_ENV=testing`, `DB_CONNECTION=sqlite`, `DB_DATABASE=:memory:`
- FTP vars set to safe test values (`FTP_HOST=ftp.rpro.digitalsmart.city`, `FTP_PASSWORD=test-password`)
- Pulse, Telescope, Nightwatch all disabled

### 2c. Playwright — Browser (E2E) tests

**Location:** `web-ui/tests/Browser/`  
**Config:** `web-ui/playwright.config.js`

| Spec file | Coverage |
|-----------|----------|
| `station.spec.js` | Station CRUD flow (create, show, edit, delete, filter pills) |
| `device.spec.js` | Device show page, device edit saves changes |
| `device-index.spec.js` | Device list |
| `navigation.spec.js` | Theme toggle, search modal |
| `sensor.spec.js` | Sensor overrides |
| `template.spec.js` | Template index/show |

**Config details:**

- Single project: Chromium only
- `testDir: ./tests/Browser`
- `timeout: 30000`, `retries: 0`
- `screenshot: 'only-on-failure'`
- `webServer`: spins up `php artisan serve --port=<port>` automatically
- Default port: `8001`; override with `PLAYWRIGHT_PORT` env var
- `PLAYWRIGHT_BASE_URL` env var also accepted

### How to run (web-ui)

```bash
cd web-ui

# PHPUnit (unit + feature — 305 tests, 822 assertions)
php artisan test
# or via composer script:
composer test

# Playwright browser tests (31 tests)
npx playwright test
# Run against a specific port:
PLAYWRIGHT_PORT=8002 npx playwright test
# Run headed (debug):
npx playwright test --headed

# First-time setup:
composer run setup
# This runs: composer install → .env copy → key:generate → migrate → npm install → npm run build
```

**Dependencies:**

- PHP 8.2+
- Composer (PHPUnit 11.5, Mockery, Faker, Laravel Pint, Sail)
- Node.js (for `npm run build` and Playwright)
- SQLite (`pdo_sqlite` PHP extension)

**Test artifacts:** `web-ui/test-results/` — screenshots from Playwright failures (`.last-run.json` present, confirming tests have been run).

---

## 3. CCTV Simulator Tests (pytest)

**Location:** `cctv-simulator/tests/`  
**Framework:** pytest >= 8.0.0  
**Production deps:** Pillow >= 10.0.0 (only)

| File | Count | What it tests |
|------|-------|--------------|
| `test_config.py` | 20 | Config loading, CCTV device extraction from `managed_config.json`, FTP target parsing, `resolve_background()` |
| `test_image_generator.py` | 11 | JPEG generation with timestamp overlay (`image_generator.py` / Pillow) |
| `test_camera.py` | 8 | `CameraThread` start/stop/graceful shutdown, file cleanup on success, file retention on partial FTP failure; `CameraManager` thread lifecycle (start, skip-no-ftp, reload-adds-new, reload-removes-deleted) |
| `test_ftp_uploader.py` | 6 | FTP upload logic, retry behavior, `FtpUploadError` |
| `test_trigger_reload.py` | 3 | HTTP-based reload trigger endpoint |
| `test_reload_server.py` | 5 | Reload server (Flask HTTP endpoint for hot-reload) |
| `conftest.py` | — | Adds parent dir to `sys.path` so tests can import sibling modules |

**Test strategy:** heavy use of `unittest.mock.patch` and `pytest`'s `tmp_path` fixture to avoid real filesystem and FTP calls. `CameraThread.start` / `CameraThread.run` are patched in manager tests so no actual threads run.

### How to run

```bash
cd cctv-simulator

# Install dev dependencies
pip install -r requirements-dev.txt
# (requirements-dev.txt = requirements.txt + pytest>=8.0.0)

# Run all tests
python -m pytest tests/ -v

# Run a specific file
python -m pytest tests/test_camera.py -v
```

---

## 4. Linting and Code Quality

### PHP — Laravel Pint

`laravel/pint` is installed as a dev dependency in `web-ui/composer.json`. Pint is an opinionated PHP code formatter (wraps PHP-CS-Fixer).

```bash
cd web-ui
./vendor/bin/pint          # format
./vendor/bin/pint --test   # check only (exit non-zero if dirty)
```

No `.pint.json` configuration file was found — Pint is running with defaults (Laravel preset).

### JavaScript — no linter configured

There is no `.eslintrc`, `eslint.config.*`, or `biome.json` in the repo root or `functions/`. The grep-lint tests in `scripts/test-command-handlers.js` serve as a lightweight structural lint for the command handler files.

### Python — no linter configured

No `ruff`, `flake8`, `mypy`, or `pylint` configuration was found. Pytest is the only quality tooling for the Python sub-system.

---

## 5. CI/CD

**File:** `.gitlab-ci.yml`  
**Platform:** Self-hosted GitLab with `intranet-runner` (Docker-in-Docker pattern — runner uses `docker run` to launch test containers)

### Stages: `test → build → deploy`

### Test stage jobs

All three test jobs:
- Run **only on merge request events** (`$CI_PIPELINE_SOURCE == "merge_request_event"`)
- Are marked `allow_failure: true` (not a hard merge gate — advisory only)
- Use bind-mount (`RUNNER_DOCKER_HOST_PWD`) to share the workspace with ephemeral Docker containers
- Include an `after_script` that `chown`s the workspace back to the runner's UID/GID (band-aid for root-owned files left by containers)

| Job | Image | Command |
|-----|-------|---------|
| `test-functions` | `node:20-alpine` | `npm run test:functions` |
| `test-phpunit` | `php:8.3-cli` (installs composer + pdo_sqlite at runtime) | `php artisan test` |
| `test-playwright` | `mcr.microsoft.com/playwright:v1.49.0-jammy` (installs PHP at runtime) | `npx playwright test` |

**Playwright artifact:** On failure, `web-ui/test-results/` is uploaded and kept for 1 week.

### Build stage jobs

Triggered automatically on version tags (`/^v\d+/`), or manually on `main`:
- `build-nodered` — builds `docker/nodered/Dockerfile`
- `build-webui` — builds `docker/web-ui/Dockerfile`
- `build-cctv-simulator` — builds `docker/cctv-simulator/Dockerfile`

### Deploy stage jobs

All manual. Use `kubectl apply` against a Kubernetes cluster:
- `deploy-edge`, `deploy-webui`, `deploy-nodered`, `deploy-cctv-simulator`

### Known issue / open question

`PRP-test-stage-value-question.md` (parked, 2026-04-25) documents an architectural decision about the CI test stage: all three jobs have `allow_failure: true` and are **not authoritative**. The `CLAUDE.md` explicitly names the local commands as the authoritative gate. Three resolution paths are sketched (delete the stage, build dedicated CI images, keep the band-aid) but no decision has been made.

---

## 6. Flow Validation — Node-RED `flows.json`

There are **no automated tests** for `flows/flows.json` or `flows.json` (root copy).

**How correctness is currently maintained:**

1. **Sync script** (`scripts/sync-functions.js` / `npm run sync`): injects source from `functions/*.js` into the flow's function nodes. This is the only automated step — it ensures the flow JSON matches the source files, but does not validate logic.
2. **Manual verification**: MQTT `mosquitto_pub` commands listed in `CLAUDE.md` are used for manual smoke testing against a live Node-RED instance.
3. **Function-node logic tests** (section 1 above) cover the pure-JS parts of the functions, but these run outside Node-RED and cannot exercise the wiring, routing, or context state of the actual flow.

**Testing approaches that would close this gap:**

- **`@node-red/test-helpers`**: The official Node-RED testing library (`node-red-node-test-helper`) provides a mock runtime that loads flow JSON, wires nodes, and lets tests send/receive messages. It would enable unit-testing individual function nodes with the real context/flow/global API.
- **Integration test against a running Node-RED instance**: A test script could start Node-RED, subscribe to MQTT, publish commands, and assert the ACK sequence. More realistic but requires a live MQTT broker and longer execution time.

---

## 7. Test Configurations (`test-configs/`)

`test-configs/` contains 7 JSON fixture files used for testing config validation logic:

| File | Purpose |
|------|---------|
| `empty-config.json` | Empty config (no stations) |
| `invalid-boolean.json` | Boolean fields with wrong types |
| `invalid-template.json` | Device references non-existent template |
| `invalid-time.json` | Malformed time values |
| `missing-device-fields.json` | Devices with required fields absent |
| `missing-meta.json` | Config missing top-level metadata |
| `uppercase-station.json` | Station keys with uppercase (should be rejected) |

These are not automatically invoked by any test runner. They appear to be manual fixtures or inputs to a config validation tool not yet implemented as an automated suite.

---

## Summary

Tests exist and are substantive. The project has 21 JS function-node tests, 305 PHPUnit tests (822 assertions), 31 Playwright browser tests, and 53 pytest tests — totalling approximately 410+ automated test cases across three runtimes.

The main gap is the Node-RED flow itself: `flows.json` has no automated test coverage. Logic extracted into `functions/lib/` is tested, but the wiring, routing, and context state of the live flow are validated only manually. The `test-configs/` fixtures and `@node-red/test-helpers` would be the natural starting points for closing that gap.

The CI test stage exists but is advisory only (`allow_failure: true`). Local commands are the authoritative gate per `CLAUDE.md`.
