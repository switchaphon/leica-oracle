# CODE-SNIPPETS: nodered-simulator

**Source:** `/Users/switchaphon/_RPRO_/internal-server/nodered-simulator`
**Version:** 4.35.1
**Date:** 2026-04-26

---

## Overview

An IoT simulation platform built on Node-RED. It simulates a water-management infrastructure — pumps, gates, water levels, rainfall, trash screens, mobile pumps, and CCTV cameras — and publishes sensor data over MQTT. The system is divided into:

- `functions/` — Node-RED function node JS files (synced into `flows/flows.json` via `scripts/sync-functions.js`)
- `cctv-simulator/` — Standalone Python service generating fake CCTV snapshots uploaded via FTP
- `edge/` — Kubernetes/Traefik ingress YAML files (infra config only, no logic)
- `scripts/` — Tooling for syncing JS into Node-RED flow JSON, testing, watching

---

## 1. Main Entry / Bootstrap

### `settings.js` — Node-RED runtime configuration

The key customisation is injecting Node's `fs` module into the global function context so function nodes can read config files from disk.

```js
// settings.js
functionGlobalContext: {
    fs: require('fs'),
},
functionExternalModules: true,
functionTimeout: 0,
uiPort: process.env.PORT || 1880,
mqttReconnectTime: 15000,
```

---

### `scripts/sync-functions.js` — Developer workflow: sync JS files into flows.json

This script is the primary dev tool. Each JS file embeds a `Node ID:` comment header. The script reads `function-mapping.json`, extracts the Node ID from each file, finds the matching node in `flows/flows.json`, and replaces its `func` property.

```js
// scripts/sync-functions.js
function extractNodeIdFromFile(content) {
    const match = content.match(/\* Node ID: ([a-f0-9]+)/);
    return match ? match[1] : null;
}

function extractFunctionCode(content) {
    // Remove the header comment block (/** ... */)
    const withoutHeader = content.replace(/^\/\*\*[\s\S]*?\*\/\s*\n/, '');
    return withoutHeader.trimEnd();
}

function syncFunctions() {
    const flow = JSON.parse(fs.readFileSync(FLOW_FILE, 'utf8'));
    const mapping = JSON.parse(fs.readFileSync(MAPPING_FILE, 'utf8'));

    for (const [filename, metadata] of Object.entries(mapping)) {
        const jsContent = fs.readFileSync(jsFilePath, 'utf8');
        const nodeId = extractNodeIdFromFile(jsContent);
        const functionCode = extractFunctionCode(jsContent);
        const nodeIndex = flow.findIndex(node => node.id === nodeId);
        flow[nodeIndex].func = functionCode;
    }

    fs.writeFileSync(FLOW_FILE, JSON.stringify(flow, null, 4), 'utf8');
}
```

---

## 2. Configuration Loading

### `functions/devices-template.js` — Load device templates at tick time

Loads device templates from the shared Docker/K8s volume config file. Uses a content-signature comparison to bump `_config_version` only when templates actually change (prevents spurious sensor resets every tick).

```js
// functions/devices-template.js
const CONFIG_PATHS = [
    '/shared-data/managed_config.json',
    '/data/config/managed_config.json'
];

// Default fallback templates — used on fresh deployments
const DEFAULT_TEMPLATES = {
  WATER_GATE_v1: { measurement: "WATER_GATE", sensors: {
      SENSOR_CURRENT: { initial_value: 0, min: 20, max: 190 },
      SENSOR_DOOR_LEVEL: { initial_value: 0, min: 0, max: 500 },
      GATE_WIDTH: { initial_value: 200 }, // cm
      GATE_HEIGHT: { initial_value: 500 }, // cm
      // ... more sensors
  }},
  WATER_PUMP_v1: { measurement: "WATER_PUMP", sensors: { /* ... */ }},
  MOBILE_PUMP_v1: { measurement: "MOBILE_PUMP", sensors: { /* ... */ }},
  WATER_LEVEL_SENSOR_v1: { measurement: "MEASUREMENT_DEVICE", type: "WATER_LEVEL",
      sensors: { SENSOR_WATER_LEVEL: { position: "inside", min: -1, max: 1, rate_per_hour: 0.2 }}},
  RAINFALL_SENSOR_v1: { /* ... */ },
  WATER_QUALITY_SENSOR_v1: { /* ... */ },
};

// Signature-based change detection — prevents sensor reset every tick
const currentSignature = JSON.stringify(device_templates);
const prevSignature = flow.get("_device_templates_signature");
if (prevSignature === undefined || currentSignature !== prevSignature) {
    flow.set("_config_version", Date.now());
}
flow.set("_device_templates_signature", currentSignature);
flow.set("_device_templates", device_templates);
```

---

### `functions/stations-configuration.js` — Load station config with hybrid fallback

Priority order: shared Docker volume → alternative mount → local project path → bundled default. Separates user data from developer logic so user edits survive code updates.

