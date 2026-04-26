# Architecture: nodered-simulator

**Version:** 4.35.1  
**Last Updated:** 2026-04-26  
**Source:** `/Users/switchaphon/_RPRO_/internal-server/nodered-simulator`  
**Timezone:** GMT+7 (Asia/Bangkok)

---

## 1. What This Project Is

**nodered-simulator** is an IoT device simulation platform for water management infrastructure. It generates realistic, physics-based sensor data and command acknowledgment sequences — replacing physical hardware for development, QA, and integration testing of MQTT-based water management control systems.

**What it simulates:**
- Water infrastructure: gates (hydraulic flow control), fixed pumps, mobile pumps, water propulsion units
- Waste management: trash screens, trash conveyors
- Environmental sensors: water level, rainfall, water quality, velocity, flow, air quality
- CCTV cameras: JPEG snapshots with timestamp overlay uploaded via FTP

**Primary consumers:** MQTT-based control applications subscribing to `data_stream/` topics and issuing commands on `data_command/` topics.

---

## 2. Directory Tree

```
nodered-simulator/
├── package.json                    # NPM scripts: sync, watch, test
├── settings.js                     # Node-RED runtime configuration
├── flows.json                      # Top-level symlink/copy (not canonical)
├── CLAUDE.md                       # AI assistant context
├── README.md                       # Setup and overview
├── NODERED_GUIDE.md                # Technical Node-RED architecture guide
├── USER_MANUAL.md                  # End-user guide
├── CHANGELOG.md                    # Version history
│
├── flows/
│   └── flows.json                  # CANONICAL Node-RED flow (deploy target)
│
├── functions/                      # Source of truth for all function-node code
│   ├── function-mapping.json       # filename → Node-RED node ID mapping
│   ├── lib/
│   │   ├── resolveSimulateMode.js  # Pure logic: per-device simulate_mode resolution
│   │   └── splitStations.js        # Pure logic: device group splitting
│   ├── stations-configuration.js   # Loads managed_config.json → flow._stations
│   ├── devices-template.js         # Loads device templates → flow._device_templates
│   ├── split-stations-devices-data.js  # Fans out one msg per (measurement|type|mode) group
│   ├── global-utilities-function.js    # Registers sim_* helper functions in global context
│   ├── command-registry-helper.js      # Global: cmd_isCommandProcessed, cmd_addCommandRegistry, cmd_completeCommandRegistry
│   ├── command-registry-cleanup.js     # TTL cleanup of completed commands (7-day expiry)
│   ├── command-water-pump.js       # Command handler: WATER_PUMP
│   ├── command-water-gate.js       # Command handler: WATER_GATE (with abort)
│   ├── command-trash-screen.js     # Command handler: TRASH_SCREEN
│   ├── command-trash-conveyor.js   # Command handler: TRASH_CONVEYOR
│   ├── command-water-propulsion.js # Command handler: WATER_PROPULSION
│   ├── simulate-water-level.js     # Physics simulation: WATER_LEVEL
│   ├── simulate-rainfall.js        # Physics simulation: RAINFALL
│   ├── simulate-water-quality.js   # Physics simulation: WATER_QUALITY
│   ├── simulate-water-velocity.js  # Physics simulation: WATER_VELOCITY
│   ├── simulate-water-flow.js      # Physics simulation: WATER_FLOW
│   ├── simulate-air-quality.js     # Physics simulation: AIR_QUALITY
│   ├── simulate-water-gate.js      # Physics simulation: WATER_GATE sensor state
│   ├── simulate-water-pump.js      # Physics simulation: WATER_PUMP sensor state
│   ├── simulate-mobile-pump.js     # Physics simulation: MOBILE_PUMP (fuel, GPS)
│   ├── simulate-water-propulsion.js # Physics simulation: WATER_PROPULSION
│   ├── simulate-trash-screen.js    # Physics simulation: TRASH_SCREEN
│   ├── simulate-trash-conveyor.js  # Physics simulation: TRASH_CONVEYOR
│   ├── testing-*.js                # 12 testing-mode variants (fixed/deterministic values)
│   ├── prepare-mqtt-payload-simulate.js  # Build combined device payload (simulate mode)
│   ├── prepare-mqtt-payload-testing.js   # Build combined device payload (testing mode)
│   ├── publish-to-mqtt-server.js   # Route payload to target MQTT broker(s)
│   ├── build-data-command-payload.js     # Format incoming command for handler routing
│   ├── parse-command.js            # Parse and validate raw MQTT command message
│   ├── calculate-water-level.js    # Derived water level calculation
│   ├── manage-flow-context.js      # Flow context read/write helpers
│   ├── delete-all-flow-context.js  # Admin: wipe all flow context
│   ├── set-null-all-flow-context.js # Admin: null all flow context values
│   ├── refuel-all-devices.js       # Admin: reset fuel to max for propulsion/mobile pump
│   └── stations-configuration_ori.js # Legacy backup (not synced)
│
├── config/
│   ├── managed_config.json         # Live station/device configuration (runtime source)
│   ├── managed_config.default.json # Bundled default for fresh deployments
│   └── managed_config.example.json # Documentation example
│
├── scripts/
│   ├── sync-functions.js           # Reads function-mapping.json, injects functions/*.js into flows.json
│   ├── sync-version.js             # Syncs package.json version → web-ui/config/app.php
│   ├── watch.js                    # File watcher: auto-runs sync-functions on change
│   ├── test-function-nodes.js      # Node 20 node:test harness (21 tests)
│   ├── test-command-handlers.js    # Command handler integration tests
│   ├── test-split-stations.js      # Unit tests for split-stations logic
│   └── test-helpers/
│       └── build-stubs.js          # Test stub builders
│
├── test-configs/                   # Invalid config fixtures for validation tests
│   ├── empty-config.json
│   ├── invalid-boolean.json
│   ├── invalid-template.json
│   ├── invalid-time.json
│   ├── missing-device-fields.json
│   ├── missing-meta.json
│   └── uppercase-station.json
│
├── cctv-simulator/                 # CCTV Snapshot Simulator (Python 3.12)
│   ├── main.py                     # Entry point: signal handlers, reload loop
│   ├── config.py                   # Config loading, CameraConfig/FtpTarget dataclasses
│   ├── camera.py                   # CameraThread + CameraManager (hot-reload)
│   ├── image_generator.py          # JPEG generation with timestamp overlay (Pillow)
│   ├── ftp_uploader.py             # FTP upload with retry (stdlib ftplib)
│   ├── reload_server.py            # HTTP server: POST /reload for instant config reload
│   ├── backgrounds/                # Background JPEG images (6 files including default.jpg)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── tests/                      # 53 pytest tests
│   │   ├── test_camera.py
│   │   ├── test_config.py
│   │   ├── test_ftp_uploader.py
│   │   ├── test_image_generator.py
│   │   ├── test_reload_server.py
│   │   └── test_trigger_reload.py
│   └── cctv-simulator-0-app.yml    # Kubernetes Deployment + Service manifest
│
├── web-ui/                         # Laravel 11 configuration manager
│   ├── artisan
│   ├── composer.json               # Laravel 11, PHP 8.2, Sanctum, SQLite
│   ├── app/
│   │   ├── Console/Commands/
│   │   │   ├── CreateApiToken.php
│   │   │   ├── ListApiTokens.php
│   │   │   ├── RevokeApiToken.php
│   │   │   └── SeedFromExistingConfig.php
│   │   ├── Http/Controllers/
│   │   │   ├── DeployController.php        # Export config + trigger Node-RED + CCTV reload
│   │   │   ├── StationController.php       # Station CRUD (web)
│   │   │   ├── DeviceController.php        # Device CRUD (web)
│   │   │   ├── DeviceTemplateController.php
│   │   │   ├── SearchController.php
│   │   │   └── Api/V1/
│   │   │       ├── DeployController.php    # REST API: POST /api/v1/deploy
│   │   │       ├── StationController.php   # REST API: CRUD /api/v1/stations
│   │   │       ├── DeviceController.php    # REST API: CRUD /api/v1/devices
│   │   │       └── DeviceTemplateController.php
│   │   ├── Models/
│   │   │   ├── Station.php         # config_json (array cast), is_enabled
│   │   │   ├── Device.php          # overrides_json, is_offline, short_commu_id
│   │   │   ├── DeviceTemplate.php  # template_id, config_json (sensors, measurement, type)
│   │   │   └── User.php            # Sanctum API tokens
│   │   ├── Services/
│   │   │   ├── CommuIdGenerator.php  # Generates padded commu_id (e.g. "001-WATERPUMP")
│   │   │   └── KubernetesLogService.php  # Fetches pod logs for deploy verification
│   │   └── Http/Resources/         # API response transformers
│   ├── database/
│   │   ├── migrations/
│   │   ├── seeders/DeviceTemplateSeeder.php  # Idempotent template seed (updateOrCreate)
│   │   └── factories/
│   ├── config/app.php              # Contains version string (synced by sync-version.js)
│   ├── tests/
│   │   ├── Feature/                # PHPUnit feature tests (305 tests total)
│   │   ├── Unit/                   # Model + service unit tests
│   │   └── Browser/                # Playwright browser tests (31 tests)
│   └── playwright.config.js        # Playwright: port 8001/8002
│
├── docker/
│   ├── nodered/
│   │   ├── Dockerfile              # FROM nodered/node-red:4.0.9-minimal (Alpine)
│   │   └── entrypoint.sh           # Copy flows-base.json → flows.json, run npm sync, start node-red
│   ├── web-ui/
│   │   ├── Dockerfile              # Multi-stage: PHP 8.2 FPM + nginx + Vite build
│   │   ├── entrypoint.sh           # SSL gen, DB symlink, migrate, seed, cache config
│   │   ├── nginx.conf              # Nginx: HTTPS on 443, PHP-FPM proxy
│   │   └── start-services.sh       # Process manager: starts nginx + php-fpm
│   └── cctv-simulator/
│       └── Dockerfile              # Multi-stage: Python 3.12 Alpine + Pillow
│
├── docker-compose.yml              # Local dev: nodered:1880, webui:8001, cctv-simulator
│
├── nodered/
│   └── nodered-0-app.yml          # K8s: Deployment + ClusterIP Service
│
├── edge/                           # Traefik reverse proxy manifests
│   ├── edge-0-traefik.yml          # Traefik v3.0 Deployment + NodePort Service
│   ├── nodered-ingressroute.yml    # IngressRoute: mqtt-$BASE_ENDPOINT_URL:1880 → nodered (basic-auth)
│   ├── web-ui-ingressroute.yml     # IngressRoute: admin-$BASE_ENDPOINT_URL:443 (HTTPS + /api/ bypass)
│   └── ssl/                        # TLS cert/key for Traefik
│
├── kubernetescrd/
│   ├── kubernetes-crd-definition-v1.yml  # Traefik CRD: IngressRoute, Middleware, etc.
│   └── kubernetes-crd-rbac.yml     # ClusterRole + ClusterRoleBinding for Traefik
│
├── docs/
│   ├── DEPLOYMENT_CHECKLIST.md
│   └── specs/
│       ├── API-SPEC.md
│       ├── COMMAND-WATER-PUMP-LOGIC.md
│       ├── COMMAND-WATER-GATE-LOGIC.md
│       ├── COMMAND-TRASH-SCREEN-LOGIC.md
│       ├── COMMAND-TRASH-CONVEYOR-LOGIC.md
│       └── COMMAND-WATER-PROPULSION-LOGIC.md
│
├── PRPs/                           # Product Requirement Proposals (feature specs)
└── .gitlab-ci.yml                  # CI/CD pipeline: test → build → deploy
```

