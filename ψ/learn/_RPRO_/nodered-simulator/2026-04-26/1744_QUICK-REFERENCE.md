# nodered-simulator — Quick Reference

**Version:** 4.35.1 | **Last Updated:** 2026-04-26 | **Timezone:** GMT+7 (Asia/Bangkok)

---

## 1. What Is This?

`nodered-simulator` is an internal **water management system simulator** that runs on Node-RED. It eliminates the need for physical hardware by generating physics-based, realistic sensor data and publishing it over MQTT — making it usable for IoT platform development, integration testing, algorithm validation, and training.

**What it simulates:**

- **Controllable devices** — Water gates, water pumps, mobile pumps, water propulsion units, trash screens, trash conveyors
- **Measurement-only devices** — Water level, rainfall, water quality (pH/O2/salinity/conductivity/temp), water velocity, water flow, air quality
- **CCTV cameras** — JPEG snapshot generation with timestamp overlay, uploaded via FTP (handled by a separate Python service)

**Why it exists:**

The production system is a real Thai water infrastructure control platform (`rpro.digitalsmart.city`). Physical hardware is expensive, geographically distributed, and not available for dev/test. This simulator mirrors the full MQTT command/ack lifecycle so the upstream system cannot tell the difference.

**Three services run together:**

| Service | Stack | Purpose |
|---|---|---|
| `nodered` | Node-RED (Node.js) | Simulation engine + MQTT publisher |
| `webui` | Laravel (PHP) + SQLite | Config manager UI, deploys `managed_config.json` |
| `cctv-simulator` | Python 3.12 | Generates CCTV JPEG snapshots, uploads via FTP |

---

## 2. How to Run

### Docker (Recommended — runs all three services)

```bash
git clone https://git.rpro.digitalsmart.city/grandline/rpro/simulator/nodered-simulator
cd nodered-simulator
docker compose up --build
```

| Service | URL |
|---|---|
| Node-RED UI | http://localhost:1880 |
| Web UI (Laravel) | http://localhost:8001 |

The Web UI port maps `8001 → 443` inside the container (HTTPS internally, HTTP externally on localhost).

**Startup sequence enforced by `depends_on`:**
`nodered` (healthy) → `webui` (healthy) → `cctv-simulator`

**Shared volume:** All three containers share a Docker volume `/shared-data` which holds `managed_config.json` and the SQLite database. Node-RED entrypoint always starts from the image-baked `flows-base.json` (git is source of truth), then runs `npm run sync` to inject current function code.

### Local Development

**Node-RED only:**

```bash
node-red --userDir .
# UI: http://127.0.0.1:1880/
```

**Web UI only (separate terminal):**

```bash
cd web-ui
composer install && npm install
php artisan migrate
php artisan serve        # http://127.0.0.1:8000/
npm run dev              # Vite asset watcher
```

**Reload Node-RED config manually after Web UI deploy:**

```bash
curl -X POST http://localhost:1880/inject/84ad8867bab8e680
```

---

## 3. Key Configuration Options

### `config/managed_config.json`

The master runtime configuration. Contains two top-level keys: `device_templates` and `stations`.

**Station parameters:**

| Field | Type | Description |
|---|---|---|
| `area` | number | Catchment area in m² (used for rainfall physics) |
| `runoff` | float (0–1) | Runoff coefficient |
| `rain_to_rise_delay` | number | Seconds before rainfall raises water level |
| `passive_drainage_rate` | number | Natural drainage rate in cm/second |
| `simulate_mode` | 0 or 1 | 1 = physics-realistic, 0 = testing/fixed mode |
| `enabled` | bool | false = station is skipped entirely |
| `mqtt_targets` | array | Which MQTT clusters to publish to (see below) |

**Per-device `simulate_mode` override (v4.35.0):** Set `simulate_mode` on a device entry to override the station-level default. Mixed-mode stations emit two separate `data_stream` messages per measurement type per tick.

**Config load priority (Node-RED reads in order):**
1. `/shared-data/managed_config.json` — Docker/K8s persistent volume
2. `/data/config/managed_config.json` — alternative mount
3. `config/managed_config.json` — local project root
4. `/data/config/managed_config.default.json` — bundled Day-0 fallback