```js
// functions/stations-configuration.js
const CONFIG_PATHS = [
    '/shared-data/managed_config.json',           // K8s/Docker persistent
    '/data/config/managed_config.json',
    'config/managed_config.json',                 // Local dev
    '/data/config/managed_config.default.json'    // Day 0 fallback
];

// Signature check: only bump _config_version when stations actually changed
const currentSignature = JSON.stringify(stations);
const prevSignature = flow.get("_stations_signature");

// updated_at injection happens AFTER signature to avoid timestamp noise
for (const stationId in stations) {
    if (!stations[stationId].updated_at) {
        stations[stationId].updated_at = Date.now();
    }
}

flow.set("_stations", stations);
if (prevSignature === undefined) {
    flow.set("_config_version", Date.now());
} else if (currentSignature !== prevSignature) {
    flow.set("_config_version", Date.now());
}
flow.set("_stations_signature", currentSignature);
```

---

## 3. Global Utility Functions

### `functions/global-utilities-function.js` — Shared physics helpers registered in global context

All simulation nodes pull these from `global.get("sim_*")`. Includes math helpers, hydraulic flow calculations, and water level physics.

```js
// functions/global-utilities-function.js

// Clamp and random
global.set("sim_clamp", (v, min, max) => Math.min(Math.max(v, min), max));
global.set("sim_randomValue", (min, max) => Math.random() * (max - min) + min);

// Sensor value with config-version-aware reset
// Returns initial_value when _config_version changed since last seen, else persists previous value
global.set("sim_getSensorValue", function (ctxPrefix, flow, device, template, sensorKey) {
    const override = device.override_sensors?.[sensorKey];
    const tmplSensor = template.sensors?.[sensorKey];
    const currentInitialValue = override?.initial_value ?? tmplSensor?.initial_value;

    const configVersion = flow.get("_config_version") ?? 0;
    const seenVersion   = flow.get(ctxPrefix + `${sensorKey}_configVersionSeen`) ?? -1;

    if (configVersion !== seenVersion) {
        flow.set(ctxPrefix + `${sensorKey}_configVersionSeen`, configVersion);
        flow.set(ctxPrefix + sensorKey, currentInitialValue);
        return currentInitialValue;
    }
    return flow.get(ctxPrefix + sensorKey) ?? currentInitialValue;
});

// Adds sensor to MQTT payload only if not in offline_sensors list
global.set("sim_addSensorValueToPayload", function (data, stationPrefix, commuId, sensorKey, value, offlineSensors = []) {
    if (!Array.isArray(offlineSensors) || !offlineSensors.includes(sensorKey)) {
        data[`${stationPrefix}-${commuId}_${sensorKey}`] = value;
    }
});

// Gate flow: Q = Cd * A * sqrt(2g * deltaH)
global.set("sim_calculateGateFlow", ({ width, height, doorLevel, upstreamLevel, downstreamLevel }) => {
    const DISCHARGE_COEFFICIENT = 0.6;
    const GRAVITY = 9.81;
    const headDiff = Math.max(0, upstreamLevel - downstreamLevel);
    const openArea = width * height * (doorLevel / 100);
    const flowRate = DISCHARGE_COEFFICIENT * openArea * Math.sqrt(2 * GRAVITY * headDiff);
    return Math.max(0, flowRate);
});

// Pump flow: zero when off, nominal * efficiency when on
global.set("sim_calculatePumpFlow", ({ nominalFlow, pumpStatus, efficiency = 1 }) => {
    if (pumpStatus !== 1) return 0;
    return nominalFlow * efficiency;
});

// Rainfall volume conversion: mm/hr + runoff + area -> m³ per timestep
global.set("sim_calculateRainfallEffect", ({ rainfallRate, runoff, timeStep, area }) => {
    const volumePerHour = (rainfallRate * runoff * area) / 1000;
    return (volumePerHour / 3600) * timeStep;
});

// Water level change with incoming/outgoing volumes and natural drainage
global.set("sim_calculateWaterLevelChange", ({
    currentLevel, incomingVolume, outgoingVolume, position,
    passiveDrainageRate, timeStep, area
}) => {
    const NATURAL_DRAINAGE_FACTOR = 0.0001;
    if (position === "inside") {
        const levelChange = (incomingVolume - outgoingVolume) / area;
        const naturalDrainage = outgoingVolume === 0 ? currentLevel * NATURAL_DRAINAGE_FACTOR : 0;
        return { newLevel: Math.max(0, currentLevel + levelChange - naturalDrainage), details: { /* ... */ } };
    } else {
        // downstream: passive drainage only
        const passiveDrainageChange = (passiveDrainageRate * timeStep) / area;
        return { newLevel: Math.max(0, currentLevel - passiveDrainageChange), details: { /* ... */ } };
    }
});
```

---

## 4. Message Routing: Split Stations to Device Groups

### `functions/split-stations-devices-data.js` — Fan-out: one message per measurement type per station

Reads `_stations` and `_device_templates` from flow context. Groups devices by `measurement|type|simulate_mode` key. Each group becomes one outgoing message so downstream nodes receive exactly the devices they care about.

