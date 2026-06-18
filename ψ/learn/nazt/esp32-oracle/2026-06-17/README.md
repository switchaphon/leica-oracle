# ESP32 Oracle — API Surface & Integration Reference

**Compiled**: 2026-06-17 @ 06:39 UTC  
**Source snapshot**: `/tmp/esp32-source/esp32-stale-copy-20260617/`  
**Status**: Stale reference (current as of 2026-05-31)

---

## Document Index

### 📋 [0639_API-SURFACE.md](./0639_API-SURFACE.md)
**Complete API reference** — Authoritative specification of all integration points.

**Contents**:
- WASM exported functions (gif-wasm: `gif_open`, `gif_play`, `gif_fb`, `gif_close`, etc.)
- React `EmscriptenSim` component API & lifecycle
- HTTP endpoints (`/api/ls`, `/api/capture`)
- Pet simulator state machine & snapshot format
- Terminal simulator contract (`createOracleTerm`)
- sim-gallery 8-section structure
- ESPHome fleet-pulse device integration
- Character pack manifest format
- Extension points for new simulators, packs, hardware

**For**: Implementers, architects, integration engineers  
**Size**: 710 lines | **Read time**: 20–30 min

---

### ⚡ [0640_QUICK-REFERENCE.md](./0640_QUICK-REFERENCE.md)
**One-page cheat sheet** — Constants, APIs, commands, troubleshooting.

**Contents**:
- WASM function signatures (condensed)
- HTTP API endpoints (quick table)
- React component syntax
- Pet state machine (computeDesired)
- Character pack structure
- Build commands
- File paths (key sources)
- Constants (REACT_MS, STALE_MS, etc.)
- Extension checklist
- Known issues & workarounds

**For**: Developers, debugging, quick lookups  
**Size**: 258 lines | **Read time**: 5–10 min

---

### 🏗️ [0641_ARCHITECTURE.md](./0641_ARCHITECTURE.md)
**System architecture & data flows** — Detailed diagrams, interaction sequences, extension recipes.

**Contents**:
- System overview (browser ↔ backend layers)
- Pet heartbeat data flow (rAF loop, state transitions)
- ESPHome HTTP poll sequence (5s interval, JSON parsing, LVGL render)
- WASM module lifecycle (Emscripten MODULARIZE)
- Character pack discovery & loading
- Add new simulator (step-by-step)
- Add new character pack (step-by-step)
- CORS considerations & workarounds
- Deployment & CI/CD
- Troubleshooting map

**For**: DevOps, system designers, debugging  
**Size**: 483 lines | **Read time**: 15–20 min

---

## Quick Navigation

### I want to…

**Implement a new feature**
1. Read [0639_API-SURFACE.md](./0639_API-SURFACE.md) § corresponding to your layer (WASM, React, HTTP, ESPHome)
2. Check [0640_QUICK-REFERENCE.md](./0640_QUICK-REFERENCE.md) for syntax & constants
3. Follow extension recipe in [0641_ARCHITECTURE.md](./0641_ARCHITECTURE.md)

**Debug a bug**
1. Consult [0640_QUICK-REFERENCE.md](./0640_QUICK-REFERENCE.md) § "Known Issues & Workarounds"
2. Check data flow diagrams in [0641_ARCHITECTURE.md](./0641_ARCHITECTURE.md)
3. Ref full API in [0639_API-SURFACE.md](./0639_API-SURFACE.md) for details

**Understand the system**
1. Start with overview in [0641_ARCHITECTURE.md](./0641_ARCHITECTURE.md) § "System Overview"
2. Follow data flows for your area of interest
3. Drill into [0639_API-SURFACE.md](./0639_API-SURFACE.md) for specifics

**Add a new simulator / pack / hardware**
→ [0641_ARCHITECTURE.md](./0641_ARCHITECTURE.md) § "Extension: Adding…"

**Quick lookup (syntax, constants, commands)**
→ [0640_QUICK-REFERENCE.md](./0640_QUICK-REFERENCE.md)

---

## System Layers

### Browser (React + Vite)
**File**: `lab/sim-gallery/`  
**Role**: Host WASM simulators + pet state machine + gallery UI

