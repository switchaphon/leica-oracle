# API Surface: nodered-simulator
> Captured: 2026-04-26  
> Source: `/Users/switchaphon/_RPRO_/internal-server/nodered-simulator`  
> Scope: flows.json, flows/, edge/, config/, docker-compose.yml, kubernetescrd/, cctv-simulator/, web-ui/

---

## 1. MQTT Topics

The entire system communicates through three MQTT topic families. Topic strings are lower-cased at publish time.

### 1.1 Published by Node-RED (outbound — simulator → downstream)

| Topic pattern | Payload `measurement` | Direction |
|---|---|---|
| `data_stream/{stationId}/water_pump` | `WATER_PUMP` | Node-RED → broker |
| `data_stream/{stationId}/water_gate` | `WATER_GATE` | Node-RED → broker |
| `data_stream/{stationId}/mobile_pump` | `MOBILE_PUMP` | Node-RED → broker |
| `data_stream/{stationId}/propulsion` | `PROPULSION` | Node-RED → broker |
| `data_stream/{stationId}/trash_screen` | `TRASH_SCREEN` | Node-RED → broker |
| `data_stream/{stationId}/trash_conveyor` | `TRASH_CONVEYOR` | Node-RED → broker |
| `data_stream/{stationId}/measurement_device/water_level` | `MEASUREMENT_DEVICE` / `WATER_LEVEL` | Node-RED → broker |
| `data_stream/{stationId}/measurement_device/rainfall` | `MEASUREMENT_DEVICE` / `RAINFALL` | Node-RED → broker |
| `data_stream/{stationId}/measurement_device/water_quality` | `MEASUREMENT_DEVICE` / `WATER_QUALITY` | Node-RED → broker |
| `data_ack/{stationCode}/{measurement}` | ACK lifecycle | Node-RED → broker |

### 1.2 Subscribed by Node-RED (inbound — command bus)

| Topic pattern | Description |
|---|---|
| `data_command/+/+` | Receives device commands. `+/+` = `{stationCode}/{measurement}` |

---

## 2. Message Formats

All payloads are JSON. Measurement field keys follow the naming pattern `{STATION_PREFIX}-{COMMU_ID}_{SENSOR_KEY}`.

### 2.1 `data_stream` envelope (base fields — all device types)

```json
{
  "station": "stationId",
  "measurement": "WATER_PUMP",
  "type": null,
  "timestamp": 1714000000000
}
```

Dynamic sensor fields are appended as flat keys at the top level, e.g.:
```json
{
  "station": "station001",
  "measurement": "WATER_PUMP",
  "type": null,
  "timestamp": 1714000000000,
  "STATION001-001-WATERPUMP_STATUS_PUMP_ON": 1,
  "STATION001-001-WATERPUMP_SENSOR_CURRENT": 85.42,
  ...
}
```

### 2.2 Sensor fields by device type

#### WATER_PUMP
| Field | Type | Notes |
|---|---|---|
| `STATUS_PUMP_ON` | int (0/1) | Pump running state |
| `SELECTOR` | string | `ONLINE` / `OFFLINE` / `AUTO` |
| `MODE` | string | `NORMAL` / `ERROR` |
| `SENSOR_VIBRATION` | float | mm/s, 2dp |
| `SENSOR_CURRENT` | float | A, 2dp |
| `SENSOR_VOLTAGE` | float | V, 2dp |
| `SENSOR_POWER` | float | kW, 2dp |
| `SENSOR_TEMP_MAIN_BEARING` | float | °C, 2dp |
| `SENSOR_TEMP_SUPPORT_BEARING` | float | °C, 2dp |
| `SENSOR_TEMP_STATOR_WINDING_1/2/3` | float | °C, 2dp |
| `FLOW_RATE` | float | 3dp |
| `EFFICIENCY` | float | 3dp |
| `ERROR_LEAKAGE_CONNECTION_HOUSING` | int (0/1) | |
| `ERROR_LEAKAGE_STATOR_HOUSING` | int (0/1) | |
| `ERROR_LEAKAGE_OIL_HOUSING` | int (0/1) | |
| `ERROR_TEMPERATURE` | int (0/1) | |
| `ERROR_TEMP_MAIN_BEARING` | int (0/1) | |
| `ERROR_TEMP_SUPPORT_BEARING` | int (0/1) | |
| `ERROR_TEMP_STATOR_WINDING_1/2/3` | int (0/1) | |
| `ERROR_LOW_LEVEL_WATER` | int (0/1) | |
| `ERROR_HIGH_LEVEL_WATER` | int (0/1) | |
| `ERROR_PHASE` | int (0/1) | |
| `ERROR_OVERLOAD` | int (0/1) | |
| `ERROR_EMERGENCY` | int (0/1) | |
| `ERROR_VIBRATION` | int (0/1) | |
| `ERROR_EARTH_LEAKAGE` | int (0/1) | |
| `ERROR_BUZZER` | int (0/1) | |

