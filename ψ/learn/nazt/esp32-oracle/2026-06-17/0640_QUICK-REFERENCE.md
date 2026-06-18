# ESP32 Oracle — Quick Reference Card

## WASM Exports (gif-wasm)

```c
int gif_open(const uint8_t *data, int len);     // Load GIF from buffer
int gif_width(void) / gif_height(void);         // Get canvas size
int gif_play(int *delay_ms);                    // Decode next frame (ret: 1=more, 0=last, -1=err)
const uint8_t *gif_fb(void);                    // Get RGBA8888 canvas (write to <canvas>)
void gif_reset(void);                           // Seek to frame 0 (loop)
void gif_close(void);                           // Cleanup
```

**Browser call**: `Module._gif_open(ptr, len)`, `Module._gif_fb()` → `Module.HEAPU8` heap view

---

## HTTP APIs

| Endpoint | Use | Response |
|----------|-----|----------|
| `GET /api/ls` | Poll session list | JSON: sessions + windows + active flags |
| `GET /api/capture?target=<s:w>` | Get pane content | JSON: `{content: "ANSI text"}` |

**Requires**: CORS headers or proxy (RFC1918 RFC + HTTPS mixed-content caveat)

---

## React Component: EmscriptenSim

```tsx
<EmscriptenSim
  src="/path/to/factory.js"      // Emscripten MODULARIZE output
  factory="FactoryName"          // globalThis[factory]
  width={320} height={480}       // Canvas dimensions
  onReady={(mod) => {...}}       // Optional callback
/>
```

**Features**: Lazy-load, visibility-gated CPU pause, 404→"not built" card, cleanup on unmount

---

## Pet State Machine

```typescript
type PetState = 'idle' | 'busy' | 'attention' | 'sleep' | 'heart'

interface Snapshot {
  total, running, waiting: number
  msg: string
  tokens: number
  pct5h, reset5h, pct7d, reset7d: number  // usage windows (-1 = absent)
}

function computeDesired(link, snap, now): PetState {
  if (!link.connected) return 'idle'
  if (now - link.lastSnap > 30000) return 'idle'  // stale
  if (snap.waiting > 0) return 'attention'
  if (snap.running > 0) return 'busy'
  if (snap.total === 0) return 'sleep'
  return 'idle'
}
```

---

## Character Pack (manifest.json)

```json
{
  "name": "bufo",
  "colors": {
    "bg": "#000000",
    "text": "#FFFFFF",
    "textDim": "#808080"
  },
  "states": {
    "idle": ["idle_0.gif", "idle_1.gif"],
    "busy": "busy.gif",
    "attention": "attention.gif",
    "sleep": "sleep.gif",
    "heart": "heart.gif"
  }
}
```

**Location**: `data/characters/<pack-name>/manifest.json`  
**Extension**: Add new packs by creating new dirs + manifest + `.gif` files (no code change)

---

## Terminal Simulator (createOracleTerm)

```javascript
const Module = await globalThis.createOracleTerm({
  canvas: canvasEl,
  locateFile: (p) => baseUrl + '/' + p,  // for .wasm
  print: console.log,
  printErr: console.warn
});

// Call C exports:
Module.ccall('term_set_header', null, ['string'], ['header text']);
Module.ccall('term_set_content', null, ['string'], ['ANSI text']);
```

**Fonts**: Baked into `.wasm` (no preload files needed)  
**Canvas**: 320×480  
**LVGL**: v9.5.0 (matches device)

---

## sim-gallery Sections

| # | ID | Type | Canvas | Notes |
|---|----|----|--------|-------|
| 01 | bufo | React | 320×480 | Pure JS pet state machine |
| 02 | wasm | iframe | — | gif-wasm demo (index.html) |
| 03 | pet-lvgl | WASM | 320×620 | Pet + HUD (Emscripten) |
| 04 | oracle-v1 | WASM | 320×480 | Skeleton oracle UI |
| 05 | oracle-v2 | WASM | 320×480 | 10-card grid |
| 06 | term | WASM | 320×480 | Fleet terminal (baked fonts) |
| 07 | term-live | iframe | — | Live terminal (poll `/api/capture`) |
| 08 | flash | iframe | — | esp-web-tools flasher |

