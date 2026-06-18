# ESP32 Oracle — Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     sim-gallery (React + Vite)                 │
│                    lab/sim-gallery/ → cdn                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  01: Bufo    │ │  02: WASM    │ │  03: Pet     │ ...        │
│  │  (Pure JS)   │ │  (iframe)    │ │  (Emscripten)│            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │                │                │                    │
│         └────────────────┴────────────────┴────────────────┐    │
│                                                           │    │
│                          EmscriptenSim Component          │    │
│                   (lazy-load, CPU pause, clean)          │    │
│                                                           │    │
│                              ▼                            │    │
│    ┌─────────────────────────────────────────────┐       │    │
│    │     Emscripten MODULARIZE WASM Instances    │       │    │
│    │  Module._gif_open / _play / _fb / _close    │       │    │
│    │  Module.ccall / cwrap (for C exports)       │       │    │
│    │  Module.HEAPU8 (wasm heap Uint8Array)       │       │    │
│    └─────────────────────────────────────────────┘       │    │
│                     △                                     │    │
│                     │ globalThis[factory]                │    │
│                     │                                     │    │
│         <script src="/sims/<proj>/<factory>.js">         │    │
│                                                           │    │
│    PetSim (React component, no WASM)                     │    │
│    ├─ State machine (petLogic.ts)                        │    │
│    ├─ Snapshot heartbeat handler                         │    │
│    ├─ GIF loader from /data/characters/                  │    │
│    └─ rAF loop (state transitions)                       │    │
│                                                           │    │
│    HTML iframes (§02, §07, §08)                          │    │
│    ├─ gif-wasm/web/index.html                            │    │
│    ├─ esp32-fleet-pulse-esphome/sim/oracle_term_sim.html│    │
│    └─ esp-web-tools flasher                              │    │
│                                                           │    │
│    HTTP polling (optional, on device.local)              │    │
│    ├─ fetch /api/ls → session list                       │    │
│    └─ fetch /api/capture?target=<s:w> → ANSI text       │    │
│                                                           │    │
└───────────────────────────────────────────────────────────────┘
         △                          △
         │                          │
         │ CORS / proxy             │ same-origin
         │ (RFC1918 caveat)         │ (dev / localhost)
         │                          │
         │                          │
    ┌────┴──────────────────────────┴──────────┐
    │                                           │
    │       Backend (maw + ESPHome)             │
    │                                           │
    │  ┌─────────────────────────────────────┐  │
    │  │   maw HTTP server (:3456)           │  │
    │  │  GET /api/ls → JSON(sessions)       │  │
    │  │  GET /api/capture?target → JSON     │  │
    │  │  (tmux session list parser)         │  │
    │  └─────────────────────────────────────┘  │
    │                                           │
    │  ┌─────────────────────────────────────┐  │
    │  │  ESPHome fleet-pulse device         │  │
    │  │                                     │  │
    │  │  ┌─────────────────────────────┐    │  │
    │  │  │ HTTP client (esp-idf)       │    │  │
    │  │  │ poll /api/ls every 5s       │    │  │
    │  │  └────────────┬────────────────┘    │  │
    │  │               │                      │  │
    │  │  ┌────────────▼──────────────────┐  │  │
    │  │  │ JSON parser (esp-idf lambda)  │  │  │
    │  │  │ Parse sessions + windows      │  │  │
    │  │  └────────────┬───────────────────┘  │  │
    │  │               │                      │  │
    │  │  ┌────────────▼──────────────────┐  │  │
    │  │  │ LVGL label renderer           │  │  │
    │  │  │ Header + 16 session rows      │  │  │
    │  │  │ recolor on active             │  │  │
    │  │  └────────────┬───────────────────┘  │  │
    │  │               │                      │  │
    │  │  ┌────────────▼──────────────────┐  │  │
    │  │  │ AXS15231 QSPI display         │  │  │
    │  │  │ 320×480 / 40 MHz              │  │  │
    │  │  │ (JC3248W535 board)            │  │  │
    │  │  └───────────────────────────────┘  │  │
    │  │                                     │  │
    │  └─────────────────────────────────────┘  │
    │                                           │
    └───────────────────────────────────────────┘