---

## 3. System Purpose and Scope

The simulator replaces physical IoT field hardware during development and testing. The real production system publishes sensor data over MQTT and receives device commands from control applications. This simulator:

1. Generates realistic `data_stream/` payloads using physics-based calculations (rainfall-to-water-level, gate movement in cm increments, sensor noise injection)
2. Subscribes to `data_command/` topics and plays back realistic command acknowledgment sequences (KEEPALIVE → INITIATED → ACKNOWLEDGE loop → data_stream → SUCCESS/ERROR/TIMEOUT)
3. Supports controllable failure modes (ERROR, TIMEOUT, INTERRUPT, DISCARDED) for testing edge cases
4. Provides a web UI for operators to configure stations and devices, then push the config to the running simulator without redeployment

---

## 4. Entry Points

### Node-RED (main simulation engine)

| Entry point | How triggered | What it does |
|---|---|---|
| `node-red --userDir .` (local) or `docker compose up` | Manual / Docker | Starts Node-RED on port 1880, loads `flows/flows.json` |
| `docker/nodered/entrypoint.sh` | Container start | Copies `flows-base.json` → `flows.json`, runs `npm run sync`, starts node-red |
| Inject node `84ad8867bab8e680` ("Start Simulation") | Web UI deploy / manual | Triggers configuration reload chain: Device Templates → Stations Config → Split → Simulation tick |
| MQTT subscribe `data_command/#` | External command sender | Triggers command processing pipeline |

