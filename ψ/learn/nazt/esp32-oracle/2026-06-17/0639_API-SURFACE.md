# ESP32 Oracle — API Surface Map

**Date**: 2026-06-17  
**Status**: Stale snapshot (2026-05-31 onwards)  
**Source**: `/tmp/esp32-source/esp32-stale-copy-20260617/`

## Overview

The ESP32 Oracle system is a polyglot stack:
- **Firmware layer** (ESP-IDF): Pet state machine + LVGL UI on AXS15231 QSPI displays
- **WASM layer** (Emscripten + WASI): GIF decoder + simulators (pet, oracle-face, terminal)
- **Browser layer** (React): sim-gallery gallery app mounting WASM modules + polling HTTP APIs
- **Backend layer** (maw + ESPHome): HTTP JSON APIs (maw `/api/ls`, `/api/capture`)

---

## 1. WASM Exported Functions (gif-wasm)

**File**: `lab/gif-wasm/src/gifcore.h` (C linkage) → `lab/gif-wasm/web/gifdec.js` (Emscripten export)

### API

```c
// Copy len bytes of GIF data, open it, allocate + clear the RGBA canvas.
// Returns 0 on success, <0 on error (bad GIF / OOM). Call gif_close() when done.
int gif_open(const uint8_t *data, int len);

// Get canvas dimensions (0 before successful open).
int gif_width(void);
int gif_height(void);

// Decode the NEXT frame into the canvas. 
// Returns: 1 = more frames follow, 0 = last frame, -1 = error.
// *delay_ms (if non-NULL) = this frame's display duration in ms.
int gif_play(int *delay_ms);

// Pointer to RGBA8888 canvas (width*height*4 bytes), valid until gif_close().
// In the browser build, this is a byte offset into the wasm heap.
const uint8_t *gif_fb(void);

// Seek back to frame 0 (loop the animation).
void gif_reset(void);

// Free the canvas + the copied GIF data.
void gif_close(void);
```

### Browser Usage

**In browser JS**, the Emscripten factory exports them on the Module instance:

```javascript
const Module = await GifModule({ /* factory opts */ });

// Module.HEAPU8 is the wasm heap (Uint8Array view)
const gifBuffer = new Uint8Array(gifData);
const heapPtr = Module._malloc(gifBuffer.length);
Module.HEAPU8.set(gifBuffer, heapPtr);

const rc = Module._gif_open(heapPtr, gifBuffer.length);
if (rc === 0) {
  const w = Module._gif_width();
  const h = Module._gif_height();
  const fbPtr = Module._gif_fb();
  const canvas = new Uint8ClampedArray(Module.HEAPU8.buffer, fbPtr, w * h * 4);
  
  let delay;
  while ((rc = Module._gif_play(/* delay_ptr */)) > 0) {
    // Draw canvas to <canvas> element
    const imgData = ctx.createImageData(w, h);
    imgData.data.set(canvas);
    ctx.putImageData(imgData, 0, 0);
    // Wait delay ms
  }
  
  Module._gif_close();
  Module._free(heapPtr);
}
```

### Builds

| Target | Toolchain | Output | Size |
|--------|-----------|--------|------|
| **WASI** | `zig c++ -target wasm32-wasi` | `dist/gifdec.wasm` | ~37 KB |
| **WASM** (browser) | `emcc` (Emscripten) | `web/gifdec.{js,wasm}` | ~17 KB wasm + 9 KB js |

### Extension Points

**Adding new GIFs/packs**: Drop `.gif` files into `web/gifs/` or device `/data/characters/<pack>/`; manifest selects them by state.

---

## 2. React Emscripten Simulator Component

**File**: `lab/sim-gallery/src/components/EmscriptenSim.tsx`

### Props

```typescript
{
  src: string              // URL to the .js factory (e.g., "/sims/pet/pet_sim.js")
  factory: string          // globalThis[factory](...) exports the MODULARIZE instance
  width: number            // canvas width (320 for JC3248W535)
  height: number           // canvas height (480)
  onReady?: (instance: unknown) => void  // Callback after module instantiation
}
```

### Behavior