```js
// functions/split-stations-devices-data.js
const deviceTemplates = flow.get("_device_templates");
const stations = flow.get("_stations");

for (const stationId in stations) {
  const station = stations[stationId];
  if (station.enabled === false) continue;

  const deviceGroups = {};

  for (const d of station.devices || []) {
    if (d.offline) continue;

    const template = deviceTemplates[d.template] || {};
    const measurement = template.measurement || "UNKNOWN";
    const effectiveMode = (d.simulate_mode ?? station.simulate_mode ?? 1) ? 1 : 0;
    const key = `${measurement}|${template.type || "null"}|${effectiveMode}`;

    // Merge template sensors with per-device overrides
    const overridedSensors = {};
    for (const sensorKey in template.sensors || {}) {
      if (Array.isArray(d.offline_sensors) && d.offline_sensors.includes(sensorKey)) continue;
      overridedSensors[sensorKey] = { ...template.sensors[sensorKey], ...(d.override_sensors?.[sensorKey] || {}) };
    }

    deviceGroups[key] = deviceGroups[key] || { measurement, type: template.type, devices: {} };
    deviceGroups[key].devices[d.commu_id] = { id: d.id, template: d.template, override_sensors: overridedSensors };
  }

  for (const key in deviceGroups) {
    // Each group becomes a separate node.send([msgs]) call
    node.send([stationOut]); // fans out one msg per group
  }
}
```

---

## 5. Sensor Simulation Nodes

### `functions/simulate-water-gate.js` — Simulates gate door movement and flow

Implements incremental door position movement toward a target level, gate fully-open/close status, flow-rate physics, and electrical sensor simulation (current, voltage).

```js
// functions/simulate-water-gate.js (key excerpt)
const clamp = global.get("sim_clamp");
const calculateGateFlow = global.get("sim_calculateGateFlow");

for (const commuId in devices) {
    const ctxPrefix = `prev_${stationPrefix}-${commuId}_`;

    let sensorDoorLevel = getSensorValue(ctxPrefix, flow, device, template, "SENSOR_DOOR_LEVEL");
    const targetDoorLevel = flow.get(ctxPrefix + "SENSOR_TARGET_DOOR_LEVEL") ?? sensorDoorLevel;
    const step = clamp(randomValue(10, 20), 10, 20);
    const tolerance = 1;

    if (Math.abs(targetDoorLevel - lastDoorLevel) > tolerance) {
        if (targetDoorLevel > lastDoorLevel) {
            sensorDoorLevel = Math.min(lastDoorLevel + step, targetDoorLevel);
            statusGateOn = 1; // opening
        } else {
            sensorDoorLevel = Math.max(lastDoorLevel - step, targetDoorLevel);
            statusGateOn = 2; // closing
        }
        // Simulate electrical load during movement
        sensorCurrent = clamp(sensorCurrent + randomValue(-0.2, 0.2), currentMin, currentMax);
        sensorVoltage = clamp(sensorVoltage + randomValue(-1.0, 1.0), voltageMin, voltageMax);
    } else {
        statusGateOn = 0;
        sensorCurrent = Math.max(currentMin, sensorCurrent - 10.1);
    }

    // Hydraulic flow rate from upstream/downstream water levels
    const flowRate = calculateGateFlow({
        width: gateWidth / 100, height: gateHeight / 100,
        doorLevel: (sensorDoorLevel / gateHeight) * 100,
        upstreamLevel: flow.get(`prev_${stationPrefix}-WATERLEVEL_UPSTREAM`),
        downstreamLevel: flow.get(`prev_${stationPrefix}-WATERLEVEL_DOWNSTREAM`)
    });

    flow.set(ctxPrefix + "SENSOR_DOOR_LEVEL", sensorDoorLevel);
    flow.set(ctxPrefix + "FLOW_RATE", flowRate);
    addSensorValueToPayload(data, stationPrefix, commuId, "SENSOR_DOOR_LEVEL", parseFloat(sensorDoorLevel.toFixed(2)), offlineSensors);
    addSensorValueToPayload(data, stationPrefix, commuId, "FLOW_RATE", parseFloat(flowRate.toFixed(3)), offlineSensors);
}
```

---

### `functions/simulate-water-pump.js` — Pump on/off with thermal and vibration model

When pump is ON: current/voltage ramp up, temperatures rise with operating-time factor, vibration modeled. When OFF: all values decay toward minimums. Auto-generates errors when thresholds are exceeded.

```js
// functions/simulate-water-pump.js (key excerpt)
const operatingTime = (timestamp - (flow.get(ctxPrefix + "start_time") || timestamp)) / 1000;
const tempIncreaseFactor = Math.min(1, operatingTime / 3600); // Max effect after 1 hour

if (statusPump === 1) {
    sensorCurrent = clamp(sensorCurrent + randomValue(-1, 15), currentMin, currentMax);
    sensorPower = (sensorCurrent * sensorVoltage) / 1000 + randomValue(-0.5, 0.5);
    tempMainBearing = clamp(tempMainBearing + randomValue(-0.5, 0.5) * tempIncreaseFactor, tMin, tMax);

    // Auto-trigger error conditions
    if (sensorCurrent > sensorCurrentMax * 1.1) errorOverload = 1;
    if (tempMainBearing > tempMainBearingMax * 1.1) errorTempMainBearing = 1;
    if (sensorVibration > sensorVibrationMax * 1.1) errorVibration = 1;

} else {
    // Cooling: linear decay toward min values
    if (sensorCurrent > sensorCurrentMin) sensorCurrent = Math.max(sensorCurrentMin, sensorCurrent - randomValue(1, 5));
    if (tempMainBearing > tempMainBearingMin) tempMainBearing = Math.max(tempMainBearingMin, tempMainBearing - randomValue(1, 5));
    errorOverload = 0; errorPhase = 0; errorVibration = 0; // reset when off
}

// Efficiency based on hydraulic head difference
const headDiff = Math.max(0, upstreamLevel - downstreamLevel);
const efficiency = Math.min(1, (headDiff / nominalHead) * 0.9);
const flowRate = calculatePumpFlow({ nominalFlow, pumpStatus: statusPump, efficiency });
```