#### WATER_GATE
| Field | Type |
|---|---|
| `SENSOR_DOOR_LEVEL` | float (mm), 2dp |
| `SENSOR_CURRENT` | float (A), 2dp |
| `SENSOR_VOLTAGE` | float (V), 2dp |
| `STATUS_FULLY_OPEN` | int (0/1) |
| `STATUS_FULLY_CLOSE` | int (0/1) |
| `STATUS_GATE_ON` | int (0/1) |
| `FLOW_RATE` | float, 3dp |
| `GATE_WIDTH` | int (cm) |
| `GATE_HEIGHT` | int (cm) |
| `GATE_SILL_ELEVATION` | int (cm) |
| `SELECTOR` | string |
| `MODE` | string |
| `ERROR_EARTH_LEAKAGE` | int (0/1) |
| `ERROR_TORQUE` | int (0/1) |
| `ERROR_OVERLOAD` | int (0/1) |
| `ERROR_EMERGENCY` | int (0/1) |

#### MOBILE_PUMP / WATER_PROPULSION
| Field | Type |
|---|---|
| `STATUS_PUMP_ON` | int (0/1) |
| `SELECTOR` | string |
| `TURN_OFF` | int |
| `SENSOR_TEMP_ENGINE` | int (°C) |
| `SENSOR_TEMP_WATER_COOLANT` | int (°C) |
| `SENSOR_ENGINE_SPEED` | int (RPM) |
| `SENSOR_OIL_PRESSURE` | int (bar) |
| `SENSOR_BATTERY_VOLTAGE` | float (V), 2dp |
| `SENSOR_FUEL_LEVEL` | float (%), 1dp |
| `GPS_LATITUDE` | float |
| `GPS_LONGITUDE` | float |

#### MEASUREMENT_DEVICE / WATER_LEVEL
```json
{
  "station": "cpybtl001",
  "measurement": "MEASUREMENT_DEVICE",
  "type": "WATER_LEVEL",
  "timestamp": 1714000000000,
  "CPYBTL001-001-WATERLEVEL_SENSOR_WATER_LEVEL": 1.23
}
```
All water-level sensors for a station are bundled into a single MQTT message.

#### MEASUREMENT_DEVICE / RAINFALL
```json
{
  "station": "stationId",
  "measurement": "MEASUREMENT_DEVICE",
  "type": "RAINFALL",
  "timestamp": 1714000000000,
  "STATIONID-001-RAINFALL_SENSOR_RAINFALL": 12.5
}
```

#### MEASUREMENT_DEVICE / WATER_QUALITY
```json
{
  "station": "stationId",
  "measurement": "MEASUREMENT_DEVICE",
  "type": "WATER_QUALITY",
  "timestamp": 1714000000000,
  "STATIONID-001-WATERQUALITY_SENSOR_PH": 7.2,
  "STATIONID-001-WATERQUALITY_SENSOR_DO": 6.1
}
```