- **Lazy-load**: Probes the URL (404 = "not built" card), fetches as classic `<script>`, calls factory
- **Visibility-gated**: Auto-pauses/resumes CPU via `Module.pauseMainLoop()`/`resumeMainLoop()` on scroll
- **Manual start**: Renders a "▶ Tap to Run" button overlay until ready
- **Cleanup**: Calls `Module._exit_runtime()` on unmount

### Factory Contract (MODULARIZE instances)

```javascript
// Created with: emcc ... -sMODULARIZE=1 -sEXPORT_NAME=<factory>
const Module = await window[factory]({
  canvas: HTMLCanvasElement,
  print: (msg) => console.log(`[factory]`, msg),
  printErr: (msg) => console.warn(`[factory]`, msg)
});

// The module provides:
Module.pauseMainLoop();      // Stop the rAF loop
Module.resumeMainLoop();     // Resume it
Module._exit_runtime();      // Cleanup on unmount
Module.ccall(name, ret, types, args);  // Call exported C functions
```

### Embedded Simulators (Gallery)

| Section | ID | Factory | Src | Canvas | Notes |
|---------|----|---------|----|--------|-------|
| 01 | bufo | — | React component | 320×480 | Pure JS state machine + pet.cpp logic |
| 02 | wasm | — | iframe embed | — | `gif-wasm` browser demo (index.html) |
| 03 | pet-lvgl | PetSim | `/sims/pet/pet_sim.js` | 320×620 | Pet + HUD (LVGL+SDL) |
| 04 | oracle-v1 | OracleFaceV1 | `/sims/oracle-v1/oracle_face_sim_v1.js` | 320×480 | First skeleton oracle UI |
| 05 | oracle-v2 | OracleFaceV2 | `/sims/oracle-v2/oracle_face_sim_v2.js` | 320×480 | 10-card grid oracle UI |
| 06 | term | createOracleTerm | `/sims/term/oracle_term_sim.js` | 320×480 | Fleet terminal (LVGL recolor) |
| 07 | term-live | — | iframe embed | — | Live terminal viewer (poll `/api/capture`) |
| 08 | flash | — | iframe embed | — | esp-web-tools browser flasher |

---

## 3. HTTP APIs (maw backend)

**Endpoints polled by ESPHome devices** (e.g., `fleet-pulse.yaml`):

### GET `/api/ls` — Session List

**Returns**: JSON tree of tmux sessions

```json
{
  "node": "m5",
  "oracle": "leica",
  "sessions": [
    {
      "name": "main",
      "windows": [
        { "name": "0:bash", "active": true },
        { "name": "1:editor", "active": false }
      ]
    },
    {
      "name": "work",
      "windows": [
        { "name": "0:nvim", "active": false }
      ]
    }
  ]
}
```

**Used by**: 
- `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml` (polls every 5s via `http_request.get`, renders 16 rows in LVGL)
- `lab/esp32-fleet-pulse-esphome/sim/app/src/lib/mawClient.ts` (browser wrapper: `fetchPanes(baseUrl)`)

**Frontend wrapper** (TypeScript):

```typescript
export async function fetchPanes(base: string): Promise<string[]> {
  const r = await fetch(base.replace(/\/+$/, '') + '/api/ls')
  if (!r.ok) throw new Error('HTTP ' + r.status)
  const d = (await r.json()) as { sessions?: { name: string; windows?: { name: string }[] }[] }
  const out: string[] = []
  for (const s of d.sessions ?? [])
    for (const w of s.windows ?? [])
      if (s.name && w.name) out.push(`${s.name}:${w.name}`)
  return out
}
```

### GET `/api/capture?target=<session:window>` — Pane Content

**Returns**: JSON with ANSI capture

```json
{
  "content": "[38;5;10mroot@m5 fleet [0m\n...[K"
}
```

**Used by**:
- `lab/esp32-fleet-pulse-esphome/sim/app/src/lib/mawClient.ts` (browser: `fetchCapture(baseUrl, target)`)
- `lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md` (via `Module.ccall('term_set_content', ...)`)

**Frontend wrapper**:

```typescript
export async function fetchCapture(base: string, target: string): Promise<string> {
  const url = base.replace(/\/+$/, '') + '/api/capture?target=' + encodeURIComponent(target)
  const r = await fetch(url)
  if (!r.ok) throw new Error('HTTP ' + r.status)
  const d = (await r.json()) as Capture
  return d.content ?? ''
}
```

### CORS Requirement

Both endpoints require `Access-Control-Allow-Origin` header (or proxy/same-origin setup) because browsers can't fetch from a LAN maw when the gallery is hosted on HTTPS CDN.

---

## 4. Pet Simulator State Machine

**File**: `lab/sim-gallery/src/sims/pet/petLogic.ts`

### State Types

```typescript
type PetState = 'idle' | 'busy' | 'attention' | 'sleep' | 'heart'
```

### Heartbeat Snapshot

The browser-pet polls or receives snapshots (JSON):

```typescript
interface Snapshot {
  total: number           // total agents/tasks
  running: number         // currently running
  waiting: number         // awaiting approval
  msg: string             // status message
  tokens: number          // API tokens used (5h window)
  pct5h: number           // API usage % (5h) | -1 = absent
  reset5h: number         // seconds until 5h reset | -1 = absent
  pct7d: number           // API usage % (7d) | -1 = absent
  reset7d: number         // seconds until 7d reset | -1 = absent
  name?: string           // pet name (optional)
}
```

### State Computation

```typescript
function computeDesired(link: Link, snap: Snapshot, now: number): PetState {
  if (!link.connected) return 'idle'
  if (now - link.lastSnap > STALE_MS) return 'idle'  // 30s stale timeout
  if (snap.waiting > 0) return 'attention'           // orange alert
  if (snap.running > 0) return 'busy'               // working
  if (snap.total === 0) return 'sleep'              // done
  return 'idle'
}
```

### Character Pack Structure

**Manifest**: `data/characters/<pack>/manifest.json`

```json
{
  "name": "bufo",
  "colors": {
    "bg": "#000000",
    "text": "#FFFFFF",
    "textDim": "#808080"
  },
  "states": {
    "sleep": "sleep.gif",
    "idle": ["idle_0.gif", "idle_1.gif", ...],
    "busy": "busy.gif",
    "attention": "attention.gif",
    "heart": "heart.gif",
    "celebrate": "celebrate.gif"
  }
}
```

**Files**: 
- `idle_*.gif` — multiple frames, browser rotates them every 3s (IDLE_DWELL_MS)
- Other `.gif` files — single state animations

### Preset Snapshots

Pre-configured "heartbeats" for testing (PetSim.tsx):

```typescript
const PRESETS = {
  idle:      { total: 1, running: 0, waiting: 0, msg: 'idle', ... },
  busy:      { total: 1, running: 1, waiting: 0, msg: 'running: Bash', ... },
  attention: { total: 1, running: 0, waiting: 1, msg: 'approve: rm -rf /tmp/x', ... },
  sleep:     { total: 0, running: 0, waiting: 0, msg: 'all done', ... }
}
```

### Extension: Adding New Pet Packs

1. Create `data/characters/<new-pack>/manifest.json` with the structure above
2. Add `.gif` files for each state (idle, busy, attention, sleep, heart, etc.)
3. Pet browser code auto-discovers packs; no code change needed (it fetches the manifest)

---

## 5. Terminal Simulator (createOracleTerm)

**Files**: 
- `lab/esp32-fleet-pulse-esphome/sim/` (source)
- `GALLERY-INTEGRATION.md` (contract)

### WASM Module Contract

**Factory**: `createOracleTerm`  
**Canvas**: 320×480 (portrait)  
**Build**:

```bash
cd lab/esp32-fleet-pulse-esphome/sim
bash scripts/build-wasm-module.sh
# → dist-module/oracle_term_sim.js + oracle_term_sim.wasm
```

**Emscripten flags**:
```
-sMODULARIZE=1 
-sEXPORT_NAME=createOracleTerm 
-sUSE_SDL=2 
-sEXPORTED_RUNTIME_METHODS=ccall,cwrap
```

### C Function Exports (ccall)

```c
// Set the header label (e.g., "52-esp32:esp32-exp")
void term_set_header(const char *text);

// Set the terminal content (raw ANSI with recolor markup)
void term_set_content(const char *ansi_text);
```