### Environment Variables

**Node-RED container:**

| Variable | Default | Purpose |
|---|---|---|
| `TZ` | `Asia/Bangkok` | Timezone |
| `MQTT_BROKER_DEV` | `dev.rpro.digitalsmart.city` | Dev MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT port |

**Web UI container:**

| Variable | Default | Purpose |
|---|---|---|
| `NODERED_API_URL` | `http://nodered:1880` | Node-RED API for triggering reloads |
| `APP_ENV` | `local` | Laravel app environment |
| `DB_CONNECTION` | `sqlite` | Always SQLite |

**CCTV simulator container:**

| Variable | Default | Purpose |
|---|---|---|
| `CONFIG_PATH` | `/shared-data/managed_config.json` | Config file path |
| `OUTPUT_DIR` | `/tmp/cctv-output` | Where JPEG snapshots are written |
| `BACKGROUNDS_DIR` | `/app/backgrounds` | Background image directory |
| `CONFIG_RELOAD_SECONDS` | `60` | How often CCTV reloads config |

### MQTT Clusters

The publish-to-MQTT node routes messages by `mqtt_targets` in the station config. Five named clusters are supported:

| Key in config | Output slot |
|---|---|
| `dev-cluster` or `test-cluster` or `staging-cluster` | Output 1 |
| `dds-cluster` | Output 2 |
| `hdy-cluster` | Output 3 |
| `rid-cluster` | Output 4 |
| `swoc-cluster` | Output 5 |

### `functions/function-mapping.json`

Maps each `functions/*.js` filename to its Node-RED node ID. The `npm run sync` script reads this to inject function code into `flows/flows.json`. Do not edit node IDs by hand.

---

## 4. What the Flows Do

There is one Node-RED tab: **"[Developing] Simulator flow"**, containing 13 groups:

### Initialization Groups

**`Initial device template/station configuration`**
Runs on startup (and on manual reload). Reads `managed_config.json` from the shared volume. Sets `_device_templates`, `_stations`, and `_config_version` in flow context. `split-stations-devices-data.js` groups devices by `measurement|type|effectiveSimulateMode` key, emitting one message per group per tick.

**`To INITIAL "Global Utilities function"`**
Registers shared simulation helpers as global functions: `sim_clamp`, `sim_randomValue`, `sim_getSensorValue`, `sim_addSensorValueToPayload`, `sim_calculateRainfallEffect`, `sim_calculateGateFlow`, `sim_calculatePumpFlow`, etc. Also registers command registry helpers (`cmd_isCommandProcessed`, `cmd_addCommandRegistry`, `cmd_completeCommandRegistry`).

### Simulation Groups

**`SIMULATE REALISTIC data_stream/xxx/xxx`** (`simulate_mode = 1`)
Physics-based simulation. Contains the realistic simulation nodes:
- `simulate-rainfall.js` — generates rain rate, accumulation, time-based resets
- `simulate-water-level.js` — base water level sensor
- `calculate-water-level.js` — combines rainfall effect + gate drainage + pump drainage + natural drainage into final water level reading
- `simulate-water-gate.js` — gate door position, flow rate
- `simulate-water-pump.js` — pump performance curves, temperature, vibration, flow
- `simulate-mobile-pump.js` — portable pump with GPS, battery, fuel consumption
- `simulate-water-propulsion.js` — engine RPM, coolant, oil, battery, fuel, GPS
- `simulate-trash-screen.js` / `simulate-trash-conveyor.js` — motor parameters, electrical
- `simulate-water-quality.js` — pH, O2, salinity, conductivity, temperature
- `simulate-water-velocity.js` / `simulate-water-flow.js` — flow measurement
- `simulate-air-quality.js` — PM2.5, PM10, CO2, temp, humidity

**`SIMULATE FIXED data_stream/xxx/xxx`** (`simulate_mode = 0`)
Testing mode with fixed/predictable values. Uses `testing-*.js` counterparts for each device type.

**`Separate machine/device type`** (two groups, one per mode)
Switch nodes that route each device type to its corresponding simulate/testing function node.