```

---

## Data Flow: Pet Heartbeat

```
Browser (sim-gallery)
│
├─ User taps "Send" or presets button
│
├─ Parse JSON → Snapshot { total, running, waiting, ... }
│
├─ Call PetSim.applySnapshot(snap)
│        │
│        ├─ Update linkRef + snapRef
│        ├─ Trigger React re-render (for HUD display)
│        └─ Continue rAF loop
│
├─ rAF loop (16.67 ms frames)
│        │
│        ├─ Compute desired state:
│        │  if (!link.connected) → idle
│        │  if (stale > 30s) → idle
│        │  if (waiting > 0) → attention ← alert
│        │  if (running > 0) → busy      ← working
│        │  if (total == 0) → sleep      ← idle
│        │  else → idle
│        │
│        ├─ If state changed:
│        │  ├─ Look up GIF in manifest
│        │  ├─ Cache-bust URL (t=performance.now())
│        │  └─ Load GIF (fetch → rAF → display)
│        │
│        ├─ If state == idle && idle_list.length > 1:
│        │  ├─ Every 3s (IDLE_DWELL_MS), rotate to next idle GIF
│        │  └─ Cycle: idle_0 → idle_1 → idle_2 → ... → idle_0
│        │
│        ├─ Mirror state → React state (for UI updates)
│        └─ Repeat next frame
│
└─ GIF canvas output to <canvas> or <img> element
```

---

## Data Flow: ESPHome HTTP Poll

```
ESPHome device
│
├─ Boot: load fleet-pulse.yaml config
│        ├─ init WiFi
│        ├─ init HTTP client
│        ├─ init LVGL display
│        └─ setup interval timer (5s)
│
├─ Every 5 seconds:
│        │
│        ├─ HTTP GET http://192.168.1.109:3456/api/ls
│        │        ├─ TCP connect
│        │        ├─ TLS optional (verify_ssl: false)
│        │        └─ Read response (max 8192 bytes)
│        │
│        ├─ Lambda: json::parse_json(body, [](JsonObject root) {
│        │        │
│        │        ├─ Extract root["node"] / root["oracle"]
│        │        ├─ Iterate root["sessions"][]
│        │        ├─ For each session, extract name + windows
│        │        ├─ Check windows[*]["active"] flag
│        │        │
│        │        ├─ Format header:
│        │        │  snprintf(hdr, "m5/leica 3 sessions", node, oracle, n)
│        │        │  lv_label_set_text(id(hdr), hdr)
│        │        │
│        │        ├─ Format rows (16 total):
│        │        │  for i, session in enumerate(sessions):
│        │        │    if i >= 16: break
│        │        │    text = f"{'*' if active else ' '} {name}  {nwindows}w"
│        │        │    lv_label_set_text(rows[i], text)
│        │        │    color = 0xFFFFFF if active else 0x888888
│        │        │    lv_obj_set_style_text_color(rows[i], color)
│        │        │
│        │        └─ Clear remaining rows
│        │
│        ├─ Display refresh (auto)
│        └─ Wait 5s, repeat
│
└─ Physical AXS15231 display
   ├─ Header: "m5/leica  3 sessions"
   ├─ Row 0: "* main  2w"        (bright, active)
   ├─ Row 1: "  work  1w"        (dim, inactive)
   └─ Row 2-15: (empty)
```

---

## WASM Module Lifecycle (Emscripten MODULARIZE)

```
HTML loads script:
  <script src="/sims/pet/pet_sim.js"></script>

On script load:
  window.PetSim = async (opts) => {
    // Creates a new Emscripten Module instance
    const Module = {
      canvas: opts.canvas,
      print: opts.print,
      printErr: opts.printErr,
      preRun: [ ... ],
      postRun: [ ... ]
    };
    
    // Instantiate WASM
    const wasmBinary = fetch('./pet_sim.wasm');
    const instance = await WebAssembly.instantiate(wasmBinary, {
      env: {
        memory: new WebAssembly.Memory({ initial: 256 }),
        emscripten_resize_heap: ...,
        ... other imports
      }
    });
    
    // Assign exports to Module
    Module._main = instance.exports._main;
    Module._gif_open = instance.exports.gif_open;
    Module._gif_play = instance.exports.gif_play;
    // ... etc
    
    // Run init
    instance.exports._emscripten_stack_setup();
    instance.exports.__wasm_call_ctors();
    
    // Start LVGL + SDL event loop (rAF)
    browser_main_loop(instance);
    
    return Module;  // resolve promise
  }

React component:
  const [ready, setReady] = useState(false);
  
  useEffect(() => {
    const script = document.createElement('script');
    script.src = '/sims/pet/pet_sim.js';
    script.onload = async () => {
      const Module = await globalThis.PetSim({
        canvas: canvasRef.current,
        print: console.log,
        printErr: console.warn
      });
      setReady(true);
      onReady?.(Module);
    };
    document.head.appendChild(script);
  }, [onReady]);
  
  return ready ? <canvas ref={canvasRef} /> : <Spinner />;

User interaction:
  Module.ccall('pet_tap', null, [], []);  // C function call
  Module.pauseMainLoop();  // pause rAF when scrolled out of view
  Module.resumeMainLoop(); // resume on scroll back in

Cleanup:
  useEffect(() => {
    return () => { Module._exit_runtime?.(); };
  }, []);
```

---

## Character Pack Discovery & Loading

```
Browser:
  fetch('/data/characters/bufo/manifest.json')
    │
    ├─ Parse: { name, colors, states }
    │
    ├─ Store colors in state
    │
    ├─ Store states (state → ["gif1", "gif2"] mapping)
    │
    └─ When entering a state (e.g., 'busy'):
         │
         ├─ Look up state in manifest: states.busy = "busy.gif"
         │
         ├─ Construct URL: /data/characters/bufo/busy.gif?t=<timestamp>
         │    (cache-bust with timestamp so re-selecting same gif restarts it)
         │
         ├─ Assign to <img src="...">
         │    or <canvas> with GIFInstance
         │
         └─ GIF animates until state changes

For idle (multi-frame):
  states.idle = ["idle_0.gif", "idle_1.gif", ..., "idle_8.gif"]
  
  Every 3s (IDLE_DWELL_MS):
    idleRotIndex = (idleRotIndex + 1) % idle.length
    showGif(idle[idleRotIndex])
```

---

## Extension: Adding a New Simulator

```
1. Create C/C++ source:
   lab/my-project/src/main.c
     │
     ├─ int main() { ... LVGL+SDL event loop ... }
     ├─ void my_function() { }  ← exported via emscripten
     └─ ...

2. Build with Emscripten:
   emcc src/main.c \
     -sMODULARIZE=1 \
     -sEXPORT_NAME=MySimulator \
     -sUSE_SDL=2 \
     -sEXPORTED_RUNTIME_METHODS=ccall,cwrap \
     -sFULL_ES6=1 \
     -O2 \
     -o web/my_simulator.js

   → web/my_simulator.js + web/my_simulator.wasm

3. Add to sim-gallery:
   lab/sim-gallery/src/routes/Gallery.tsx
   
   <SimSection id="my-sim" ...>
     <DeviceFrame label="...">
       <EmscriptenSim
         src="/sims/my-project/my_simulator.js"
         factory="MySimulator"
         width={320}
         height={480}
         onReady={(mod) => {
           // Optional: initialize the simulator
           mod.ccall('my_function', null, [], []);
         }}
       />
     </DeviceFrame>
   </SimSection>

4. Rebuild gallery:
   cd lab/sim-gallery
   npm run build
```

---

## Extension: Adding a New Character Pack

```
1. Create directory:
   mkdir -p data/characters/my-pet

2. Create manifest:
   cat > data/characters/my-pet/manifest.json <<EOF
   {
     "name": "my-pet",
     "colors": {
       "bg": "#1a1a2e",
       "text": "#00ff00",
       "textDim": "#666666"
     },
     "states": {
       "idle": ["idle_0.gif", "idle_1.gif"],
       "busy": "busy.gif",
       "attention": "attention.gif",
       "sleep": "sleep.gif",
       "heart": "heart.gif"
     }
   }
   EOF

3. Add GIF files:
   cp /path/to/gifs/*.gif data/characters/my-pet/

4. Update pet simulator to load new pack:
   const PACK = 'my-pet'  (in petLogic.ts or as a selection dropdown)

5. Reload browser:
   The PetSim component auto-discovers packs
   (no rebuild needed if you're adding, not code-changing)
```

---

## CORS Considerations

```
Browser (sim-gallery on https://example.com)
  │
  ├─ fetch('http://192.168.1.109:3456/api/ls')
  │        │
  │        ├─ Browser sees cross-origin:
  │        │  ├─ Scheme mismatch: https → http (mixed-content warning)
  │        │  ├─ Host mismatch: example.com → 192.168.1.109
  │        │  └─ RFC1918 RFC: public HTTPS → private IP (blocked)
  │        │
  │        └─ Preflight OPTIONS request
  │            Access-Control-Allow-Origin: ?
  │            Access-Control-Allow-Methods: GET
  │
Workarounds:
  1. Proxy maw through your HTTPS domain
     example.com/api/ls → proxy → maw:3456/api/ls
  
  2. Use local dev (localhost)
     http://localhost:5173 → http://localhost:3456/api/ls
     (same-origin, no CORS needed)
  
  3. Service worker to rewrite fetch (fragile)
  
  4. VPN / same network + maw adds CORS headers
     (maw must respond with Access-Control-Allow-Origin: https://example.com)
```

---

## Deployment & CI/CD

```
Local dev:
  cd lab/sim-gallery
  npm install
  npm run dev                  # :5173
  npm run build-sims          # compile WASM sims (Makefile)
  
  curl http://localhost:3456/api/ls  # maw on localhost
  
  (Access-Control-Allow-Origin not needed for localhost)

Production (Cloudflare Workers):
  npm run build               # vite build → dist/
  npm run deploy              # wrangler deploy
  
  (Cloudflare serves dist/ at example.com)
  (Gallery iframes + fetch CORS checks apply)
  
Git:
  All source in repo (no build artifacts committed)
  
  .gitignore:
    dist/
    node_modules/
    .env.local
    
CI/CD:
  On push to main:
    npm ci
    npm run build-sims
    npm run build
    npm run deploy --dry-run  (or: wrangler deploy)
```

---

## Troubleshooting Map

```
Symptom: "Simulator not built" card (orange)
  └─ Cause: Emscripten .js not found at /sims/<proj>/<factory>.js
  └─ Fix: npm run build-sims in gallery dir

Symptom: CORS error on /api/ls fetch
  └─ Cause: maw missing Access-Control-Allow-Origin header
  └─ Fix: Proxy through HTTPS domain OR use local dev

Symptom: ESPHome JSON parsing fails
  └─ Cause: max_response_buffer_size < /api/ls response (~2.8 KB)
  └─ Fix: Set max_response_buffer_size: 8192 in fleet-pulse.yaml

Symptom: Pet GIF won't decode (OOM)
  └─ Cause: gif decoder heap exhausted
  └─ Fix: Ensure GIF isn't > 320×480×4 bytes × frame count
           Or: pre-optimize GIF (reduce frames / palette)

Symptom: terminal module doesn't render (black canvas)
  └─ Cause: fonts not baked in (missing lv_font_conv step)
  └─ Fix: Check sim/fonts_gen/ → compile to .c → link into .wasm
```

---

*Architecture diagram compiled by Leica Oracle, 2026-06-17.*