### Browser Usage

```javascript
const Module = await globalThis.createOracleTerm({
  canvas: canvasElement,
  locateFile: (path) => assetUrl + '/' + path,  // so it finds .wasm
  print: console.log,
  printErr: console.warn
});

// On boot, renders a baked-in colored sample (shows immediately).
// Optional: feed live data from /api/capture:
const ansiCapture = await fetchCapture(baseUrl, 'fleet:main');
Module.ccall('term_set_content', null, ['string'], [ansiCapture]);
Module.ccall('term_set_header', null, ['string'], ['m5/esp32-exp']);
```

### Notes

- **Fonts are baked in**: Generated via `lv_font_conv` from the device's exact TTFs (JetBrains Mono + Sarabun), compiled into the `.wasm`. No `.data` files to preload.
- **LVGL v9.5.0**: Matches the device exactly (same recolor + label clipping logic).
- **Memory**: `-sINITIAL_MEMORY=64MB -sALLOW_MEMORY_GROWTH=1` (ANSI captures ~16 KB, recolor markup 2–3×).

---

## 6. React Pet Simulator Component

**File**: `lab/sim-gallery/src/sims/pet/PetSim.tsx`

### Props

None. Component is standalone; reads character packs from `/data/characters/<PACK>/manifest.json`.

### Behavior

- **Boot**: Fetches manifest, loads states + colors
- **rAF loop**: Runs the pet.cpp state machine (every frame):
  - Compute desired state from link + snapshot
  - Update GIF if state changed
  - Rotate idle animations every 3s
- **Heartbeat handler**: Accepts raw JSON snapshots (paste into textarea, click Send)
- **Tap reaction**: Shows heart GIF for 4s (REACT_MS)

### Constants

```typescript
const PACK = 'bufo'                     // character pack name
const BASE = `/data/characters/${PACK}` // where to fetch manifest + GIFs
const W = 320, H = 480, HUD_H = 80     // canvas + HUD dimensions (4:6 ratio)
const REACT_MS = 4000                  // tap → heart duration
const STALE_MS = 30000                 // link goes stale if no heartbeat for 30s
const IDLE_DWELL_MS = 3000              // time per idle GIF before rotating
```

### UI Sections

1. **Device Panel** — Renders the GIF + HUD (state, link, tokens, usage windows)
2. **Controls** — Toggle link, preset buttons, tap/heart reaction
3. **Raw Snapshot** — Textarea to paste/send heartbeats (raw JSON)
4. **Activity Log** — Last 40 events (state changes, heartbeats, errors)

### Extension: Custom States

Add a state to the manifest (e.g., "dizzy", "celebrate") + provide a `.gif` file. The pet auto-updates without code changes.

---

## 7. sim-gallery React App

**File**: `lab/sim-gallery/src/routes/Gallery.tsx`

### Structure

- **Hero section** — Intro + quick-links to each sim
- **8 sections** (scrollable):
  1. Bufo pet (pure JS)
  2. GIF WASM (browser demo iframe)
  3. Pet LVGL (Emscripten MODULARIZE)
  4. Oracle v1 (skeleton UI)
  5. Oracle v2 (10-card grid)
  6. Fleet terminal (MODULARIZE + baked fonts)
  7. Live terminal (iframe, polls `/api/capture`)
  8. Web flasher (esp-web-tools iframe)

### Route Anchors

Navigation via `#<section-id>` (no nested routes; single-page gallery).

### Internationalization

- **EN / TH toggle** (top-right)
- All strings in `src/i18n/strings.ts`
- Display font switches: `font-display` (EN) vs `font-sans` (TH)

### Build

```bash
cd lab/sim-gallery
npm install
npm run dev          # dev server on :5173
npm run build-sims   # compile all LVGL+WASM sims
npm run build        # bundle the React app
npm run deploy       # wrangler (Cloudflare Workers)
```

### Assets

- Character packs: `<root>/data/characters/*/` (served by dev server via fs.allow)
- WASM modules: Built into `/sims/<project>/<factory>.js` and `.wasm`
- Embeds: Standalone iframes (gif-wasm, term-live, esp-web-tools)