### Command Processing Groups

**`Publish "data_command"`**
Contains `build-data-command-payload.js` — a hardcoded test helper that fires a sample WATER_PUMP or WATER_GATE command. Used for manual testing within the flow editor (not for production).

**`data_command/data_ack`** (parent group wrapping the two below)

**`Recive "data_command" & Return "data_ack"`**
Core command handler group. Subscribes to `data_command/#`. Parses topic → station + measurement, routes by measurement type to one of five command handlers:
- `command-water-pump.js`
- `command-water-gate.js`
- `command-trash-screen.js`
- `command-trash-conveyor.js`
- `command-water-propulsion.js`

Each handler performs: duplicate check → FIFO busy check → register → multi-checkpoint ACK loop → mark complete.

### Publishing Group

**`Pushlish payload to MQTT Server`**
`prepare-mqtt-payload-simulate.js` buffers messages from the simulation tick, then `publish-to-mqtt-server.js` routes them to the correct MQTT broker output nodes based on `mqtt_targets`.

### Utility Groups

**`To CLEAR "Flow Context Data"`**
Inject nodes for maintenance:
- `manage-flow-context.js` — reset specific flow context keys by station/device/sensor
- `delete-all-flow-context.js` — wipe all `prev_*` flow context keys
- `set-null-all-flow-context.js` — null out all flow context
- `refuel-all-devices.js` — resets `SENSOR_FUEL_LEVEL` to max and clears `ERROR_FUEL` for all fuel-bearing devices

---

## 5. How to Modify / Extend Flows

**All function code lives in `functions/*.js` — never edit `flows/flows.json` directly.**

### Edit an existing function

```bash
# 1. Edit the file
vim functions/simulate-water-pump.js

# 2. Sync to flows.json
npm run sync

# 3. In Node-RED UI: Import → flows/flows.json → Deploy
```

### Add a new device type

1. Add a new `functions/simulate-<type>.js` and `functions/testing-<type>.js`
2. Add a new `functions/command-<type>.js` if it accepts commands
3. Register the node ID in `functions/function-mapping.json`
4. In Node-RED UI: add the new function node to the correct group, wire it into the "Separate machine/device type" switch, connect to the MQTT publish chain
5. Run `npm run sync` and redeploy
6. Add the device template to `managed_config.json` under `device_templates`

### Add a new station

Use the Web UI at http://localhost:8001, then click "Deploy to Node-RED". The Web UI writes `managed_config.json` to `/shared-data/` and calls the Node-RED inject endpoint to trigger a config reload at runtime (no Node-RED redeploy needed).

### Change execution mode for testing

```javascript
// In Node-RED debug console or via an inject node
flow.set("prev_STATION999-001-WATERPUMP_MODE", "ERROR1");
flow.set("prev_STATION999-001-WATERPUMP_ERROR", 0);
```

Available modes: `NORMAL`, `ERROR1`, `ERROR2`, `TIMEOUT1`, `TIMEOUT2`, `INTERRUPT1`, `INTERRUPT2`, `DISCARDED` (Water Gate adds `ERROR3`, `TIMEOUT3`, `INTERRUPT3`, `ABORTED`).

### Watch mode (auto-sync on save)

```bash
npm run watch
```

---

## 6. NPM Scripts

All scripts are in `package.json`; no npm dependencies are installed (built-in Node.js modules only).

| Script | Command | What it does |
|---|---|---|
| `npm run sync` | `node scripts/sync-functions.js` | Reads `function-mapping.json`, injects `functions/*.js` code into matching nodes in `flows/flows.json` |
| `npm run watch` | `node scripts/watch.js` | Watches `functions/` for changes, auto-runs sync |
| `npm run sync:version` | `node scripts/sync-version.js` | Syncs `package.json` version into `web-ui/config/app.php` (footer display) |
| `npm run test` | `node --test scripts/test-function-nodes.js` | Runs all function-node tests (21 tests via Node 20 built-in `node:test`) |
| `npm run test:functions` | Same as above | Explicit alias for function-node test suite |
| `npm version patch` | (npm lifecycle) | Bumps version, auto-runs `sync:version`, stages `web-ui/config/app.php`, creates git tag |

