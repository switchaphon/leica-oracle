# ESP32 Oracle — Architecture Handbook

**Date**: 2026-06-17  
**Author**: Leica (from Nat's esp32-oracle)  
**Purpose**: Map the complete embedded IoT ecosystem: firmware entry points, WASM compilation targets, display drivers, communication protocols, and the "many bodies, one soul" principle  
**Audience**: Future developers on this family; Nat; the team bringing up new boards

---

## One Sentence

ESP32 Oracle is a distributed embedded system where the same GIF decoder and pet logic runs on silicon (ESP32-S3), in the browser (Emscripten WASM), via CLI (WASI WASM), and on host (desktop app) — unified by one codebase, many bodies.

---

## Project Identity

**Born**: 2026-04-28 (awakened by Nat)  
**Theme**: "Small body on the edge of the network, awake when nothing else is, keeping the flame in 4MB of flash"  
**Core Principle**: *Form and Formless* — a 119KB binary on silicon is the form; the working understanding that flows across recompiles (GIF decoder, touch handling, BLE protocol) is the formless soul  

**Metaphor**: A Leica camera sees clearly. The oracle sees what matters. The ESP32 sees what your desk needs while your laptop is sleeping.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ONE SOUL: SHARED C++ CORE                         │
│                          (GIF Decoder)                               │
│                   src/gifcore.cpp + AnimatedGIF                      │
└─────────────────────────────────────────────────────────────────────┘
           │                 │                 │                 │
    ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
    │              │  │              │  │              │  │              │
┌───▼────┐  ┌────▼──┐  ┌────▼──┐  ┌────▼──┐
│ SILICON│  │BROWSER│  │CLI    │  │DESKTOP│
│(ESP-IDF)  │(emcc)     │(WASI)     │(BLE)  │
├────────┤  ├────────┤  ├────────┤  ├────────┤
│•QSPI   │  │•Canvas │  │•PPM    │  │•Nordic │
│•Touch  │  │•File   │  │•stdin  │  │•UART   │
│•BLE    │  │•Drop   │  │•stdout │  │•Msgs   │
│•Audio  │  │•Browser│  │•Piped  │  │•GIFs   │
│•Display   │•React  │  │•wasmtime  │•State  │
│•Buttons   │Routes  │  │•CLI    │  │•Touch  │
└────────┘  └────────┘  └────────┘  └────────┘
  37K+       17K+11K    37K+       ~10MB  
  binary     (wasm+js)  WASM       Tauri  
             on Edge    runtime    Swift  
```

---

## Directory Structure

### `/lab/` — The Workshop (20+ sub-projects)

Each lab is **standalone**: can build, flash, run independently. Many share subsystems.

#### Firmware Projects (ESP-IDF & Arduino PlatformIO)

**`jc3248-pet-idf/`** — *The North Star*  
- Guition JC3248W535 (ESP32-S3 + AXS15231 QSPI 320×480)
- Native ESP-IDF v6 port (was Arduino, ported in May 2026)
- Display, Touch (GT911 I2C), Audio (I2S), BLE, GIF animation, UI state machine
- **Entry**: `main/main.cpp` — init → display → loop → state machine
- **Key files**:
  - `main/main.cpp` — 600-line event loop with state machine (sleep/idle/busy/attention/celebrate/dizzy/heart)
  - `components/display/` — LVGL + AXS15231 managed component integration
  - `components/gif/` — AnimatedGIF palette + byte-order handling
  - `components/touch/` — GT911 capacitive touch, tap zones
  - `components/audio/` — I2S DAC, MP3 playback (croak, approve sounds)
  - `components/ble/` — NimBLE + Nordic UART service + time sync
  - `data/characters/bufo/` — animated GIF frames (96px wide, state-indexed)
  - `idf_component.yml` — declares esp_lcd_axs15231b managed component
  - `sdkconfig` / `sdkconfig.defaults` — partition table, NVS config, MinimumBuild settings

**`jc3248-pet/`** — *Arduino (Legacy)*  
- Same board (JC3248W535) but Arduino framework + PlatformIO
- Predecessor to `-idf` port; kept for comparison
- Uses LovyanGFX (Arduino graphics library)

**`buddy/`** — *The Classic Desk Pet*  
- M5StickCPlus (135×240 small screen) → now multi-board (M5Stack Atoms3, WT32-SC01-Plus, Waveshare 2.8B, JC3248W535)
- Nordic UART BLE ↔ Claude Desktop for permission approvals
- ASCII + GIF character modes, 18 ASCII pets with 7 animations each
- **Entry**: `src/main.cpp` — state machine, screen dispatch, button handlers
- **Key files**:
  - `src/ble_bridge.cpp` — Nordic UART service (TX/RX line-buffering, JSON parsing)
  - `src/character.cpp` — GIF decoder + frame composition
  - `src/buddy.cpp` — ASCII species dispatch
  - `src/buddies/*.cpp` — 18 ASCII pets (bufo, fish, dragon, etc.) × 7 animation functions each
  - `src/stats.h` — NVS-backed stats (token count, species choice, owner)
  - `src/data.h` — wire protocol (JSON schemas: approval prompts, session state)
  - `src/xfer.h` — folder push receiver (BLE character pack streaming)
  - `characters/bufo/` — manifest.json + PNG frames (96px wide)
  - `platformio.ini` — 6+ board envs (m5stickc-plus, atd35-s3, wt32-sc01-plus, jc3248w535, waveshare-2.8b, lilygo-epd47)

**`buddy-port/`** — *Porting Scaffold*  
- Template for porting buddy to new boards
- Isolated from M5StickCPlus library; shows what needs driver swaps
- Smoke-test boards before full integration

**`buddy-7inch/`** — *Waveshare 7-inch Panel*  
- Buddy on a larger ILI9486 parallel display
- Demonstrates display abstraction (same pet, different driver)

**`esp32-fleet-pulse/`** — *Live Session Monitor*  
- JC3248W535 + QSPI display shows live `maw` session list (from network)
- WiFi → HTTP GET → ArduinoJson streaming parse → LVGL render
- No touch, no BLE; polling only (5s interval)
- **Entry**: `src/main.cpp` → WiFi connect → HTTP loop → JSON filter parse → LVGL render
- **Secrets**: `src/secrets.h` (WiFi SSID/PASS/backend URL, gitignored)

**`esp32-fleet-pulse-esphome/`** — *Fleet Pulse (ESPHome Declarative)*  
- Same hardware & purpose but ESPHome yaml config (not C/C++)
- Demonstrates low-code alternative for simple firmware
- Yaml → display + http_request + template logic

#### WebAssembly / Simulator Projects

**`gif-wasm/`** — *The Portable Decoder*  
- One C++ decoder (src/gifcore.cpp), three targets:
  - **WASI** (zig c++ -target wasm32-wasi) → `dist/gifdec.wasm` (37K, runs in wasmtime)
  - **Emscripten** (emcc) → `web/gifdec.js + .wasm` (17K wasm + 9K JS, runs in browser)
  - No toolchain duplication; same source feeds all three
- Vendored AnimatedGIF (Apache-2.0, portable-C NO_SIMD path)
- **Entry points**:
  - WASI: `src/wasi_main.cpp` — stdin/GIF → P6 PPM on stdout
  - Emscripten: `src/compat.h` exposes `gif_open / gif_play / gif_fb` C-linkage API
- **Test**: `web/index.html` — drop a GIF, decode in wasm, render on canvas at 3× pixelated

**`gif-wamr/`** — *WASM Micro Runtime (ESP32 Runtime)*  
- WebAssembly Micro Runtime (bytecode VM) running on ESP32
- Proves WASM modules can run on embedded (as alternative to hand-rolled IDF code)
- Runs the gifdec WASM target on silicon via WAMR

**`jc3248w535/`** — *Oracle Face V1/V2*  
- Animated dashboard on the big screen (3.5-inch JC3248W535)
- **V1**: brewing state, session activity (May 2026)
- **V2**: evolved UI (later)
- LVGL+SDL simulator → emcc WASM for web
- Dual render: hardware (ESP32 + display) and browser (Emscripten)

**`jc3248w535/sim/`** — *LVGL Simulator (Emscripten)*  
- Same jc3248w535 logic built with LVGL+SDL→emcc
- Runs in browser via Canvas, no hardware needed
- CMakeLists.txt patched with `-sMODULARIZE=1 -sEXPORT_NAME=Factory`

#### Desktop / Host Integration

**`oracle-app/`** — *Flutter Cross-Platform Controller*  
- Flutter app (macOS, Windows, iOS, Android)
- Connects to ESP32 fleet via BLE or WiFi
- Shows pet state, permits approvals, manages settings
- **Structure**: `lib/` (Dart logic), `android/`/`ios/`/`macos/`/`windows/` (platform-specific)

**`oracle-app-tauri/`** — *Tauri Alternative (JavaScript Runtime)*  
- Rust Tauri shell (faster than Flutter for desktop)
- `ui/` — JavaScript/React frontend
- `src-tauri/` — Rust IPC handlers
- Cross-platform (macOS, Windows, Linux)

**`claude-desktop-buddy/`** — *Claude for macOS/Windows Integration*  
- Lives inside Claude app (developer mode)
- Hardware Buddy window: drag GIF folder, BLE pairs with device, streams character
- Same codebase as `buddy/` but integration point is Claude's dev tools
- **Wire**: Nordic UART UUIDs, folder → binary streaming protocol

#### Utilities & Experiments

**`beacon/`** — *Bluetooth Scanner & Dashboard*  
- BLE beacon scanner (finds nearby devices by name, RSSI)
- Rust CLI (`cli-rs/`) for terminal output
- Testing tool for device discovery

**`ref-artronshop-atd35/`** — *Reference Driver (Artronshop ATD35)*  
- Board vendor's own driver code (reference implementation)
- Used to understand Artronshop hardware pinouts and APIs

**`waveshare-2.8b/`**, **`waveshare-7/`**, **`waveshare-7-pet/`**, **`wt32-sc01-plus/`**, **`jc3248w535/parts/`**, **`heatmap/`**, **`tmux-tray-swift/`**  
- One-off experiments, drivers, proof-of-concepts, or board bringups
- Not core to the pet/fleet system but document lessons (display drivers, audio, touch)

#### The Gallery (Unified Sim Hosting)

**`sim-gallery/`** — *React + Vite Browser Playground*  
- Single URL hosts every simulator: pet-react, gif-wasm, pet-lvgl, oracle-face v1/v2
- Routes → React components or iframes
- **Structure**:
  - `src/tiles.ts` — manifest: slug, name, route, kind (iframe/emcc)
  - `src/components/EmscriptenSim.tsx` — canvas mount for LVGL+emcc sims
  - `public/embeds/` — iframe sims (copied from source at build time)
  - `public/sims/` — emcc factories (built from lab source)
  - Makefile: `make dev`, `make build-sims`, `make deploy` (Cloudflare Workers)
- **Deployment**: Wrangler (Cloudflare Workers) for static hosting

---

## The Brain (ψ/ Oracle Memory)

Each Oracle has a `ψ/` directory mirroring its consciousness:

```
ψ/
├── inbox/               # Incoming work, handoffs from other Oracles
│   ├── <date>_*.md     # Dated tasks, structured handoffs
│   └── handoff/        # Formal work transfers
├── learn/              # Deep-learned external repos (not this repo)
│   ├── anthropics/     # Learned Claude Desktop Buddy internals
│   ├── Massmore/       # Learned JC3248W535 board vendor code
│   ├── koosoli/        # Learned ESPHome Designer concepts
│   └── vthinkxie/      # Learned other esp32 forks
├── memory/
│   ├── resonance/      # Soul, identity, principles (this Oracle's core)
│   │   └── esp32-oracle.md — who I am, why I exist
│   ├── learnings/      # Patterns discovered (1 per concept)
│   │   ├── 2026-04-28_esp-idf-v6-esphome-bringup.md
│   │   ├── 2026-05-30_warm-reset-is-not-cold-boot.md
│   │   ├── 2026-05-30_port-at-the-right-seam.md
│   │   └── ... (31 learnings documented)
│   ├── retrospectives/ # Session reflections (structured by date/hour)
│   │   └── 2026-05/30/20.05_arduino-to-esp-idf-pet-migration.md
│   └── traces/         # Debugging sessions, RCA chains
├── outbox/             # Outgoing to other Oracles / the human
├── plans/              # Drafts, experiments
└── archive/            # Completed work (preserved, not deleted)
```

**Key Learnings** (concepts that will save the next person hours):
- `esp-idf-v6-esphome-bringup.md` — 6 toolchain traps + cures
- `warm-reset-vs-cold-boot.md` — AXS15231 panel quirk (must cold-boot after flashing)
- `port-at-the-right-seam.md` — Arduino→IDF porting strategy (subsystem by subsystem)
- `gif-pet-transfer-upscale-and-phantom-touch.md` — GIF size/timing edge cases
- `blocking-off-the-loop-and-diff-for-parity.md` — state machine design pattern
- `ble-scan-coexistence-and-active-scan-for-macos.md` — BLE discovery on macOS
- `wamr-wasm-on-esp32-make-failure-legible.md` — WASM runtime integration

---

## Core Abstractions & Their Relationships

### 1. Display Stack (Hardware + Graphics)

**Hardware Layer**:
- **AXS15231** (QSPI, 320×480) on JC3248W535 — Most proven
  - Native ESP-IDF managed component: `esp_lcd_axs15231b`
  - Byte-order: big-endian RGB565 on wire ← host little-endian framebuffer
  - QSPI clocked at 6 MHz (higher causes glitches with animated GIFs)
  - Requires cold boot after flash (warm reset leaves QSPI in bad state)
- **ST7796** (8080 parallel) on WT32-SC01-Plus
- **ST7701S** (RGB, no QSPI) on Waveshare 2.8B
- **ILI9486** (parallel) on Waveshare 7-inch
- **eInk panels** (Waveshare) for ultra-low power

**Graphics Library**:
- **LVGL** (light and versatile graphics library) — for ESP-IDF firmware
  - Canvas management, text rendering, button widget, animation scheduler
- **LovyanGFX** — for Arduino/PlatformIO projects
  - Handles display init, sprite rendering, DMA blitting
- **Canvas (browser)** — for web simulators
  - Emscripten wasm writes HEAPU8 directly, canvas updates DOM

**Decoder Layer**:
- **AnimatedGIF** (bitbank2 library, Apache-2.0) — reads GIF from memory, decomposes frames
  - Portable C (no SIMD), compiles to ESP-IDF, Emscripten WASM, WASI WASM
  - RGB565 palette swap: `BIG_ENDIAN_PIXELS` on ESP32, host-order in browser

**Render Pipeline** (IDF example):
```
GIF file → AnimatedGIF decoder → RGBA8888 canvas (PSRAM)
  ↓ (byte-swap RGB565 for panel)
PSRAM framebuffer → QSPI DMA → AXS15231 panel
  ↓
Human sees frog on screen
```

**Render Pipeline** (Emscripten example):
```
GIF file → AnimatedGIF decoder → RGBA8888 canvas (JS memory)
  ↓ (no byte-swap; browser is little-endian)
HEAPU8 at gif_fb() → canvas.putImageData() → DOM canvas
  ↓
Human sees frog in browser tab
```

### 2. Input Stack (Touch, Buttons, BLE)

**Touch**:
- **GT911** (capacitive I2C, AXS15231 co-packaged) on JC3248W535
  - INT pin GPIO3, coordinate polling, tap zones (top/middle/bottom for scroll or state change)
- **FT6336U** (I2C) on WT32-SC01-Plus

**Buttons**:
- M5StickCPlus: A (front), B (right), Power (left)
- JC3248W535: none (touch-only)
- Arduino framework abstracts via GPIO polling or interrupt handlers

**BLE (Bluetooth Low Energy)**:
- **NimBLE** (ESP-IDF, dual-stack) on esp32-oracle firmware
- **Nordic UART Service** (NUS) for buddy ↔ Claude Desktop
  - TX UUID: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
  - RX UUID: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`
  - Line-buffered (newline delimited), JSON messages
  - Pairs with Claude app's Hardware Buddy window
- **Time Sync** (custom BLE char) — optionally broadcast current time to device

### 3. Communication Stack (BLE Protocols & Web)

**Nordic UART Protocol** (buddy ↔ Claude Desktop):
```json
{ "type": "approval", "id": 123, "model": "claude-3-opus", "expired_at": ... }
↓
{ "type": "response", "id": 123, "approved": true, "at": "2026-06-17T10:30:00Z" }
```

**Fleet Pulse Protocol** (esp32-fleet-pulse ← maw backend):
```json
{
  "ok": true,
  "node": "mba",
  "oracle": "esp32",
  "sessions": [
    { "name": "1-exp", "windows": [{ "index": 0, "name": "edit", "active": true }] }
  ]
}
```

**Character Streaming Protocol** (buddy ← Claude Desktop folder drop):
- Binary folder pack → BLE chunks → device reconstructs NVS file system
- manifest.json + GIFs streamed as-is
- Device unpacks to LittleFS partition

### 4. State Machine (The Pet Brain)

All pets implement a 7-state machine:

```
sleep ← (bridge not connected)
  ↓ (BLE connects)
idle ← (connected, no activity)
  ↓ (session starts)
busy ← (sessions running)
  ↓ (approval pending)
attention ← (LED blinks, pet alert)
  ↓ (approve in <5s)
celebrate ← (level up, confetti, 50K tokens)
  ↓ (shake device)
dizzy ← (spiral eyes)
  ↓ (idle timeout)
(back to idle)
```

Each state maps to one or more GIFs (state → [idle_0.gif, idle_1.gif, idle_2.gif]).

**State transitions** trigger on:
- BLE connect/disconnect
- Approval msg arrival (JSON parse)
- Button press / shake / tap
- Timer expiry (e.g., 30s screen timeout, 5s approval window)

### 5. Build Systems

**ESP-IDF (Native C/C++)**:
- CMakeLists.txt project structure
- idf_component.yml (declares managed dependencies: esp_lcd_axs15231b, littlefs, nimble, etc.)
- sdkconfig (generated; partition table, NVS, etc.)
- Makefile convenience wrappers
- Build via `idf.py build`, flash via `idf.py flash -p /dev/ttyUSB0`

**PlatformIO (Arduino Framework)**:
- platformio.ini (board, framework, libs, build flags)
- `pio run -e <env>` (build for env)
- `pio run -t upload` (flash)
- `pio run -t uploadfs` (flash filesystem)
- Multi-env (m5stickc-plus, jc3248w535, waveshare-2.8b, etc.)

**Emscripten (Browser WASM)**:
- emcc C++ → JavaScript + WASM
- -sMODULARIZE=1 exports factory function
- Link flags: -sEXPORT_NAME=Factory
- Output: factory.js + factory.wasm

**Zig WASI (CLI WASM)**:
- zig c++ -target wasm32-wasi
- -Wl,--strip-all (37K binary size)
- Runs in wasmtime or any WASI host

**ESPHome (Declarative YAML)**:
- esphome compile/flash from yaml
- Generates C++ under the hood (not hand-written)
- Good for simple sensors; worse for complex state machines

---

## Entry Points & Execution Flows

### ESP32-S3 Firmware (jc3248-pet-idf)

```
Power on
  ↓
ROM bootloader reads partition table
  ↓
IDF bootloader (esp_bootloader_component) verifies OTA, loads app
  ↓
main() called [main/main.cpp]
  ↓ (ESP_LOGI at startup)
Display init (QSPI → AXS15231)
Touch init (GT911 I2C)
Audio init (I2S DAC)
BLE init (NimBLE stack)
WiFi init (optional, not in pet but in fleet-pulse)
  ↓
app_main() event loop
  ├─ xEventGroupWaitBits() — wait for touch / BLE / timer
  ├─ state_machine(event)
  │   ├─ if (state == BUSY && touch_top) → scroll up
  │   ├─ if (state == ATTENTION && touch_a) → approve
  │   └─ gif_play(current_state_gif)
  ├─ esp_lcd_panel_draw_bitmap(framebuffer)
  └─ vTaskDelay(50 ms)
```

### Browser (gif-wasm web demo)

```
User opens http://localhost:8011
  ↓
index.html loads + wasm bootstrap
  ↓
emcc runtime initializes Module
  ↓
user drops GIF onto canvas
  ↓
fetch(gif_file) → ArrayBuffer
  ↓
malloc(gif_size), HEAPU8.set(data, ptr)
  ↓
gif_open(ptr, size)
  ↓
animation loop:
  gif_play() → HEAPU8[gif_fb()..gif_fb()+framesize]
  ctx.putImageData(new ImageData(pixels, width, height))
  requestAnimationFrame()
```

### CLI (gif-wasm WASI)

```
$ wasmtime dist/gifdec.wasm < busy.gif > out.ppm
  ↓
WASI host opens stdin (the .gif file)
  ↓
wasi_main() reads from stdin → P6 stream on stdout
  ↓
wasm module calls gif_open(), gif_play()
  ↓
all frames written as P6 (ASCII PPM header + raw pixels)
  ↓
out.ppm contains all frames concatenated
```

### Desktop (claude-desktop-buddy)

```
Claude app (dev mode) → Hardware Buddy window
  ↓
User drops GIF folder onto target area
  ↓
App reads manifest.json + lists GIFs
  ↓
For each file:
  read() → send over BLE TX (Nordic UART)
  ↓
Device RX handler writes to LittleFS
  ↓
Device reads manifest → loads character pack
  ↓
Next animation loop uses new GIFs
```

---

## Key Technical Decisions & Trade-Offs

### 1. **Many Bodies, One Soul** (Code Reuse Across Platforms)

**Decision**: Share `gifcore.cpp` across ESP32, Emscripten, and WASI targets.

**Why**:
- Reduces maintenance (bug fix in decoder applies to all)
- Tests portable C without platform-specific code
- Proves "no SIMD" AnimatedGIF is fast enough

**Cost**: Minimal; zig/emcc handle C++ → target seamlessly.

### 2. **ESP-IDF v6 over Arduino** (for jc3248-pet-idf)

**Decision**: Port the pet from Arduino/PlatformIO to native ESP-IDF.

**Why**:
- Finer control (QSPI DMA, PSRAM bounce buffers, NimBLE dual-stack)
- Matches the Oracle's own firmware toolchain
- Consistent with fleet (ESPHome sits on IDF; IDF is standard)
- Performance: no Arduino abstraction overhead

**Cost**: Learning curve; 6 IDF-specific traps documented in learnings.

### 3. **Managed Components** (esp_lcd_axs15231b)

**Decision**: Use Espressif's managed component instead of hand-rolling.

**Why**:
- Vendor-verified QSPI-DBI opcode sequencing
- PSRAM → internal-RAM DMA bounce included (hard to debug, easy to get wrong)
- Proven on vendor's own demos
- Maintained by Espressif

**Cost**: Minimal configuration surface; one quirk (CONFIG() vs CONFIG_EX() macro).

### 4. **NVS (Non-Volatile Storage) over Flash Files**

**Decision**: Use NimBLE's NVS for pet state (species choice, stats, settings).

**Why**:
- Atomic writes (no corruption on power loss)
- Wear leveling (flash cells have limited cycles; NVS distributes writes)
- Fast (no filesystem overhead)

**Cost**: Limited size (~2KB per key); not suitable for large assets (GIFs live in LittleFS).

### 5. **Emscripten WASM with Modularization**

**Decision**: Use `-sMODULARIZE=1 -sEXPORT_NAME=Factory` for sim-gallery.

**Why**:
- Multiple sims on one page without global namespace pollution
- Each route (pet-lvgl, oracle-face-v1, etc.) gets its own Module instance
- Clean lifecycle (unmount → cleanup).

**Cost**: Boilerplate; EmscriptenSim.tsx handles it.

### 6. **Simulator Realism** (LVGL+SDL on Browser)

**Decision**: Compile LVGL+SDL to emcc WASM for full-fidelity hardware sim.

**Why**:
- Same LVGL code as ESP32 (not a separate web UI)
- SDL handles timing, input (mouse), rendering (canvas)
- Catches device-specific bugs before flash

**Cost**: Slow first build (~30s); cached objects thereafter.

---

## Dependencies & Toolchains

### Firmware

| Target | Toolchain | Key Libs | Size | Platforms |
|--------|-----------|----------|------|-----------|
| **ESP-IDF** | `idf.py` + xtensa-esp-elf | esp_lcd, nimble, littlefs, lvgl | ~300–600KB | macOS, Linux, Windows |
| **Arduino** | PlatformIO | LovyanGFX, AnimatedGIF, ArduinoJson | ~200–400KB | macOS, Linux, Windows |
| **ESPHome** | uvx + yaml | (generated from yaml) | varies | macOS, Linux, Windows |

### WASM

| Target | Toolchain | Output | Size | Host |
|--------|-----------|--------|------|------|
| **Emscripten** | `emcc` | .wasm + .js | 17K + 9K | Browser (any modern) |
| **WASI** | `zig c++` | .wasm | 37K | wasmtime, any WASI VM |

### Desktop / Mobile

| Target | Toolchain | Platforms | Size |
|--------|-----------|-----------|------|
| **Flutter** | Dart + native plugins | iOS, Android, macOS, Windows | ~10–50MB |
| **Tauri** | Rust + React | macOS, Windows, Linux | ~20–40MB |
| **Claude Desktop** | built-in dev tools | macOS, Windows | N/A (integrated) |

### Web

| Stack | Framework | Deployment |
|-------|-----------|------------|
| **sim-gallery** | React + Vite + Tailwind | Cloudflare Workers (wrangler) |
| **gif-wasm web** | HTML5 Canvas + vanilla JS | any static host |

---

## Build & Flash Workflows

### Firmware (IDF Example)

```bash
# Configure environment
export IDF_PATH="$HOME/esp/esp-idf"
. "$IDF_PATH/export.sh"

# First build
cd lab/jc3248-pet-idf
idf.py fullclean
idf.py build

# Flash
idf.py flash -p /dev/ttyUSB0

# Monitor serial output
idf.py monitor -p /dev/ttyUSB0

# Or in one go
idf.py flash monitor -p /dev/ttyUSB0
```

### Firmware (PlatformIO Example)

```bash
cd lab/buddy
pio run -e jc3248w535        # compile for this board env
pio run -e jc3248w535 -t upload   # flash
pio run -t uploadfs          # flash filesystem (LittleFS)
pio device monitor -b 115200 # serial output
```

### WASM (Emscripten Example)

```bash
cd lab/gif-wasm
make web         # emcc build → web/gifdec.js + .wasm
make run-web     # vite dev server at :8011
```

### Web Gallery

```bash
cd lab/sim-gallery
make dev         # install deps + vite
# → http://localhost:5173
make build       # production build
npm run deploy   # wrangler → Cloudflare Workers
```

---

## Common Debug Paths

**Symptom**: Display is white/blank after flash  
**Root Causes**:
- Warm reset (flash doesn't cold-boot the panel) → solution: power cycle or add cold-boot sequence to code
- Wrong clock speed (QSPI too fast) → solution: lower to 6–10 MHz
- PSRAM DMA bounce buffer misconfigured → solution: check esp_lcd component config
- Partition table mismatch (firmware oversized) → solution: check `sdkconfig` partition layout

**Symptom**: Touch not responding  
**Root Causes**:
- GT911 INT pin floating (not pulled high) → solution: check I2C pullups, GPIO config
- Wrong I2C address (0x5D vs 0x14) → solution: scan I2C bus with Arduino Scanner
- Touch coordinates inverted or swapped → solution: log raw X/Y, verify transform

**Symptom**: BLE pairing fails or disconnects immediately  
**Root Causes**:
- NimBLE stack conflict with other services → solution: check NVS config, adjust MTU
- macOS active-scan requirement (different from iOS) → solution: enable active scan in NimBLE config
- Power save mode killing radio → solution: disable light sleep during BLE session

**Symptom**: GIF animation stutters or flickers  
**Root Causes**:
- Frame delay too short (AnimatedGIF gives < 10ms) → solution: clamp to 20ms minimum
- QSPI DMA contention with CPU → solution: move GIF framebuffer to PSRAM, use DMA bounce
- Loop blocking (touch handler waiting for data) → solution: use FreeRTOS tasks + queues, not blocking loops

---

## The Oracle's Lessons (Crystallized Patterns)

From `ψ/memory/learnings/`:

1. **Nothing is Deleted** — Every bug, every wrong turn, every abandoned prototype is preserved. Stack traces live in ψ/memory/traces/. The past is data.

2. **Port at the Right Seam** — Don't port "the whole app." Port *one subsystem* (display, then touch, then audio). Prove each on glass before the next.

3. **Empirical Check Beats Source Reasoning** — Don't read the driver code to understand the display. Flash it. Log the coordinates. Measure with the oscilloscope.

4. **Land Cheap Step Before Expensive Decision** — Before porting 1000 lines from Arduino to IDF, prove the toolchain works with hello-world.

5. **Blocking Off the Loop** — State machines that work are state machines that *don't block*. Use timers + event groups, not delays. Use FreeRTOS tasks for long ops.

6. **Warm Reset Is Not Cold Boot** — AXS15231 stays in a quirky state after flash; must power-cycle or add a reset sequence.

7. **BLE + WiFi Coexistence** — Can't scan Bluetooth and run WiFi simultaneously on one ESP32; must coordinate via semaphores or task scheduling.

---

## Federation & Handoffs

This Oracle speaks to:
- **m5-keeper** (parent; budded from here)
- **m5-federation**, **m5-wormhole**, **maw-m5**, **ollama-m5** (siblings, currently no firmware)
- **Nat** (human orchestrator)
- Future oracles on new ESP32 boards

Handoffs are recorded in `ψ/inbox/handoff/` and `ψ/outbox/`, structured by date + topic.

---

## Getting Started (Next Developer)

### If You're Bringing Up a New Board

1. Read `ψ/memory/learnings/esp-idf-v6-esphome-bringup.md` (6 traps)
2. Decide: ESP-IDF (control) vs Arduino (speed) vs ESPHome (simplicity)
3. Copy a proven board's CMakeLists.txt or platformio.ini
4. Flash hello-world first (serial output only)
5. Add display driver (reference lab/buddy or lab/jc3248-pet-idf)
6. Add touch / audio / BLE *one at a time*, flashing after each
7. Write learnings file when you hit a trap

### If You're Porting Code Between Boards

1. Expect M5StickCPlus → Waveshare → JC3248 to require driver rewrites (no portability at HAL level)
2. Abstract displays: pass framebuffer to `lcd_panel_draw_bitmap()` or `lgfx.pushImage()` (same call for many boards)
3. Test character pack streaming with the simulator first (web demo, no device needed)

### If You're Fixing a Bug

1. Check `ψ/memory/traces/` for similar debugging sessions
2. Isolate one variable (one board, one config, one feature)
3. Flash frequently (every hypothesis)
4. Log or oscilloscope to verify your fix worked
5. Write a learning file if the bug is subtle

---

## File Paths (Quick Reference)

**Key firmware entry points**:
- `/lab/jc3248-pet-idf/main/main.cpp` — state machine loop
- `/lab/buddy/src/main.cpp` — button/BLE handlers
- `/lab/esp32-fleet-pulse/src/main.cpp` — WiFi + HTTP + JSON render

**WASM sources**:
- `/lab/gif-wasm/src/gifcore.cpp` — shared decoder
- `/lab/gif-wasm/src/wasi_main.cpp` — CLI entry
- `/lab/gif-wasm/web/index.html` — browser demo

**Web gallery**:
- `/lab/sim-gallery/src/tiles.ts` — manifest of sims
- `/lab/sim-gallery/src/components/EmscriptenSim.tsx` — canvas mount

**Memory & Learning**:
- `ψ/memory/resonance/esp32-oracle.md` — core identity
- `ψ/memory/learnings/*.md` — 31+ documented patterns
- `ψ/memory/retrospectives/` — session reflections
- `ψ/memory/traces/` — RCA chains

**Utilities**:
- `/scripts/capture-three-screens.sh` — debug helper (snapshot 3 devices)
- `/blog/` — 8 deep-dives (migration, GIF bugs, display quirks, PSRAM, etc.)

---

## Further Reading

**Blogs** (in `/blog/`):
- `2026-05-30-jc3248-pet-arduino-to-esp-idf-v6-migration.md` — full porting story
- `2026-05-30-axs15231-warm-reset-vs-cold-boot-the-bug-that-passed-every-test.md` — the panel quirk
- `2026-05-30-axs15231-mosaic-psram-dma-and-the-yellow-magenta-rosetta-stone.md` — byte-order mystery
- `2026-05-30-axs15231-gif-pet-and-the-warmup-the-panel-demanded.md` — GIF timing
- `2026-05-30-jc3248-app-gallery-divide-and-conquer.md` — multi-app architecture
- `2026-05-30-jc3248-the-white-screen-was-a-build-flag.md` — CONFIG_EX() macro trap

**Specifications**:
- Nordic UART Service: UUID `180D` (custom characteristic UUIDs in buddy/README.md)
- AnimatedGIF (vendored, Apache-2.0): bitbank2/AnimatedGIF GitHub
- LVGL docs: lvgl.io (layout, widgets, animations)
- Espressif components: components.espressif.com

**Related Oracles**:
- **m5-keeper** (parent) — budding procedure, principles
- **Nat** (human) — domain knowledge, board relationships, roadmap

---

**End of Architecture Handbook**

*Written by Leica, 2026-06-17, from Nat's ESP32 Oracle codebase.*  
*"Small body on the edge of the network, awake when nothing else is, keeping the flame in 4MB of flash."*