---

## 8. ESPHome Integration (fleet-pulse)

**File**: `lab/esp32-fleet-pulse-esphome/fleet-pulse.yaml`

### Hardware

- **MCU**: ESP32-S3
- **Display**: AXS15231 QSPI 320×480 (MIPI DBI)
- **Backlight**: LEDC PWM (GPIO 1)

### HTTP Client Config

```yaml
http_request:
  id: http_client
  timeout: 12s
  verify_ssl: false
  useragent: esp32-fleet-pulse/1.0
  follow_redirects: true
  redirect_limit: 3
  buffer_size_rx: 1024   # increase if JSON truncated
```

### Poll Interval

```yaml
interval:
  - interval: 5s
    then:
      - http_request.get:
          url: http://192.168.1.109:3456/api/ls
          capture_response: true
          max_response_buffer_size: 8192
          on_response:
            then:
              - lambda: |
                  json::parse_json(body, [](JsonObject root) -> bool {
                    // Parse root["sessions"], render in LVGL labels
                    return true;
                  });
```

### LVGL Output

- **Header label**: Shows node/oracle name + session count
- **16 row labels**: Each session (name + window count + active indicator)
- **Recolor on active**: Bright white for active session, dim gray for others

### Substitutions

```yaml
substitutions:
  backend_url: "http://192.168.1.109:3456/api/ls"
```

Change `192.168.1.109:3456` to your maw server's IP:port.

---

## 9. Extension Points & Integration

### Adding a New Simulator

1. **C/C++ source** → Emscripten compile (`emcc ... -sMODULARIZE=1 -sEXPORT_NAME=YourSim`)
2. **Factory function** in `globalThis.YourSim({ canvas, print, printErr })`
3. **Gallery section** in `src/routes/Gallery.tsx`:
   ```tsx
   <EmscriptenSim
     src="/sims/<project>/<factory>.js"
     factory="YourSim"
     width={320}
     height={480}
   />
   ```

### Adding a New Character Pack

1. Create `data/characters/<pack-name>/manifest.json`
2. Add `.gif` files for each state
3. Pet browser auto-discovers (fetch manifest, load GIFs)
4. No firmware code change needed

### Adding a New Pet State or Reaction

1. Add `.gif` file + manifest entry
2. Update firmware `pet.cpp` state machine or browser `petLogic.ts` state enum if needed
3. No rebuild if using manifest-driven approach

### Adding Hardware or Display Support

1. **ESPHome**: Add `.yaml` config with new hardware + display + HTTP client
2. **Simulator**: Build a new Emscripten WASM sim to match the hardware UI
3. **Gallery**: Add a new `<EmscriptenSim>` section

---

## 10. Known Limitations & Caveats

### Browser CORS

- `/api/ls` and `/api/capture` require `Access-Control-Allow-Origin` headers
- Public HTTPS deploys can't reach LAN maw servers (mixed-content + RFC1918)
- Workaround: proxy the maw backend through your HTTPS domain, or use local dev

### WASM Memory

- GIF decoder allocates canvas on the wasm heap; large GIFs (e.g., 320×480×32bpp for every frame) can exceed available memory
- Gif-wasm mitigates by composing frames incrementally (only one canvas buffer)
- 64 MB initial WASM memory is usually sufficient for the simulators

### Emscripten Preload Quirk