#### TRASH_SCREEN / TRASH_CONVEYOR
| Field | Type |
|---|---|
| `SENSOR_CURRENT` | float (A), 2dp |
| `SENSOR_VOLTAGE` | float (V), 2dp |
| `TIME_MIN` | int |
| `TIME_HOUR` | int |
| `STATUS_SCREEN_ON` / `STATUS_CONVEYOR_ON` | int (0/1) |
| `SELECTOR` | string |
| `MODE` | string |
| `ERROR_EARTH_LEAKAGE` | int (0/1) |
| `ERROR_OVERLOAD` | int (0/1) |
| `ERROR_EMERGENCY` | int (0/1) |
| `ERROR_TORQUE` | int (0/1) |

### 2.3 `data_command` payload (inbound command)

```json
{
  "status": "CREATED",
  "id": "uuid-v4",
  "serial": "STATION888-001-PROPULSION",
  "stationCode": "station888",
  "measurement": "PROPULSION",
  "timestamp": 1714000000000,
  "switch_on": 1
}
```

- `serial` format: `{STATIONCODE}-{COMMU_ID}` (upper-case)
- `switch_on`: `1` = on, `0` = off
- Published to: `data_command/{stationCode}/{measurement}` (lower-case)

### 2.4 `data_ack` payload (outbound ACK)

```json
{
  "id": "uuid-v4",
  "status_command": "KEEPALIVE",
  "serial": "STATION888-001-WATERPUMP",
  "stationCode": "station888",
  "measurement": "WATER_PUMP",
  "timestamp": 1714000000000,
  "switch_on": 1,
  "_debug_execution_id": "exec-abc123"
}
```

`status_command` lifecycle values (in order):
1. `KEEPALIVE` — sent every 3 s while processing
2. `INITIATED` — device acknowledged start
3. `SUCCESS` — command completed
4. `ERROR` — validation or device-busy failure
5. `STATION_NOT_FOUND` — station not in config
6. `DEVICE_NOT_FOUND` — device serial not found
7. `WRONG_COMMAND` — invalid status field (commented out, reserved)

---

## 3. External Integrations

### 3.1 MQTT Brokers

| Name (mqtt_target) | Host | Port | Protocol | Auth | Notes |
|---|---|---|---|---|---|
| `dev-cluster` | `dev.rpro.digitalsmart.city` | 1883 | MQTT v4 | none | Primary dev target |
| `test-cluster` | (same routing as dev-cluster) | 1883 | MQTT v4 | — | Alias in broker routing |
| `staging-cluster` | (same routing as dev-cluster) | 1883 | MQTT v4 | — | Alias in broker routing |
| `dds-cluster` | `dds.rpro.digitalsmart.city` | 1883 | MQTT v4 | none | DDS deployment |
| `hdy-cluster` | `dds.rpro.digitalsmart.city` | 1883 | MQTT v4 | none | HDY deployment |
| `rid-cluster` | `iot.rid.go.th` | 1883 | MQTT v4 | none | RID (Royal Irrigation Dept) |
| `swoc-cluster` | `dds.rpro.digitalsmart.city` | 1883 | MQTT v4 | none | SWOC deployment |

Broker routing is determined at publish time from `station.mqtt_targets[]` in `managed_config.json`. Each station declares which clusters it publishes to. The "Publish to MQTT Server" function node splits messages into 5 output arrays (dev, dds, hdy, rid, swoc).

### 3.2 FTP (CCTV snapshots)

Used by `cctv-simulator` only. FTP target config per CCTV device:

```json
{
  "host": "${FTP_HOST}",
  "port": 21,
  "username": "devftp",
  "password": "${FTP_PASSWORD}",
  "remote_path": "/",
  "passive_mode": true
}
```

- Environment variables `FTP_HOST`, `FTP_PORT`, `FTP_PASSWORD` are injected at runtime.
- Username is derived: `{mqtt_target_without_-cluster}ftp` — e.g. `dev-cluster` → `devftp`.
- Upload retries 3 times with 5 s back-off.

### 3.3 Node-RED Admin API (internal)

The Web UI calls Node-RED's REST API to trigger flow reload:

```
POST http://nodered:1880/inject/84ad8867bab8e680
```