---

### `functions/simulate-rainfall.js` — Accumulation with time-based reset

Rainfall accumulates every 15-second tick. Every minute it resets and reports the accumulated mm value. Also maintains a rolling 1-hour history used by the water level calculator.

```js
// functions/simulate-rainfall.js (key excerpt)
const increment = (usedRate / 3600) * 15; // 15 second tick
accumulated += increment;

// Reset every 60 seconds and report
if (!lastReset || (timestamp - lastReset) >= 60000) {
    value = parseFloat(accumulated.toFixed(4));
    accumulated = 0;
    lastReset = timestamp;
    isReset = true;
} else {
    value = parseFloat(accumulated.toFixed(4));
}

// Maintain 1-hour rolling history for delayed rainfall effect on water level
rainHistory = manageRainfallHistory({
    history: rainHistory,
    station_id,
    currentRate: usedRate,
    timestamp
});

// Output: two message arrays — MQTT messages AND raw rainfallData for calculate-water-level
return [messages, rainfallData];
```

---

### `functions/simulate-water-level.js` — Water level with position, bias, and noise

Each sensor can be `position: "inside"` (rises with rain/pump inflow) or `outside` (passive drainage). Applies a small random noise term plus a station bias that pulls the value back toward its initial setting.

```js
// functions/simulate-water-level.js (key excerpt)
const { newLevel, details } = calculateWaterLevelChange({
    currentLevel,
    incomingVolume: 0, // filled in by calculate-water-level.js after rainfall/gate/pump data arrive
    outgoingVolume: 0,
    position,
    passiveDrainageRate: passive_drainage_rate || 0.05,
    timeStep: TIME_STEP, // 15 seconds
    area: stationArea
});

// Small random noise
const noise = (Math.random() - 0.5) * 0.005;
// Bias: pull toward initial_value, scaled by bias_factor (default 0.1)
const bias = (stationInitial - currentLevel) * stationBias;
let finalLevel = clamp(newLevel + noise + bias, min, max);

// Store upstream/downstream reference for gate/pump calculations
if (position === "inside") flow.set(upstreamKey, finalLevel);
else flow.set(downstreamKey, finalLevel);
```

---

### `functions/simulate-mobile-pump.js` — Mobile pump with fuel consumption and GPS

Extends the base pump model with fuel/battery depletion, engine temperature/speed, oil pressure, and GPS coordinates. Includes a `TURN_OFF` state that zeroes all readings.

```js
// functions/simulate-mobile-pump.js (key excerpt)
if (statusPump === 1) {
    fuelLevel = Math.max(0, fuelLevel - randomValue(0.05, 0.1));    // gradual consumption
    batteryLevel = Math.max(0, batteryLevel - randomValue(0.02, 0.05));
    tempEngine = clamp(tempEngine + randomValue(-2, 20), tempEngineMin, tempEngineMax);
    engineSpeed = clamp(engineSpeed + randomValue(-10, 300), engineSpeedMin, engineSpeedMax);
    if (fuelLevel < 5) errorFuel = 1;
} else {
    // Passive refuel when pump is off (e.g. operator refills tank)
    const FUEL_REFILL_PER_INTERVAL = 15;
    fuelLevel = Math.min(fuelLevelMax, fuelLevel + FUEL_REFILL_PER_INTERVAL);
    if (tempEngine > 0) tempEngine = Math.max(0, tempEngine - randomValue(3, 5));
}

// TURN_OFF: hard-zero all operational readings
if (statusTurnoff === 1 && prevTurnoff === 0) {
    tempCoolant = tempEngine = engineSpeed = oilPressure = statusPump = 0;
    batteryVoltage = batteryLevel = 0;
    statusSelector = 'STOP';
}
```

---

### `functions/simulate-trash-screen.js` — Screen motor with operating-time counters

Accumulates `TIME_MIN` and `TIME_HOUR` while the screen is running. Simulates current/voltage ramp up during operation and triggers `errorOverload` when current exceeds 95% of max.

```js
// functions/simulate-trash-screen.js (key excerpt)
if (statusScreenOn === 1) {
    sensorCurrent = clamp(sensorCurrent + randomValue(-1, 15), currentMin, currentMax);
    sensorVoltage = clamp(sensorVoltage + randomValue(-1, 15), voltageMin, voltageMax);

    const elapsedSeconds = (timestamp - (flow.get(ctxPrefix + "last_time_update") || timestamp)) / 1000;
    timeMin += elapsedSeconds / 60;
    if (timeMin >= 60) { timeHour += Math.floor(timeMin / 60); timeMin = timeMin % 60; }

    if (sensorCurrent > sensorCurrentMax * 0.95) errorOverload = 1;
} else {
    // Decay and reset
    sensorCurrent = Math.max(currentMin, sensorCurrent - randomValue(1, 5));
    errorOverload = 0;
}
```

---

## 6. Water Level Calculation (Aggregation Node)