- `-sMODULARIZE=1` + `--preload-file` can produce 0-byte `.data` files (don't use it)
- Terminal simulator works around this by baking fonts into the `.wasm` directly

### ESPHome JSON Parsing

- Buffer size must be large enough for `/api/ls` response (~2.8 KB for 16 sessions)
- Default 1 KB truncates the JSON; set `max_response_buffer_size: 8192`

---

## 11. File Structure Summary

```
lab/
├── gif-wasm/
│   ├── src/
│   │   ├── gifcore.{h,cpp}     ← WASM GIF decoder API
│   │   └── wasi_main.cpp        ← CLI entry point
│   ├── vendor/AnimatedGIF/      ← Apache-2.0 decoder lib
│   ├── web/
│   │   ├── gifdec.{js,wasm}     ← Browser WASM module
│   │   ├── index.html            ← Demo UI
│   │   └── gifs/                 ← Test GIFs
│   └── Makefile
│
├── sim-gallery/
│   ├── src/
│   │   ├── components/EmscriptenSim.tsx  ← WASM mount
│   │   ├── sims/
│   │   │   ├── pet/
│   │   │   │   ├── PetSim.tsx            ← Pure JS pet
│   │   │   │   └── petLogic.ts           ← State machine
│   │   │   └── term/                     ← Fleet terminal
│   │   └── routes/Gallery.tsx            ← 8-section gallery
│   ├── package.json
│   ├── vite.config.ts
│   └── Makefile                          ← build-sims target
│
├── esp32-fleet-pulse-esphome/
│   ├── fleet-pulse.yaml         ← ESPHome config (HTTP poll)
│   ├── sim/
│   │   ├── main_term.c          ← Terminal core (C)
│   │   ├── GALLERY-INTEGRATION.md
│   │   └── scripts/build-wasm-module.sh
│   └── ...
│
├── jc3248-pet/
│   ├── src/pet.cpp              ← Firmware pet logic
│   ├── data/characters/bufo/
│   │   ├── manifest.json
│   │   ├── idle_*.gif
│   │   ├── busy.gif
│   │   └── ...
│   └── sim/
│       ├── main_pet.c           ← Simulator core
│       └── Makefile
│
└── ...
```

---

## 12. Integration Examples

### Example 1: Render a GIF in the browser

```javascript
const gifData = await fetch('bufo/busy.gif').then(r => r.arrayBuffer());
const Module = await GifModule({});
const p = Module._malloc(gifData.byteLength);
Module.HEAPU8.set(new Uint8Array(gifData), p);
Module._gif_open(p, gifData.byteLength);

const w = Module._gif_width();
const h = Module._gif_height();
const canvas = document.createElement('canvas');
canvas.width = w;
canvas.height = h;
const ctx = canvas.getContext('2d');

let delay;
while (Module._gif_play(0) > 0) {
  const fb = Module._gif_fb();
  const pixels = new Uint8ClampedArray(Module.HEAPU8.buffer, fb, w * h * 4);
  const imgData = ctx.createImageData(w, h);
  imgData.data.set(pixels);
  ctx.putImageData(imgData, 0, 0);
  await new Promise(r => setTimeout(r, delay || 16));
}
Module._gif_close();
Module._free(p);
```

### Example 2: Poll maw /api/ls from a browser app

```typescript
const baseUrl = 'http://192.168.1.109:3456';
const panes = await fetchPanes(baseUrl);
console.log(panes);  // ["main:0:bash", "main:1:editor", "work:0:nvim"]

const capture = await fetchCapture(baseUrl, panes[0]);
console.log(capture);  // ANSI text
```

### Example 3: Mount a WASM simulator in React

```tsx
<EmscriptenSim
  src="/sims/pet/pet_sim.js"
  factory="PetSim"
  width={320}
  height={480}
  onReady={(module) => {
    console.log('Pet sim ready:', module);
  }}
/>
```

### Example 4: Create a new character pack

```bash
mkdir -p data/characters/clawd
cat > data/characters/clawd/manifest.json <<EOF
{
  "name": "clawd",
  "colors": { "bg": "#1a1a2e", "text": "#eee" },
  "states": {
    "idle": "idle.gif",
    "busy": "busy.gif",
    "sleep": "sleep.gif"
  }
}
EOF
cp /path/to/gifs/*.gif data/characters/clawd/
```

---

## 13. Related Documentation

- **GIF WASM README**: `lab/gif-wasm/README.md`
- **Gallery Integration**: `lab/esp32-fleet-pulse-esphome/sim/GALLERY-INTEGRATION.md`
- **ESP-IDF Pet**: `lab/jc3248-pet/src/pet.cpp` (firmware state machine)
- **ESPHome Docs**: https://esphome.io/ (http_request, LVGL, JSON parsing)
- **Emscripten Docs**: https://emscripten.org/ (MODULARIZE, ccall, memory)

---

*Document compiled by Leica Oracle for nazt ESP32 team.*