Node ID `84ad8867bab8e680` is the "Start Simulation" inject node. This triggers the Device Templates → Stations Configuration initialization chain, which re-reads `managed_config.json` from the shared volume.

### 3.4 CCTV Reload Server (internal)

The CCTV simulator exposes a minimal HTTP server at port 8080:

| Method | Path | Description |
|---|---|---|
| `POST` | `/reload` | Force immediate config reload from `managed_config.json` |
| `GET` | `/health` | Health check — returns `{"status":"ok"}` |

Called by Web UI deploy at `http://cctv-simulator-0-app:8080/reload`. A fallback trigger file `/shared-data/.cctv-reload` is also written; the simulator polls it every 5 s.

### 3.5 Kubernetes log access

`KubernetesLogService` (PHP, internal) reads pod stdout logs for deploy verification. Environment variables:
- `NODERED_POD_NAME` (default: `nodered-0-app`)
- `CCTV_POD_NAME` (default: `cctv-simulator-0-app`)

---

## 4. Web UI HTTP Endpoints (Laravel)

Base URL: `https://admin-{BASE_ENDPOINT_URL}` (production) or `http://localhost:8001` (local Docker)

### 4.1 Web (browser) routes — no auth required at router level

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Redirect → `/stations` |
| `GET` | `/stations` | Station list |
| `GET` | `/stations/create` | Create station form |
| `POST` | `/stations` | Create station |
| `GET` | `/stations/{id}` | Station detail |
| `GET` | `/stations/{id}/edit` | Edit form |
| `PUT` | `/stations/{id}` | Update station |
| `DELETE` | `/stations/{id}` | Delete station + all devices |
| `PATCH` | `/stations/{id}/toggle-enabled` | Toggle station enabled flag |
| `GET` | `/devices` | Device list |
| `GET` | `/devices/create` | Create device form |
| `POST` | `/devices` | Create device |
| `GET` | `/devices/{id}` | Device detail |
| `GET` | `/devices/{id}/edit` | Edit form |
| `PUT` | `/devices/{id}` | Update device |
| `DELETE` | `/devices/{id}` | Delete device |
| `PUT` | `/devices/{device}/sensors/{sensorKey}` | Override a sensor value/range |
| `DELETE` | `/devices/{device}/sensors/{sensorKey}` | Reset sensor override |
| `PATCH` | `/devices/{device}/toggle-offline` | Toggle device offline |
| `PATCH` | `/devices/{device}/sensors/{sensorKey}/toggle-offline` | Toggle single sensor offline |
| `POST` | `/devices/{device}/sensors/{sensorKey}/situations` | Add time-range situation |
| `PUT` | `/devices/{device}/sensors/{sensorKey}/situations/{index}` | Update situation |
| `DELETE` | `/devices/{device}/sensors/{sensorKey}/situations/{index}` | Remove situation |
| `GET` | `/templates` | Template list |
| `GET` | `/templates/{id}` | Template detail |
| `POST` | `/deploy/export` | Export DB → `managed_config.json` |
| `POST` | `/deploy` | Full deploy (export + reload Node-RED + reload CCTV) |
| `POST` | `/deploy/reload` | Reload Node-RED only (no export) |
| `GET` | `/api/search` | Global search across stations/devices |

### 4.2 API v1 routes — requires Sanctum bearer auth (`/api/v1/`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/stations` | List stations |
| `POST` | `/api/v1/stations` | Create station |
| `GET` | `/api/v1/stations/{id}` | Show station (`?include=devices`) |
| `PUT` | `/api/v1/stations/{id}` | Update station |
| `DELETE` | `/api/v1/stations/{id}` | Delete station |
| `GET` | `/api/v1/devices` | List devices |
| `POST` | `/api/v1/devices` | Create device |
| `GET` | `/api/v1/devices/{id}` | Show device |
| `PUT` | `/api/v1/devices/{id}` | Update device |
| `DELETE` | `/api/v1/devices/{id}` | Delete device |
| `GET` | `/api/v1/templates` | List templates |
| `GET` | `/api/v1/templates/{id}` | Show template |
| `POST` | `/api/v1/deploy` | Full deploy |
| `POST` | `/api/v1/deploy/export` | Export only |