### Web UI (Laravel)

| Entry point | How triggered | What it does |
|---|---|---|
| `php artisan serve` (local) or HTTPS on port 443 (Docker/K8s) | Browser / API client | Station/device CRUD, deploy trigger |
| `POST /api/v1/deploy` | REST API (Bearer token) | Export config → trigger Node-RED inject → trigger CCTV reload |
| `docker/web-ui/entrypoint.sh` | Container start | SSL gen, DB symlink to shared volume, `php artisan migrate`, DeviceTemplateSeeder, auto-seed |

### CCTV Simulator (Python)

| Entry point | How triggered | What it does |
|---|---|---|
| `python -u main.py` / container | Container start | Loads config, starts one `CameraThread` per CCTV_v1 device |
| `POST /reload` (HTTP on port 8080) | Web UI deploy | Forces immediate config reload without mtime check |
| Trigger file `/shared-data/.cctv-reload` | Web UI deploy (fallback) | Polled every 5s, triggers `manager.force_reload()` |
| `SIGHUP` | OS signal | Requests config reload |

### NPM scripts

| Script | Command | What it does |
|---|---|---|
| `npm run sync` | `node scripts/sync-functions.js` | Reads `function-mapping.json`, injects `functions/*.js` bodies into `flows/flows.json` |
| `npm run watch` | `node scripts/watch.js` | Auto-runs sync on any `functions/*.js` change |
| `npm run test` / `npm run test:functions` | `node --test scripts/test-function-nodes.js` | Runs 21 unit tests (Node 20 built-in `node:test`) |
| `npm version patch` | npm lifecycle | Runs `sync-version.js` to update version in `web-ui/config/app.php` |