**Navigation**: Anchor links `#<section-id>` (no nested routes)  
**Build**: `npm run dev` (dev) / `npm run build` (prod) / `npm run build-sims` (compile WASM)

---

## ESPHome fleet-pulse.yaml

```yaml
http_request:
  id: http_client
  timeout: 12s
  verify_ssl: false
  buffer_size_rx: 1024

interval:
  - interval: 5s
    then:
      - http_request.get:
          url: http://192.168.1.109:3456/api/ls  # ← customize IP:port
          capture_response: true
          max_response_buffer_size: 8192          # ← must be >= /api/ls response size
```

**Hardware**: ESP32-S3 + AXS15231 QSPI 320×480 + LEDC backlight  
**Output**: LVGL labels (header + 16 session rows)

---

## Build Commands

```bash
# Gallery app (React + Vite)
cd lab/sim-gallery
npm install
npm run dev                  # dev server :5173
npm run build-sims          # compile all WASM sims (Makefile)
npm run build               # bundle for production
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

## File Paths (Key)

```
lab/gif-wasm/src/gifcore.{h,cpp}
lab/gif-wasm/web/gifdec.js
lab/sim-gallery/src/components/EmscriptenSim.tsx
lab/sim-gallery/src/sims/pet/petLogic.ts
lab/sim-gallery/src/routes/Gallery.tsx
lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml
lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md
lab/jc3248-pet/data/characters/bufo/manifest.json
```

---

## Constants (pet-sim)

```typescript
const PACK = 'bufo'                  // active pack name
const BASE = `/data/characters/bufo` // manifest + GIF location
const REACT_MS = 4000                // tap → heart reaction duration
const STALE_MS = 30000               // link timeout
const IDLE_DWELL_MS = 3000           // idle animation rotation interval
const W = 320, H = 480, HUD_H = 80   // canvas + HUD size
```

---

## Extension Checklist

### Add a new character pack
- [ ] Create `data/characters/<pack>/manifest.json`
- [ ] Add `.gif` files for each state
- [ ] Done (no code change)

### Add a new simulator
- [ ] Build with `emcc ... -sMODULARIZE=1 -sEXPORT_NAME=YourName`
- [ ] Add section in `Gallery.tsx`
- [ ] Mount with `<EmscriptenSim factory="YourName" ... />`

### Add a new hardware / display
- [ ] Create ESPHome `.yaml` config
- [ ] Build matching WASM simulator
- [ ] Add section in gallery

### Add new pet states/reactions
- [ ] Add `.gif` file to pack
- [ ] Update `manifest.json`
- [ ] If firmware-driven, update `pet.cpp` state enum
- [ ] Done (manifest-driven approach avoids code changes)

---

## Known Issues & Workarounds

| Issue | Cause | Fix |
|-------|-------|-----|
| CORS 404 on `/api/ls` | RFC1918 + HTTPS mixed-content | Proxy maw through HTTPS domain or use local dev |
| ESPHome JSON truncated | `max_response_buffer_size` too small | Set to ≥8192 for `/api/ls` |
| WASM "not built" card | Simulator src 404 or not compiled | Run `npm run build-sims` in gallery dir |
| 0-byte `.data` file with `-sMODULARIZE` | Emscripten + `--preload-file` bug | Don't use `--preload-file`; bake assets (like terminal fonts) into .wasm |
| GIF decode fails (OOM) | Large canvas + many frames | Use incremental decode (like gif-wasm does) |

---

## Quick Links

- **Stale snapshot source**: `/tmp/esp32-source/esp32-stale-copy-20260617/`
- **GIF decoder**: `lab/gif-wasm/src/gifcore.h` (C API)
- **React mount**: `lab/sim-gallery/src/components/EmscriptenSim.tsx`
- **State machine**: `lab/sim-gallery/src/sims/pet/petLogic.ts`
- **Gallery routes**: `lab/sim-gallery/src/routes/Gallery.tsx`
- **Terminal contract**: `lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md`
- **ESPHome**: `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml`
- **Pet pack example**: `lab/jc3248-pet/data/characters/bufo/manifest.json`

---

*Last updated: 2026-06-17*