#### Station create/update body schema

```json
{
  "station_id": "uuid",
  "station_code": "lowercase-alphanumeric",
  "station_name": "string",
  "area": 10000,
  "runoff": 0.3,
  "rain_to_rise_delay": 15,
  "passive_drainage_rate": 0.05,
  "simulate_mode": true,
  "is_enabled": true,
  "mqtt_targets": ["dev-cluster"]
}
```

#### Deploy response body

```json
{
  "success": true,
  "message": "Deployment completed successfully",
  "logs": ["Step 1: ...", "✓ Exported 20 stations...", "..."]
}
```

---

## 5. Kubernetes CRDs

All CRDs are Traefik v3 custom resources in namespace `default`.

### 5.1 CRD Definitions (`kubernetes-crd-definition-v1.yml`)

| Kind | Group | Description |
|---|---|---|
| `IngressRoute` | `traefik.io/v1alpha1` | HTTP router — defines rules + services + middlewares + TLS |
| (Implicitly referenced) | `traefik.io` | Also covers: `Middleware`, `MiddlewareTCP`, `TraefikService`, `IngressRouteTCP`, `IngressRouteUDP`, `TLSOption`, `TLSStore`, `ServersTransport`, `ServersTransportTCP` |

### 5.2 RBAC (`kubernetes-crd-rbac.yml`)

`ClusterRole: traefik-ingress-controller` grants `get/list/watch` on:
- Core: `services`, `endpoints`, `secrets`
- `networking.k8s.io`: `ingresses`, `ingressclasses` (+ `update` on status)
- `traefik.io`: all Traefik CRD resources listed above

Bound to `ServiceAccount: traefik-ingress-controller` in namespace `default`.

### 5.3 Deployed IngressRoutes

#### Node-RED UI (`nodered-ingressroute.yml`)
- EntryPoint: `nodered` (port 1880)
- Rule: `Host('mqtt-{BASE_ENDPOINT_URL}')`
- Service: `nodered-0-app:1880`
- Middleware: `basic-auth` (htpasswd, default `admin/admin`)

#### Web UI (`web-ui-ingressroute.yml`)
- HTTPS: `Host('admin-{BASE_ENDPOINT_URL}')` → `web-ui-0-app:443`  
  API prefix (`/api/`) bypasses basic-auth; all other paths require it.
- HTTP: `Host('admin-{BASE_ENDPOINT_URL}')` → redirect to HTTPS (301)
- TLS: from secret `tls-secret`
- Backend: uses `ServersTransport: webui-insecure-transport` (skip TLS verify, self-signed)

#### Traefik entrypoints (`edge-0-traefik.yml`)

| Name | Container port | NodePort |
|---|---|---|
| `web` | 80 | 30001 |
| `websecure` | 443 | 30002 |
| `nodered` | 1880 | 30003 |
| `admin` (Traefik dashboard) | 8080 | 30729 |

TLS: min TLS 1.2, ciphers ECDHE-RSA-AES256-GCM-SHA384 / CHACHA20_POLY1305 / TLS 1.3 equivalents, `sniStrict: true`.

---

## 6. Docker Service Network (local dev)

Network name: `simulator-network` (bridge driver).

| Service | Container | Ports (host:container) | Health check |
|---|---|---|---|
| `nodered` | `nodered` | `1880:1880` | `curl http://localhost:1880` |
| `webui` | `web-ui` | `8001:443` | `wget https://localhost:443/health` |
| `cctv-simulator` | `cctv-simulator` | (none external) | (none) |

Shared volume `shared-data` (local driver) is mounted at `/shared-data` in all three containers. This is the single-file IPC bus:

| File | Producer | Consumer |
|---|---|---|
| `/shared-data/managed_config.json` | Web UI deploy | Node-RED (on reload), CCTV simulator |
| `/shared-data/.cctv-reload` | Web UI deploy (fallback) | CCTV simulator (polling every 5 s) |