---

## 5. Core Abstractions

### 5.1 managed_config.json — The Single Configuration Source

Everything flows from this JSON file. It is written by the Web UI and read by Node-RED and the CCTV Simulator.

```
managed_config.json
├── meta              { version, exported_at, exported_by }
├── device_templates  { WATER_PUMP_v1: { measurement, sensors: { SENSOR_KEY: { initial_value, min, max } } }, ... }
└── stations          { station_code: { area, runoff, simulate_mode, mqtt_targets, devices: [...] } }
```

**Key fields per device:**
- `template`: references a key in `device_templates`
- `commu_id`: short identifier (e.g. `"001-WATERPUMP"`)
- `simulate_mode` (optional device override, v4.35.0): overrides station-level `simulate_mode`
- `offline`: if true, device is skipped in simulation
- `offline_sensors`: list of sensor keys to suppress from payload

### 5.2 Node-RED Flow Groups

The flow is organized into groups (visible in the editor as tabs/subflows):

| Group ID | Name | Purpose |
|---|---|---|
| `286ccbc7b3e57d5b` | Global Utilities / Registry | Startup: load global helpers, command registry helper, cleanup |
| `69bce6bf58a8a979` | Configuration | Load device templates + stations config, fan-out to device groups |
| `94692f37c89a5386` | MQTT Publish | Prepare payload, route to MQTT brokers |
| `0d9b6b916e3f127c` | Simulate Mode | Per-measurement simulation functions |
| `a6d6bcba881f179b` | Testing Mode | Per-measurement testing functions (deterministic values) |
| `8a87f018aeb67d26` | Command Handlers | Incoming command processing (5 device types) |
| `c9f19205654a1b7c` | Command Input | Build data_command payload from raw MQTT |
| `de9c0cb8d22c546b` | Context Management | Admin: manage/delete/null flow context, refuel |

### 5.3 Function Sync Workflow

`functions/*.js` files are the **source of truth** for Node-RED function node code. The flow JSON (`flows/flows.json`) embeds this code in its `"func"` property. The sync process:

```
functions/command-water-pump.js
  └─ header comment contains: "Node ID: 1f42d26df5a01e57"
  └─ scripts/sync-functions.js reads function-mapping.json
  └─ finds node 1f42d26df5a01e57 in flows.json
  └─ replaces flows.json[node].func with file body (header stripped)
```

**Constraint:** No NPM modules may be used inside function nodes. Only Node.js built-ins (accessed via `global.get("fs")`) and globals registered at startup.

### 5.4 Global Context Functions

Registered at startup by `global-utilities-function.js` and `command-registry-helper.js`. Available to all function nodes via `global.get("name")`:

| Function | Purpose |
|---|---|
| `sim_clamp(v, min, max)` | Clamp numeric value |
| `sim_randomValue(min, max)` | Random float in range |
| `sim_addSensorValueToPayload(data, prefix, commuId, key, value, offlines)` | Append sensor field, respecting offline_sensors list |
| `sim_getSensorValue(ctxPrefix, flow, device, template, sensorKey)` | Get sensor value from flow context; resets to `initial_value` when `_config_version` changes |
| `sim_calculateRainfallEffect({rainfallRate, runoff, timeStep, area})` | Physics: rainfall → volume |
| `sim_calculateGateFlow({width, height, doorLevel, upstream, downstream})` | Physics: gate → flow rate |
| `sim_calculatePumpFlow({nominalFlow, pumpStatus, efficiency})` | Physics: pump flow |
| `sim_calculateWaterLevelChange({...})` | Physics: combined level change |
| `sim_manageRainfallHistory({...})` | Rolling 1-hour rainfall history |
| `cmd_isCommandProcessed(flow, node, commandId, serial)` | Duplicate command detection |
| `cmd_addCommandRegistry(flow, node, commandId, serial, executionId)` | Register new command |
| `cmd_completeCommandRegistry(flow, node, commandId, serial, finalStatus)` | Mark command complete |

### 5.5 Command Processing Pattern

All 5 command handlers (WATER_PUMP, WATER_GATE, TRASH_SCREEN, TRASH_CONVEYOR, WATER_PROPULSION) follow the same pattern:

```
1. Create executionId = `${commandId}_${Date.now()}`
2. Duplicate check: cmd_isCommandProcessed → return null if seen
3. FIFO busy check: scan registry[serial] for any completedTime === null → reject with ERROR
4. Register: cmd_addCommandRegistry
5. Load mode from flow context: prev_{SERIAL}_MODE (default: NORMAL)
6. Multi-checkpoint validation (1–3 checkpoints depending on device)
7. Send timed ACK sequence via setTimeout:
   Phase 1 KEEPALIVEs → INITIATED → Phase 2 KEEPALIVEs / ACKNOWLEDGE loop → data_stream → SUCCESS/ERROR/TIMEOUT/INTERRUPT
8. Immediately mark complete: cmd_completeCommandRegistry (MUST happen before setTimeout delays)
```

**Command registry** (stored in `flow._command_registry`):
```json
{
  "STATION999-001-WATERPUMP": {
    "cmd123": {
      "executionId": "cmd123_1699012345678",
      "startTime": 1699012345678,
      "completedTime": null,
      "finalStatus": null
    }
  }
}
```
TTL: 7 days for completed commands. Daily cleanup via inject node → `command-registry-cleanup.js`.

### 5.6 Per-Device simulate_mode (v4.35.0)

`split-stations-devices-data.js` groups devices by `measurement|type|effectiveMode`. The effective mode resolves as:

```
device.simulate_mode ?? station.simulate_mode ?? 1
```

A mixed-mode station emits two messages per measurement/type per tick — one for simulate mode, one for testing mode. The flow's "Switch by simulate_mode" node routes each to the appropriate simulation group.

### 5.7 CCTV Simulator Architecture

The Python service is entirely independent of Node-RED. It reads `managed_config.json` directly.

```
main.py
├── wait_for_config()          blocks until managed_config.json exists
├── CameraManager.start()      parses config, starts CameraThread per CCTV_v1 device
├── ReloadServer (port 8080)   HTTP server for POST /reload
└── Main loop (every 5s)
    ├── check /shared-data/.cctv-reload trigger file
    ├── check SIGHUP flag
    └── periodic stale file cleanup (every 60s)

CameraThread (one per camera)
└── Every interval_seconds:
    ├── resolve_background(background_image, backgrounds_dir)
    ├── create_image(bg_path, local_path, device_name, device_id)  ← Pillow JPEG with timestamp
    └── for each ftp_target: upload_to_ftp(local_path, filename, target)
```

Config reload is **hot**: `CameraManager._load_and_apply()` stops threads for removed/changed cameras and starts new ones, without restarting the process.

### 5.8 Web UI — Deploy Flow

The "Deploy to Node-RED" action (web UI button or `POST /api/v1/deploy`) executes:

```
DeployController::deploy()
1. exportToJson()               query Station/Device/DeviceTemplate models → managed_config dict
2. File::put(/shared-data/managed_config.json)   write to shared volume
3. curl POST http://cctv-simulator-0-app:8080/reload   instant CCTV reload
4. file_put_contents(/shared-data/.cctv-reload)  fallback trigger file
5. curl POST http://nodered-0-app:1880/inject/84ad8867bab8e680   trigger Node-RED config reload
6. sleep(1), fetch pod logs via KubernetesLogService   verification
```

---

## 6. Key Dependencies

### Node-RED / JavaScript

| Dependency | Version | Purpose |
|---|---|---|
| `node-red` | 4.0.9 (Docker base) | Flow runtime |
| Node.js | >=14.0.0 (engine) | JavaScript runtime |
| Built-in `fs` | stdlib | Config file reading (exposed via `functionGlobalContext`) |
| Built-in `node:test` | Node 20+ | Function-node test harness |

No third-party NPM packages are used inside function nodes (hard constraint).

### Web UI (PHP/Laravel)

From `web-ui/composer.json`:
- Laravel 11, PHP 8.2
- `laravel/sanctum` — API token authentication
- `sqlite` — embedded database (persisted on shared volume in production)
- Vite + npm for frontend asset bundling
- Playwright for browser tests

### CCTV Simulator (Python)

From `cctv-simulator/requirements.txt`:
- Python 3.12
- `Pillow` — JPEG image generation with FreeType text overlay
- `ftplib` (stdlib) — FTP upload
- `pytest` — test runner

---

## 7. Infrastructure

### Docker Compose (Local Development)

```
docker-compose.yml
├── nodered          port 1880       FROM nodered/node-red:4.0.9-minimal
├── webui            port 8001→443   FROM php:8.2-fpm-alpine (multi-stage)
└── cctv-simulator   (no host port)  FROM python:3.12-alpine (multi-stage)

shared-data volume (named, local driver)
├── managed_config.json   ← written by webui, read by nodered + cctv-simulator
├── database.sqlite       ← Laravel DB, symlinked from webui container
├── flows.json            ← copy of running flows
└── .cctv-reload          ← trigger file for CCTV config reload
```

Startup order: `nodered` (health: HTTP 1880) → `webui` → `cctv-simulator`

### Kubernetes (Production)

Three separate Deployments, all `strategy: Recreate`, all pinned to node `intranet`:

```
Namespace: default

Deployments:
├── nodered-0-app      (replicas: 1)   image: .../nodered:$TAG
│   ├── initContainer: alpine fix-permissions (chmod 777 /shared-data)
│   ├── volumes: nodered-data (hostPath: /mnt/data/nodered/data)
│   │            shared-data  (hostPath: /mnt/data/nodered/shared)
│   └── Service: nodered-0-app:1880 (ClusterIP)
│
├── web-ui-0-app       (replicas: 1)   image: .../webui:$TAG
│   ├── env: NODERED_API_URL=http://nodered-0-app:1880
│   │        CCTV_RELOAD_URL=http://cctv-simulator-0-app:8080/reload
│   ├── volumes: shared-data (hostPath: /mnt/data/nodered/shared)
│   │            web-ui-data (hostPath: /mnt/data/web-ui/data)
│   └── Service: web-ui-0-app:443 (ClusterIP)
│
└── cctv-simulator-0-app (replicas: 1) image: .../cctv-simulator:$TAG
    ├── env: CONFIG_PATH=/shared-data/managed_config.json
    │        TRIGGER_FILE=/shared-data/.cctv-reload
    │        FTP_HOST/PORT/PASSWORD (from CI/CD variables)
    ├── volumes: shared-data     (hostPath: /mnt/data/nodered/shared)
    │            cctv-backgrounds (hostPath: /mnt/data/cctv-simulator/backgrounds)
    └── Service: cctv-simulator-0-app:8080 (ClusterIP, reload endpoint)
```

**Host volume structure:**
```
/mnt/data/
├── nodered/
│   ├── data/       → /data in nodered pod (flows.json, settings.js, Node-RED state)
│   └── shared/     → /shared-data in ALL pods (config, DB, trigger files)
├── web-ui/
│   └── data/       → /app/storage in webui pod (Laravel logs, sessions)
└── cctv-simulator/
    └── backgrounds/ → /app/backgrounds in cctv pod
```

### Edge / Ingress (Traefik v3.0)