### `functions/calculate-water-level.js` — Final water level combining rain + gates + pumps

This node runs after rainfall, gate, and pump simulation nodes have stored their data in flow context. It aggregates all contributing factors and produces the final MQTT water level payload.

```js
// functions/calculate-water-level.js (key excerpt)
// Deduplication: skip if already executed this tick
const executionId = `calc_water_level_${timestamp}_${execCounter}`;
if (flow.get("_last_water_level_calc") === executionId) return null;
flow.set("_last_water_level_calc", executionId);

for (const stationData of waterLevelData) {
    let incomingVolume = 0, outgoingVolume = 0;

    if (position === "inside") {
        // Rainfall volume (with configurable delay)
        const stationRainfall = validRainfallData.find(r => r.station_id === station_id);
        if (station_params.rain_delay === 0 || delayedRain) {
            const effectiveRate = delayedRain ? delayedRain.rate : stationRainfall.rainfall_rate;
            incomingVolume += calculateRainfallEffect({ rainfallRate: effectiveRate, runoff, timeStep: TIME_STEP, area });
        }

        // Gate drainage
        Object.values(stationDevices.gates || {}).forEach(gate => {
            const gateFlow = calculateGateFlow({ ...gate, upstreamLevel: water_level });
            outgoingVolume += gateFlow * TIME_STEP;
        });

        // Pump drainage (fixed + mobile)
        ['pumps', 'mobilePumps'].forEach(pumpType => {
            Object.values(stationDevices[pumpType] || {}).forEach(pump => {
                outgoingVolume += calculatePumpFlow(pump) * TIME_STEP;
            });
        });
    }

    const { newLevel } = calculateWaterLevelChange({ currentLevel: water_level, incomingVolume, outgoingVolume, ... });

    // Output key: STATION_ID-COMMU_ID_SENSOR_WATER_LEVEL
    addSensorValueToPayload(stationGroups[station_id], station_id.toUpperCase(), commu_id, "SENSOR_WATER_LEVEL", newLevel, []);
}
```

---

## 7. Command Handling

### `functions/parse-command.js` — Topic parsing into message metadata

Incoming MQTT command topics follow the pattern `data_command/{stationCode}/{measurement}`. This node splits the topic and attaches the components to the message.

```js
// functions/parse-command.js
const parts = msg.topic.split("/");
msg.stationCode = parts[1];
msg.measurement = parts[2];
msg.commands = msg.payload;
return msg;
```

---

### `functions/build-data-command-payload.js` — Construct test command messages

Used in testing flows to inject commands. Generates a UUID, builds a command object, and sets the MQTT topic.

```js
// functions/build-data-command-payload.js
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

const command = {
    status: 'CREATED',
    id: generateUUID(),
    serial: 'STATION888-001-WATERPUMP',
    stationCode: 'station888',
    measurement: 'WATER_PUMP',
    timestamp: Date.now(),
    switch_on: 1
};
msg.topic = `data_command/${command.stationCode.toLowerCase()}/${command.measurement.toLowerCase()}`;
msg.payload = [command];
```

---

### `functions/command-water-gate.js` — Full gate command lifecycle with phased ACKs

This is the most complex handler. It implements a multi-phase command lifecycle: KEEPALIVE spam → INITIATED → ACKNOWLEDGE loop (incremental gate movement) → SUCCESS/ABORT/ERROR/INTERRUPT/TIMEOUT. Supports abort, FIFO device-busy rejection, and injected failure modes (MODE = ERROR1/ERROR2/ERROR3/INTERRUPT1-3/TIMEOUT1-3).

Key design: all state changes happen via `setTimeout`; the main function body pre-computes all timer schedules synchronously and exits, relying on closures.

```js
// functions/command-water-gate.js (key patterns)

// ===== DUPLICATE DETECTION (MQTT retained messages / concurrent duplicates) =====
const isCommandProcessed = global.get("cmd_isCommandProcessed");
if (isCommandProcessed && isCommandProcessed(flow, node, msg.payload.id, msg.payload.serial)) {
    return null; // Silent ignore
}

// ===== FIFO: reject if device already has an in-progress command =====
if (msg.payload.is_abort !== 1) {
    const registry = flow.get('_command_registry') || {};
    for (const cmdId in registry[msg.payload.serial] || {}) {
        if (!registry[msg.payload.serial][cmdId].completedTime) {
            sendAck('ERROR', 0, executionId); // "Device busy"
            return null;
        }
    }
}

// ===== ACKNOWLEDGE loop: simulate gate moving in 10-20cm steps =====
let currentDoorLevel = flow.get(ctxPrefix + "_SENSOR_DOOR_LEVEL") || 0;
while (Math.abs(targetDoorLevel - currentDoorLevel) > tolerance && iterationCount < maxIterations) {
    const step = Math.floor(Math.random() * 11) + 10;
    const nextDoorLevel = targetDoorLevel > currentDoorLevel
        ? Math.min(currentDoorLevel + step, targetDoorLevel)
        : Math.max(currentDoorLevel - step, targetDoorLevel);

    // Check interruption at a random point within the 3s iteration window
    const randomCheckDelay = Math.floor(Math.random() * 3001);
    const checkTimerId = setTimeout(() => {
        const currentMode = flow.get(ctxPrefix + "_MODE") || 'NORMAL';
        if (currentMode === 'ABORTED') {
            wasInterrupted = true;
            flow.set(ctxPrefix + "_SENSOR_DOOR_LEVEL", previousDoorLevel); // gate stops at previous pos
            clearTimeout(/* all pending timers */);
            sendAck('ABORT', 2000, executionId);
            return;
        }
        // Similar blocks for ERROR3, INTERRUPT3, TIMEOUT3...
    }, delayForThisIteration + randomCheckDelay);

    scheduledTimers.push(checkTimerId);
    currentDoorLevel = nextDoorLevel;
    currentDelay += 3000;
    iterationCount++;
}

// ===== After loop: send SUCCESS and trigger data_stream publish =====
setTimeout(() => {
    if (wasInterrupted) return;
    flow.set(ctxPrefix + "_STATUS_GATE_ON", 0);
    triggerDataStreamPublish(stationCode, serial, measurement, 1000, executionId);
    setTimeout(() => sendAck('SUCCESS', 0, executionId), 2000);
}, currentDelay + 3000);

return null; // Node-RED function returns immediately; all work is in timers
```