Internal service URLs (container-to-container):
- Web UI → Node-RED: `http://nodered:1880` (env `NODERED_API_URL`)
- Web UI → CCTV: `http://cctv-simulator:8080/reload` (Docker); `http://cctv-simulator-0-app:8080/reload` (K8s)

---

## 7. Configuration Schema (`managed_config.json`)

### 7.1 Top-level structure

```json
{
  "meta": {
    "version": "1.0",
    "exported_at": "ISO-8601",
    "exported_by": "string"
  },
  "device_templates": { "<TEMPLATE_ID>": { ... } },
  "stations": { "<STATION_CODE>": { ... } }
}
```

### 7.2 Device template schema

```json
{
  "template_id": "WATER_PUMP_v1",
  "template_name": "Water Pump v1",
  "device_type": null,
  "measurement": "WATER_PUMP",
  "type": null,
  "version": 1,
  "sensors": {
    "<SENSOR_KEY>": {
      "initial_value": 0,
      "min": 0,
      "max": 100
    }
  }
}
```

For `CCTV_v1` template, additional fields exist:
```json
{
  "snapshot_interval_minutes": 1,
  "background_image": "default",
  "ftp_defaults": { "host": "", "port": 21, "password": "", "passive_mode": true },
  "ftp_targets": []
}
```

### 7.3 Station schema

```json
{
  "station_id": "uuid",
  "station_code": "buengfarang",
  "station_name": "Station Display Name",
  "enabled": true,
  "simulate_mode": true,
  "area": 10000,
  "runoff": 0.3,
  "rain_to_rise_delay": 15,
  "passive_drainage_rate": 0.05,
  "mqtt_targets": ["dev-cluster"],
  "devices": [ { ... } ]
}
```

### 7.4 Device schema (within station)

```json
{
  "template": "WATER_GATE_v1",
  "id": "uuid",
  "commu_id": "001-WATERGATE",
  "device_name": "Water Gate 1",
  "offline": false,
  "offline_sensors": ["SENSOR_CURRENT"],
  "override_sensors": {
    "<SENSOR_KEY>": {
      "initial_value": 0,
      "min": 0,
      "max": 500,
      "rate_per_hour": 0.2,
      "situation": [
        { "from": "07:00", "to": "11:00", "case": "down" }
      ]
    }
  },
  "bias_factor": 0.15
}
```

For CCTV devices, additional override fields:
```json
{
  "snapshot_interval_minutes": 2,
  "background_image": "canal_bg.jpg",
  "ftp_targets": [
    { "host": "ftp.example.com", "port": 21, "username": "devftp",
      "password": "${FTP_PASSWORD}", "remote_path": "/", "passive_mode": true }
  ]
}
```

### 7.5 Sensor situation `case` values

Used by WATER_LEVEL and RAINFALL nodes for time-based behavior:
- `up` — value increases during time window
- `down` — value decreases
- `stable` — minimal variation

### 7.6 Known template IDs

| Template ID | Measurement | MQTT topic suffix |
|---|---|---|
| `WATER_GATE_v1` | `WATER_GATE` | `.../water_gate` |
| `WATER_PUMP_v1` | `WATER_PUMP` | `.../water_pump` |
| `MOBILE_PUMP_v1` | `MOBILE_PUMP` | `.../mobile_pump` |
| `WATER_LEVEL_SENSOR_v1` | `MEASUREMENT_DEVICE` / `WATER_LEVEL` | `.../measurement_device/water_level` |
| `WATER_QUALITY_SENSOR_v1` | `MEASUREMENT_DEVICE` / `WATER_QUALITY` | `.../measurement_device/water_quality` |
| `RAINFALL_SENSOR_v1` | `MEASUREMENT_DEVICE` / `RAINFALL` | `.../measurement_device/rainfall` |
| `TRASH_SCREEN_v1` | `TRASH_SCREEN` | `.../trash_screen` |
| `TRASH_CONVEYOR_v1` | `TRASH_CONVEYOR` | `.../trash_conveyor` |
| `WATER_PROPULSION_v1` | `PROPULSION` | `.../propulsion` |
| `CCTV_v1` | `CCTV` | (FTP only, no MQTT) |