```
Traefik Deployment (edge-0-traefik)
├── Entrypoints: :80 (web), :443 (websecure), :1880 (nodered)
├── Provider: kubernetescrd
└── IngressRoutes:
    ├── nodered-ui-ingressroute
    │   Host(mqtt-$BASE_ENDPOINT_URL):1880 → nodered-0-app:1880 [basic-auth]
    └── web-ui-websecure-ingressroute
        Host(admin-$BASE_ENDPOINT_URL)/api/ → web-ui-0-app:443 [no auth, for REST API]
        Host(admin-$BASE_ENDPOINT_URL)      → web-ui-0-app:443 [basic-auth, TLS]

CRDs applied: IngressRoute, Middleware, TLSOption, ServersTransport, etc.
RBAC: ClusterRole traefik-ingress-controller (read services/endpoints/ingresses/traefik CRDs)
```

### CI/CD Pipeline (GitLab)

```
.gitlab-ci.yml — 3 stages

test (merge_request_event only, allow_failure: true)
├── test-functions   docker run node:20-alpine → npm run test:functions
├── test-phpunit     docker run php:8.3-cli    → php artisan test
└── test-playwright  docker run playwright:v1.49.0 → npx playwright test

build (on version tag v\d+ auto; on main manual)
├── build-nodered         docker build docker/nodered/Dockerfile → push
├── build-webui           docker build docker/web-ui/Dockerfile  → push
└── build-cctv-simulator  docker build docker/cctv-simulator/Dockerfile → push

deploy (manual)
├── deploy-edge           kubectl apply CRDs + Traefik + IngressRoutes
├── deploy-nodered        sync code from image to host volume → kubectl apply
├── deploy-webui          prepare dirs → kubectl apply
└── deploy-cctv-simulator sync backgrounds from image → kubectl apply
```

Production URLs:
- Node-RED: `http://mqtt-simulator.rpro.digitalsmart.city:1880`
- Web UI: `https://admin-simulator.rpro.digitalsmart.city`

---

## 8. How Node-RED Flows Connect to the Rest of the System

```
                    ┌─────────────────────┐
                    │    Web UI (Laravel)  │
                    │    :443              │
                    │  Station/Device CRUD │
                    └──────────┬──────────┘
                               │ POST /inject/84ad8867bab8e680
                               │ writes /shared-data/managed_config.json
                               │ POST /reload (CCTV, port 8080)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Node-RED (:1880)                              │
│                                                                   │
│  [Inject: Start Simulation]                                       │
│       │                                                           │
│       ├─► [Device Templates]  ──► flow._device_templates         │
│       │                                                           │
│       └─► [Stations Config]   ──► flow._stations                │
│               │  (reads /shared-data/managed_config.json)        │
│               ▼                                                   │
│       [Split Stations & Devices]                                  │
│               │  fans out one msg per (measurement|type|mode)    │
│               ▼                                                   │
│       [Switch: simulate_mode?]                                    │
│          /                    \                                   │
│   simulate_mode=1          simulate_mode=0                       │
│   (realistic)              (deterministic)                        │
│       │                         │                                 │
│   simulate-*.js            testing-*.js                          │
│       │                         │                                 │
│       └────────────┬────────────┘                                │
│                    ▼                                              │
│       [prepare-mqtt-payload-*.js]                                 │
│         builds combined device payload                            │
│                    ▼                                              │
│       [publish-to-mqtt-server.js]                                │
│         routes to mqtt_targets (e.g. "dev-cluster")              │
│                    │                                              │
└────────────────────┼──────────────────────────────────────────────┘
                     │ MQTT publish
                     ▼
          ┌─────────────────────┐
          │   MQTT Broker(s)    │
          │   dev-cluster:1883  │
          └──────┬─────────┬───┘
                 │         │
    data_stream/ │         │ data_command/
                 ▼         │
          [Consumer apps]  │
          (control system) │
                           │
                    ┌──────┴───────────────────────────────────────┐
                    │  Node-RED MQTT subscribe: data_command/#      │
                    │                                               │
                    │  [MQTT In node]                              │
                    │      ▼                                        │
                    │  [parse-command.js]                          │
                    │      ▼                                        │
                    │  [build-data-command-payload.js]             │
                    │      ▼                                        │
                    │  [Global Registry Helper] ──────────────┐    │
                    │      ▼                                   │    │
                    │  [Switch: by measurement]               │    │
                    │   ├─ WATER_PUMP  → command-water-pump  │    │
                    │   ├─ WATER_GATE  → command-water-gate  │    │
                    │   ├─ TRASH_SCREEN → command-trash-screen│   │
                    │   ├─ TRASH_CONVEYOR → command-trash-conv│   │
                    │   └─ PROPULSION → command-water-propul  │    │
                    │           │                              │    │
                    │           └─► timed ACK sequence via    │    │
                    │               setTimeout (3s intervals) │    │
                    │                    ▼                     │    │
                    │           MQTT publish: data_ack/        │    │
                    │                    ▼                     │    │
                    │           cmd_completeCommandRegistry ◄──┘    │
                    └──────────────────────────────────────────────┘
```