**`triggerDataStreamPublish`** — forces the simulation node to re-publish current sensor state for the affected device only:

```js
function triggerDataStreamPublish(stationId, serial, measurement, delayMs, execId) {
    const simulateMode = deviceConfig.simulate_mode ?? stationConfig.simulate_mode ?? true;
    setTimeout(() => {
        node.send([null, triggerMsg]); // Output 2: trigger sim node
    }, delayMs);
}
```

**`sendAck`** — reads gate state at send-time (not at schedule-time) and publishes to `data_ack/{stationCode}/{measurement}`:

```js
function sendAck(status, delayMs, execId) {
    const createAck = () => ({
        id: msg.payload.id,
        status_command: status,
        serial: msg.payload.serial,
        timestamp: Date.now(),           // captured at send time
        sensor_door_level: flow.get(ctxPrefix + "_SENSOR_DOOR_LEVEL"),
        status_fully_open: flow.get(ctxPrefix + "_STATUS_FULLY_OPEN"),
    });

    if (isFinal) {
        const completeCommandRegistry = global.get("cmd_completeCommandRegistry");
        completeCommandRegistry(flow, node, msg.payload.id, msg.payload.serial, status);
    }
    setTimeout(() => node.send([{ topic: `data_ack/...`, payload: createAck() }, null]), delayMs);
}
```

---

## 8. Command Registry

### `functions/command-registry-helper.js` — Global functions for duplicate prevention and FIFO

Registers three functions into global context. Commands are kept for 7 days after completion (to reject MQTT retained message replays). Only completed commands are ever purged.

```js
// functions/command-registry-helper.js
const COMMAND_REGISTRY_TTL = 7 * 24 * 60 * 60 * 1000; // 7 days

// Check: is command already known (in-progress OR completed)?
global.set("cmd_isCommandProcessed", function(flow, node, commandId, serial) {
    const registry = flow.get('_command_registry') || {};
    return !!(registry[serial] && registry[serial][commandId]);
});

// Register: mark command as in-progress
global.set("cmd_addCommandRegistry", function(flow, node, commandId, serial, execId) {
    registry[serial][commandId] = {
        executionId: execId,
        startTime: Date.now(),
        completedTime: null,
        finalStatus: null
    };
    flow.set('_command_registry', registry);
});

// Complete: mark with final status, keep entry for TTL (never delete immediately)
global.set("cmd_completeCommandRegistry", function(flow, node, commandId, serial, finalStatus) {
    registry[serial][commandId].completedTime = Date.now();
    registry[serial][commandId].finalStatus = finalStatus;
    flow.set('_command_registry', registry);
});

// Cleanup: remove completed entries older than TTL (run periodically)
global.set("cmd_cleanupExpiredCommands", function(flow, node) {
    for (const serial in registry) {
        for (const commandId in registry[serial]) {
            const entry = registry[serial][commandId];
            if (entry.completedTime && (now - entry.completedTime > COMMAND_REGISTRY_TTL)) {
                delete registry[serial][commandId];
                cleanedCount++;
            }
        }
        if (Object.keys(registry[serial]).length === 0) delete registry[serial];
    }
    flow.set('_command_registry', registry);
});
```

---

## 9. MQTT Routing

### `functions/publish-to-mqtt-server.js` — Fan-out by broker cluster

Receives a batched array of MQTT messages, groups them by `mqtt_target` string, and outputs five separate arrays — one per broker cluster — on separate Node-RED outputs.

```js
// functions/publish-to-mqtt-server.js
const messagesByBroker = {};
msg.payload.forEach(m => {
    const stationId = m.payload.station;
    const config = stations[stationId];
    config.mqtt_targets.forEach(broker => {
        messagesByBroker[broker] = messagesByBroker[broker] || [];
        messagesByBroker[broker].push({ topic: m.topic, payload: m.payload });
    });
});

// Output 1: dev/test/staging | Output 2: dds-cluster | ... | Output 5: swoc-cluster
msg.dev  = messagesByBroker["dev-cluster"] || messagesByBroker["test-cluster"] || [];
msg.dds  = messagesByBroker["dds-cluster"] || [];
msg.hdy  = messagesByBroker["hdy-cluster"] || [];
msg.rid  = messagesByBroker["rid-cluster"] || [];
msg.swoc = messagesByBroker["swoc-cluster"] || [];
return [msg.dev, msg.dds, msg.hdy, msg.rid, msg.swoc];
```