**Testing commands (not npm scripts):**

```bash
# Node-RED function-node tests (21 tests)
npm run test:functions

# Web UI unit + feature tests (305 tests, 822 assertions)
cd web-ui && php artisan test

# Web UI browser tests (31 Playwright tests)
cd web-ui && npx playwright test

# CCTV simulator tests (53 pytest tests)
cd cctv-simulator && python -m pytest tests/ -v

# Water Gate abort integration tests
cd scripts && ./test-abort-feature.sh
```

---

## 7. Notable Gotchas

**Functions/*.js is the source of truth — flows.json is generated.**
Never commit hand-edits to `flows/flows.json` function code. The sync script will overwrite them. Always edit `functions/` and run `npm run sync`.

**No npm modules in function nodes.**
All function code (`functions/*.js`) must use only built-in Node.js modules (`fs`, `path`, etc.). This is a hard constraint — Node-RED function nodes do not have access to `node_modules`.

**Registry completion must be immediate, not inside setTimeout.**
When a command handler determines its final status (SUCCESS/ERROR/TIMEOUT/INTERRUPT), it must call `cmd_completeCommandRegistry` immediately. Only the ACK send is delayed with `setTimeout`. Putting completion inside the timeout causes race conditions with ABORT commands and the FIFO busy check.

**Multiple Node-RED instances on the same MQTT broker = ghost messages.**
If you see ACK messages without `_debug_execution_id`, another Node-RED instance is processing the same commands. Check `ps aux | grep node-red`. The production fix is to add station filtering at the top of each command handler.

**setTimeout timers survive Node-RED hot-deploy.**
If you deploy mid-execution, previously scheduled timers keep firing. The only clean reset is a full Node-RED restart.

**Config reload does not reset flow context state.**
When you deploy a new `managed_config.json`, device state (`prev_*` variables) persists in flow context. Use the "To CLEAR Flow Context Data" inject nodes to reset specific devices, or use `delete-all-flow-context.js` to wipe everything.

**`_config_version` stamp controls sensor value reset.**
`sim_getSensorValue` compares `_config_version` in flow context against the last-seen version. When they differ, it resets the sensor to `initial_value`. This fires on every config reload — intentional behaviour for picking up new sensor ranges.

**The Web UI is on port 8001 in Docker, not 8000.**
`docker-compose.yml` maps `8001:443`. The local dev `php artisan serve` runs on 8000 by default.

**SQLite database persists on the shared volume in K8s.**
`/shared-data/database.sqlite` — delete this file on the host to do a full data reset. The entrypoint will recreate it on next pod start and re-run migrations + `DeviceTemplateSeeder`.

**`DeviceTemplateSeeder` always runs on deploy.**
It uses `updateOrCreate`, so it is idempotent. New device templates added in code will appear in existing deployments without wiping data.

**Laravel `Collection::filter()` breaks Alpine.js.**
`filter()` preserves original array keys, turning arrays into objects when serialized via `Js::from()`. Always chain `->values()` after `filter()` to re-index before passing to the frontend.

**Fuel dead state.**
WATER_PROPULSION and MOBILE_PUMP permanently stop when fuel drops below 5% (`errorFuel`). Since v4.34.3, fuel passively refills at +15% per simulation interval when the device is OFF. If a device is stuck, use the "Refuel All Devices" inject node or set `SENSOR_FUEL_LEVEL` directly in flow context.

**flows.json node structure in Docker.**
The Node-RED entrypoint always copies the image-baked `flows-base.json` to `flows.json` on every container start, then runs `npm run sync` to inject function code. This means any manual in-UI edits to nodes (not function code) are lost on container restart. Structural changes must be made in the flows JSON and committed.

---

## Production URLs

| Service | URL |
|---|---|
| Node-RED | http://mqtt-simulator.rpro.digitalsmart.city:1880 |
| Web UI | https://admin-simulator.rpro.digitalsmart.city |

**CI/CD pipeline (GitLab):**
`build-nodered` → `build-webui` → `build-cctv-simulator` → `deploy-nodered` → `deploy-webui` → `deploy-cctv-simulator`