### MQTT Topic Scheme

```
Sensor data (published by Node-RED periodically):
  data_stream/{station_id}/measurement_device/water_level
  data_stream/{station_id}/measurement_device/rainfall
  data_stream/{station_id}/measurement_device/water_quality
  data_stream/{station_id}/water_gate
  data_stream/{station_id}/water_pump
  data_stream/{station_id}/mobile_pump
  data_stream/{station_id}/trash_screen
  data_stream/{station_id}/trash_conveyor
  data_stream/{station_id}/propulsion

Commands (received by Node-RED from control system):
  data_command/{station_id}/water_pump
  data_command/{station_id}/water_gate
  data_command/{station_id}/trash_screen
  data_command/{station_id}/trash_conveyor
  data_command/{station_id}/propulsion

Acknowledgments (published by Node-RED in response to commands):
  data_ack/{station_id}/water_pump
  data_ack/{station_id}/water_gate
  data_ack/{station_id}/trash_screen
  data_ack/{station_id}/trash_conveyor
  data_ack/{station_id}/propulsion
```

### Field Naming Conventions (Critical)

| Device | Command field | ACK field | Flow context key | data_stream key |
|---|---|---|---|---|
| WATER_PUMP | `switch_on` | `switch_on` | `STATUS_PUMP_ON` | `STATUS_PUMP_ON` |
| WATER_GATE | `target_door_level` | `door_level` | `SENSOR_DOOR_LEVEL` | `SENSOR_DOOR_LEVEL` |
| TRASH_SCREEN | `trash_screen_on` | `trash_screen_on` | `STATUS_SCREEN_ON` | `STATUS_SCREEN_ON` |
| TRASH_CONVEYOR | `trash_conveyor_on` | `trash_conveyor_on` | `STATUS_CONVEYOR_ON` | `STATUS_CONVEYOR_ON` |
| WATER_PROPULSION | `switch_on` | `switch_on` | `STATUS_PROPULSION_ON` | `STATUS_PROPULSION_ON` |

Flow context keys are always prefixed: `prev_{SERIAL}_{KEY}` (e.g. `prev_STATION999-001-WATERPUMP_STATUS_PUMP_ON`).

---

## 9. Test Coverage

| Suite | Runner | Count | Scope |
|---|---|---|---|
| Function-node unit tests | `npm run test:functions` (node:test) | 21 tests | split-stations grouping, resolveSimulateMode, grep-lint on 5 command handlers |
| PHP unit + feature tests | `php artisan test` (PHPUnit) | 305 tests, 822 assertions | Station/Device/Template CRUD, Deploy, API, Services |
| Browser tests | `npx playwright test` | 31 tests | Station CRUD, device management, deploy flow, simulate_mode toggle |
| CCTV simulator tests | `python -m pytest tests/` | 53 tests | Config loading (20), image gen (11), camera threading (8), FTP upload (6), trigger (3), reload server (5) |

---

## 10. Version History Highlights

| Version | Key change |
|---|---|
| v4.35.1 | Node 20 test harness (21 tests), CI test stage, Playwright `simulate_mode` test re-enabled |
| v4.35.0 | Per-device `simulate_mode` override; mixed-mode station support |
| v4.34.3 | Fuel passive refill (+15%/interval when OFF); `_config_version` stamp for sensor reset |
| v4.34.0 | Combined device payloads (multiple devices of same type merged into single MQTT message) |
| v4.19 | Database persistence: SQLite symlinked to shared volume, survives redeployment |
| v4.14 | Kubernetes split-pod architecture (Node-RED, Web UI, CCTV as separate Deployments) |
| v4.9 | Water Gate abort feature; `disable_abort` per-device config |
| v4.6 | FIFO queue processing; one in-progress command per device serial |
| v4.5 | Duplicate command prevention; command registry with 7-day TTL |