---

## 10. Flow Context Management

### `functions/manage-flow-context.js` — Targeted flow context reset by station/device/sensor

Supports three match cases and two actions (delete or set_null). Used to reset sensor state when a device is rebooted or test scenarios are reset. Uses RegExp for safe station-name matching.

```js
// functions/manage-flow-context.js
const flowKeys = flow.keys();
const regex = new RegExp(`(^|[^a-zA-Z0-9])${stationCode}([^a-zA-Z0-9]|$)`);

// Case 1: all keys for a station
const keys = flowKeys.filter(k => regex.test(k));

// Case 2: station + commuId prefix
const keys = flowKeys.filter(k => k.startsWith(`prev_${stationCode}-${commuId}_`));

// Case 3: exact sensor key or prefix
const exactKey = `prev_${stationCode}-${commuId}_${sensorKey}`;
const prefixKey = `prev_${stationCode}-${commuId}_${sensorKey}_`;

matchedKeys.forEach(key => {
    if (action === "delete")      flow.set(key, undefined);
    else if (action === "set_null") flow.set(key, null);
    else if (action === "reset_error") flow.set(key, 0);
});
```

---

## 11. Simulate Mode Resolution

### `functions/lib/resolveSimulateMode.js` — Single source of truth for simulate_mode

Pure function used by tests; command handlers inline the same expression verbatim (Node-RED function nodes cannot `require()` user files).

```js
// functions/lib/resolveSimulateMode.js
function resolveSimulateMode(deviceConfig, stationConfig) {
  return (deviceConfig?.simulate_mode ?? stationConfig?.simulate_mode ?? true);
}
module.exports = { resolveSimulateMode };
```

---

## 12. CCTV Simulator (Python)

### `cctv-simulator/main.py` — Entry point: signal handling, reload loop, stale file cleanup

Waits for the config file to exist (handles deploy race), starts `CameraManager`, starts an HTTP reload server, then runs a poll loop checking for a trigger file and performing periodic cleanup.

```python
# cctv-simulator/main.py (key patterns)
config_path = os.environ.get("CONFIG_PATH", "/shared-data/managed_config.json")
trigger_file = os.environ.get("TRIGGER_FILE", "/shared-data/.cctv-reload")

# Block until config file appears (deploy race condition)
while not os.path.exists(config_path):
    logger.warning("Config file not found: %s — retrying in %ds", config_path, retry_interval)
    time.sleep(retry_interval)

manager = CameraManager(config_path, output_dir, backgrounds_dir)
manager.start()
reload_server = ReloadServer(manager, port=reload_server_port)
reload_server.start()

# Main loop: check trigger file + SIGHUP every 5s, cleanup stale files every 60s
while not shutdown:
    time.sleep(trigger_check_interval)
    if os.path.exists(trigger_file):
        os.remove(trigger_file)
        manager.force_reload()

def cleanup_stale_files(output_dir, max_age_seconds=3600):
    for filename in os.listdir(output_dir):
        if os.path.getmtime(filepath) < now - max_age_seconds:
            os.remove(filepath)
```

---

### `cctv-simulator/config.py` — Parse managed_config.json and extract CCTV device configs

Merges template defaults with per-device overrides. Resolves `${ENV_VAR}` patterns in FTP target fields. Skips disabled stations and offline devices.

```python
# cctv-simulator/config.py
@dataclass
class CameraConfig:
    device_id: str
    station_id: str
    commu_id: str
    interval_seconds: float
    background_image: str
    ftp_targets: list
    is_offline: bool = False

def merge_template_with_device(template, device, station_id) -> CameraConfig:
    # Device values override template defaults
    interval_min = device.get('snapshot_interval_minutes', template.get('snapshot_interval_minutes', 1))
    ftp_targets = device.get('ftp_targets', template.get('ftp_targets', []))
    background  = device.get('background_image', template.get('background_image', 'default'))
    return CameraConfig(device_id=device['id'], interval_seconds=interval_min * 60, ...)

def _resolve_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} with env values — used for FTP credentials."""
    return re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), ''), value)

def extract_cctv_devices(config) -> list:
    """Only CCTV_v1 template, enabled station, non-offline, non-empty ftp_targets."""
    for station_id, station in config.get('stations', {}).items():
        if station.get('enabled') is False: continue
        for device in station.get('devices', []):
            if device.get('template') != 'CCTV_v1': continue
            if device.get('offline', False): continue
            cam = merge_template_with_device(cctv_template, device, station_id)
            if not cam.ftp_targets: continue  # skip unconfigured cameras
            cameras.append(cam)
```

---

### `cctv-simulator/camera.py` — CameraThread and CameraManager with hot-reload

One `threading.Thread` per camera. `CameraManager` diffs the old vs new config on reload and stops/starts only changed or removed cameras.