**Key API**:
- `EmscriptenSim` (React component) — mount WASM modules
- `PetSim` (React component) — pure JS pet state machine
- Pet `petLogic.ts` — state machine logic
- Gallery sections — 8 different simulators

**Refs**: [0639 §2](./0639_API-SURFACE.md#2-react-emscripten-simulator-component), [0639 §4](./0639_API-SURFACE.md#4-pet-simulator-state-machine), [0639 §6](./0639_API-SURFACE.md#6-react-pet-simulator-component)

### WASM (Emscripten)
**Files**: `lab/gif-wasm/`, `lab/jc3248-pet/sim/`, `lab/esp32-fleet-pulse-esphome/sim/`  
**Role**: Decode GIFs, render LVGL UIs on virtual canvas

**Key API**:
- `gif_open()`, `gif_play()`, `gif_fb()`, `gif_close()` — GIF decoder
- `createOracleTerm({ canvas, print, printErr })` — terminal simulator
- `PetSim`, `OracleFaceV1`, `OracleFaceV2` — UI simulators

**Refs**: [0639 §1](./0639_API-SURFACE.md#1-wasm-exported-functions-gif-wasm), [0639 §5](./0639_API-SURFACE.md#5-terminal-simulator-createoracleterm)

### HTTP Backend (maw)
**Role**: Serve session list & pane captures to devices & browsers

**Endpoints**:
- `GET /api/ls` → JSON (sessions + windows)
- `GET /api/capture?target=<s:w>` → JSON (ANSI text)

**Refs**: [0639 §3](./0639_API-SURFACE.md#3-http-apis-maw-backend), [0640](./0640_QUICK-REFERENCE.md#http-apis)

### ESPHome Device (ESP32 + display)
**File**: `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml`  
**Role**: Poll HTTP API every 5s, render session list on LVGL

**Hardware**: ESP32-S3 + AXS15231 QSPI 320×480 + LEDC backlight  
**Flow**: HTTP GET → JSON parse → LVGL label update

**Refs**: [0639 §8](./0639_API-SURFACE.md#8-esphome-integration-fleet-pulse), [0641](./0641_ARCHITECTURE.md#data-flow-esphome-http-poll)

### Firmware (ESP-IDF)
**File**: `lab/jc3248-pet/src/pet.cpp` (+ other device projects)  
**Role**: Pet state machine, GIF decoder, LVGL UI, BLE link

**Not documented in detail here** (firmware only); reference for web/sim equivalents.

---

## Key Types & Data Structures

### Pet Snapshot (heartbeat)
```typescript
{
  total: number,           // total agents/tasks
  running: number,         // running now
  waiting: number,         // awaiting approval (→ attention state)
  msg: string,             // status message
  tokens: number,          // API tokens used (5h window)
  pct5h: number,           // usage % (5h) | -1 = absent
  reset5h: number,         // seconds until reset | -1 = absent
  pct7d: number,           // usage % (7d) | -1 = absent
  reset7d: number,         // seconds until reset | -1 = absent
  name?: string            // pet name (optional)
}
```

**State computation**:
```
if (!link.connected) → idle
if (stale > 30s) → idle
if (waiting > 0) → attention
if (running > 0) → busy
if (total == 0) → sleep
else → idle
```

### Character Pack (manifest.json)
```json
{
  "name": "<pack>",
  "colors": { "bg": "#000000", "text": "#FFFFFF", "textDim": "#808080" },
  "states": {
    "idle": ["idle_0.gif", "idle_1.gif"],
    "busy": "busy.gif",
    "attention": "attention.gif",
    "sleep": "sleep.gif",
    "heart": "heart.gif"
  }
}
```

### /api/ls Response
```json
{
  "node": "<node-name>",
  "oracle": "<oracle-name>",
  "sessions": [
    {
      "name": "<session-name>",
      "windows": [
        { "name": "<window-name>", "active": true/false },
        ...
      ]
    },
    ...
  ]
}
```

---

## Build Commands

```bash
# Gallery (React + Vite)
cd lab/sim-gallery
npm install
npm run dev                  # dev server :5173
npm run build-sims          # compile all LVGL+WASM sims
npm run build               # bundle for prod
npm run deploy              # Cloudflare Workers

# GIF WASM
cd lab/gif-wasm
make                        # both WASI + WASM
make web                    # browser only
make run-web               # dev server :8011

# Terminal simulator
cd lab/esp32-fleet-pulse-esphome/sim
bash scripts/build-wasm-module.sh
# → dist-module/oracle_term_sim.{js,wasm}
```

---

## Key Files & Paths

| File | Purpose |
|------|---------|
| `lab/gif-wasm/src/gifcore.h` | GIF decoder API (C) |
| `lab/gif-wasm/web/gifdec.js` | WASM module (Emscripten) |
| `lab/sim-gallery/src/components/EmscriptenSim.tsx` | WASM mount component (React) |
| `lab/sim-gallery/src/sims/pet/petLogic.ts` | Pet state machine logic |
| `lab/sim-gallery/src/routes/Gallery.tsx` | 8-section gallery app |
| `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml` | ESPHome HTTP poll + LVGL render |
| `lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md` | Terminal simulator contract |
| `lab/jc3248-pet/data/characters/bufo/manifest.json` | Pet pack structure |
| `lab/jc3248-pet/src/pet.cpp` | Firmware pet logic (reference) |

---

## Common Questions

**Q: How do I add a new pet pack?**  
A: Create `data/characters/<name>/manifest.json` + `.gif` files. No code change. See [0641](./0641_ARCHITECTURE.md) § "Extension: Adding a New Character Pack".

**Q: How do I render a GIF in the browser?**  
A: Use `GifModule._gif_open()` + `_gif_play()` + `_gif_fb()`. Example in [0641](./0641_ARCHITECTURE.md) § "Integration Examples".

**Q: Why does `/api/ls` fail in the browser?**  
A: CORS + RFC1918 + HTTPS mixed-content. Solution: proxy through HTTPS domain or use local dev. See [0641](./0641_ARCHITECTURE.md) § "CORS Considerations".

**Q: What's the pet state machine?**  
A: `computeDesired(link, snap, now)` in [0639 §4](./0639_API-SURFACE.md#4-pet-simulator-state-machine). Returns state based on link + snapshot.

**Q: How do I add a new simulator?**  
A: Build with Emscripten (`-sMODULARIZE`), add React section in Gallery. Steps in [0641](./0641_ARCHITECTURE.md) § "Extension: Adding a New Simulator".

**Q: What's the ESPHome integration?**  
A: `fleet-pulse.yaml` polls `/api/ls` every 5s, parses JSON, renders session list in LVGL. See [0639 §8](./0639_API-SURFACE.md#8-esphome-integration-fleet-pulse).

---

## Document Provenance

**Source**: `/tmp/esp32-source/esp32-stale-copy-20260617/` (stale snapshot from 2026-05-31)

**Explored**:
- `lab/gif-wasm/` — GIF decoder C API + WASM build
- `lab/sim-gallery/` — React gallery app + simulators
- `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml` — ESPHome config + HTTP poll
- `lab/esp32-fleet-pulse-esphome/sim/` — Terminal simulator + integration guide
- `lab/jc3248-pet/` — Pet firmware logic + character packs
- Various simulator directories (oracle-v1, oracle-v2, term, buddy, etc.)

**Snapshot date**: 2026-05-31 onwards (based on blog posts, inbox entries, commits)

**Limitations**:
- No oracle-app or oracle-app-tauri source found (may be in separate repos)
- Snapshot is stale; active development may have changed APIs
- No full firmware source (ESP-IDF level) documented here

---

## Related Learning Resources

**From nazt team**:
- [../README.md](../../README.md) — Parent learning directory
- [../../nazt.md](../../nazt.md) — Team context & projects

**From codebase**:
- `lab/gif-wasm/README.md` — GIF decoder details
- `lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md` — Terminal simulator contract
- Blog posts in `blog/` — Hardware adventures, debugging logs

**External docs**:
- [Emscripten](https://emscripten.org/) — WASM compilation, MODULARIZE
- [ESPHome](https://esphome.io/) — HTTP client, LVGL, JSON parsing
- [LVGL](https://docs.lvgl.io/) — UI library
- [AnimatedGIF](https://github.com/bitbank2/AnimatedGIF) — GIF decoder (Apache-2.0)

---

**Compiled by**: Leica Oracle  
**For**: nazt ESP32 team (Un)  
**Updated**: 2026-06-17 06:39 UTC