---

## 8. CCTV Simulator Output

### 8.1 Image generation

The CCTV simulator produces JPEG snapshots, not MQTT messages. Pipeline per camera thread:

1. Load a background image from `/app/backgrounds/` (random pick if `background_image = "default"`, otherwise named file)
2. Overlay a semi-transparent black bar at ~6% from top containing:
   - Line 1 left: `device_name`
   - Line 1 right: `YYYY-MM-DD  HH:MM:SS` (local time, Asia/Bangkok)
   - Line 2: `device_id` (UUID)
3. Save as JPEG to `/tmp/cctv-output/`

### 8.2 Output filename format

```
{device_id}_{YYYYMMDDHHMMSSmmm}_API.jpg
```

Example: `f76e6c72-d1fd-4eb4-aca6-7ad606b655a1_20260426174500123_API.jpg`

### 8.3 FTP upload and lifecycle

- Each CCTV device runs in its own daemon thread (`Camera-{commu_id}`)
- Upload interval: `snapshot_interval_minutes * 60` seconds (default 1 min)
- On success: local file is deleted after upload
- On partial failure (one FTP target failed): local file is retained
- Stale local files (> 1 hour old) are cleaned up every ~60 s

### 8.4 Downstream FTP consumers

The FTP server receives files at `{remote_path}/{device_id}_{timestamp}_API.jpg`. Downstream systems poll or receive these files from the FTP server. The file naming convention (`_API.jpg` suffix) is understood by consuming systems that display CCTV images in dashboards.

### 8.5 Config reload mechanism

| Trigger | Source |
|---|---|
| `POST /reload` to port 8080 | Web UI deploy action (primary) |
| Trigger file `/shared-data/.cctv-reload` | Web UI deploy action (fallback) |
| `SIGHUP` signal | Manual / orchestrator |

On reload, camera threads are reconciled: new devices gain threads, removed devices stop, unchanged devices keep running.

---

## 9. Node-RED Flow Architecture Summary

The single flow tab ("Simulator flow") is organized into named groups:

| Group | Function |
|---|---|
| `Initial device template/station configuration` | Startup: loads `managed_config.json` into `flow._device_templates` and `flow._stations` |
| `To INITIAL "Global Utilities function"` | Registers helper functions in `global` context (clamp, randomValue, calculatePumpFlow, etc.) |
| `Recive "data_command" & Return "data_ack"` | Subscribes `data_command/+/+`, routes to per-measurement command handlers, publishes ACKs |
| `SIMULATE REALISTIC data_stream/xxx/xxx` | Inject timer → split stations/devices → per-type simulate functions → MQTT publish |
| `SIMULATE FIXED data_stream/xxx/xxx` | Same topology but returns sensor values as-is (testing mode) |
| `Separate machine/device type` | Switch node routing by `measurement` type to correct simulator function |
| `Pushlish payload to MQTT Server` | Splits messages by broker name and routes to 5 MQTT out nodes |
| `Publish "data_command"` | Manual inject for testing command payloads |
| `To CLEAR "Flow Context Data"` | Maintenance: null / delete flow context |

### Command handling state machine (per device)

```
Receive data_command
        ↓
  Duplicate check (command registry, 7-day TTL)
        ↓ new
  Device busy check (FIFO — one in-progress command at a time)
        ↓ idle
  Register as in-progress
        ↓
  Send KEEPALIVE every 3s × N
        ↓
  Send INITIATED
        ↓
  Send KEEPALIVE every 3s × M
        ↓
  Execute (toggle switch_on, trigger data_stream publish)
        ↓
  Send SUCCESS (or ERROR / STATION_NOT_FOUND / DEVICE_NOT_FOUND)
        ↓
  Mark completed in registry
```

Commandable device types: `WATER_PUMP`, `WATER_GATE`, `TRASH_SCREEN`, `TRASH_CONVEYOR`, `WATER_PROPULSION`.