```python
# cctv-simulator/camera.py
class CameraThread(threading.Thread):
    def run(self):
        while not self._stop_event.is_set():
            self._capture_and_upload()
            self._stop_event.wait(timeout=self.config.interval_seconds)

    def _capture_and_upload(self):
        bg_path = resolve_background(self.config.background_image, self.backgrounds_dir)
        filename = generate_filename(self.config.device_id)
        local_path = os.path.join(self.output_dir, filename)
        create_image(bg_path, local_path, device_name=..., device_id=...)
        for target in self.config.ftp_targets:
            upload_to_ftp(local_path, filename, target)
        os.remove(local_path)  # cleanup after successful upload

class CameraManager:
    def _load_and_apply(self):
        new_cameras = extract_cctv_devices(load_config(self.config_path))
        # Diff: stop cameras that no longer exist or whose config changed
        for device_id, thread in self._cameras.items():
            if device_id not in new_ids or self._config_changed(thread.config, new_configs.get(device_id)):
                thread.stop(); thread.join(timeout=10); to_remove.append(device_id)
        # Start new cameras
        for cam_config in new_cameras:
            if cam_config.device_id not in self._cameras:
                thread = CameraThread(cam_config, self.output_dir, self.backgrounds_dir)
                thread.start()
                self._cameras[cam_config.device_id] = thread

    @staticmethod
    def _config_changed(old, new) -> bool:
        return (new is None or old.interval_seconds != new.interval_seconds
                or old.background_image != new.background_image
                or len(old.ftp_targets) != len(new.ftp_targets)
                or any(o.host != n.host for o, n in zip(old.ftp_targets, new.ftp_targets)))
```

---

### `cctv-simulator/image_generator.py` — Overlay CCTV-style header bar onto background image

Pillow-based image generator. Composites a semi-transparent black bar with device name, date/time, and device UUID onto a background photo. Filename format is `{device_uuid}_{YYYYMMDDHHMMSSmmm}_API.jpg`.

```python
# cctv-simulator/image_generator.py
def create_image(background_path, output_path, *, device_name='', device_id=''):
    img = Image.open(background_path).convert('RGB')
    font_size = max(12, img.size[0] // 40)  # proportional to image width

    # Black semi-transparent overlay bar at 6% from top
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, bar_y, width, bar_y + bar_height], fill=(0, 0, 0, 160))

    # Line 1: device_name (left) + datetime (right)
    draw.text((padding_x, text_y), device_name, fill='white', font=font_bold)
    draw.text((width - padding_x - right_w, text_y), datetime_str, fill='white', font=font_bold)
    # Line 2: device_id UUID
    draw.text((padding_x, text_y), device_id, fill='white', font=font_small)

    Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB').save(output_path, 'JPEG')

def generate_filename(device_id):
    ms = datetime.datetime.now().strftime("%f")[:3]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ms
    return f"{device_id}_{timestamp}_API.jpg"
```

---

### `cctv-simulator/ftp_uploader.py` — FTP upload with recursive dir creation and retry

Uses stdlib `ftplib`. Navigates/creates the remote directory path recursively. Retries 3 times with 5-second delays.

```python
# cctv-simulator/ftp_uploader.py
def _ensure_remote_dir(ftp, path):
    for d in path.strip('/').split('/'):
        try:
            ftp.cwd(d)
        except ftplib.error_perm:
            ftp.mkd(d); ftp.cwd(d)

def upload_to_ftp(local_path, remote_filename, target, retries=3):
    for attempt in range(1, retries + 1):
        try:
            ftp = ftplib.FTP()
            ftp.connect(target.host, target.port, timeout=30)
            ftp.login(target.username, target.password)
            ftp.set_pasv(target.passive_mode)
            _ensure_remote_dir(ftp, target.remote_path)
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_filename}', f)
            ftp.quit()
            return True
        except ftplib.all_errors as e:
            if attempt < retries: time.sleep(5)
    raise FtpUploadError(f"Failed after {retries} attempts: {last_error}")
```

---

## Key Patterns Summary

| Pattern | Where | Notes |
|---------|-------|-------|
| Content-signature versioning | `devices-template.js`, `stations-configuration.js` | Prevents sensor reset on every tick |
| Global function registry | `global-utilities-function.js`, `command-registry-helper.js` | Node-RED function nodes share logic via `global.get()` |
| Sensor value with config version | `sim_getSensorValue` | Returns `initial_value` only when `_config_version` changed |
| Flow context key naming | All sim nodes | Pattern: `prev_{STATION}-{COMMU_ID}_{SENSOR_KEY}` |
| Fan-out by measurement type | `split-stations-devices-data.js` | Groups devices by `measurement|type|simulate_mode`, one msg per group |
| Multi-broker MQTT routing | `publish-to-mqtt-server.js` | 5 output ports, one per cluster |
| Phased ACK lifecycle | `command-water-gate.js` | KEEPALIVE → INITIATED → ACKNOWLEDGE → SUCCESS/ABORT/ERROR/INTERRUPT/TIMEOUT |
| FIFO device-busy rejection | `command-water-gate.js` | Only one in-progress command per device serial at a time |
| 7-day command TTL | `command-registry-helper.js` | Rejects MQTT retained message replays |
| Offline sensors filtering | All sim nodes | `addSensorValueToPayload` skips keys in `offline_sensors[]` |
| Hot-reload via trigger file | `cctv-simulator/main.py` | Polls `/shared-data/.cctv-reload`; also supports SIGHUP and HTTP POST /reload |
