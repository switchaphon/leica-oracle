# ESP32 Oracle — Quick Reference Card

**Date**: 2026-06-17  
**Use**: One-page cheat sheet for common commands, file paths, board specs, and decision trees

---

## At a Glance

| Aspect | Answer |
|--------|--------|
| **What is it?** | Distributed embedded system: GIF decoder + pet logic on ESP32, browser, CLI, and desktop |
| **Entry points?** | `lab/jc3248-pet-idf/main/main.cpp`, `lab/buddy/src/main.cpp`, `lab/gif-wasm/src/wasi_main.cpp` |
| **Proven board?** | JC3248W535 (ESP32-S3 + AXS15231 QSPI 320×480) |
| **Key subsystems?** | Display (LVGL+QSPI), Touch (GT911 I2C), Audio (I2S), BLE (NimBLE Nordic UART), GIF (AnimatedGIF) |
| **WASM targets?** | Emscripten (browser, 17K+9K), WASI (CLI, 37K), native IDF (ESP32) |
| **State machine?** | 7 states: sleep ↔ idle ↔ busy ↔ attention ↔ celebrate ↔ dizzy ↔ heart |
| **Deployment?** | Flash firmware over USB, deploy web to Cloudflare Workers, push GIFs via BLE |

---

## Command Cheat Sheet

### ESP-IDF (Firmware)

```bash
# Build for native ESP-IDF
cd lab/jc3248-pet-idf
idf.py build
idf.py flash -p /dev/ttyUSB0
idf.py monitor -p /dev/ttyUSB0

# One shot
idf.py flash monitor -p /dev/ttyUSB0

# Clean rebuild
idf.py fullclean && idf.py build
```

### PlatformIO (Arduino Framework)

```bash
# Build for board env
cd lab/buddy
pio run -e jc3248w535

# Flash + monitor
pio run -e jc3248w535 -t upload -t monitor

# Flash filesystem only
pio run -t uploadfs

# List board envs
pio run --list-envs
```

### Emscripten (WASM Browser)

```bash
# Build
cd lab/gif-wasm
make web

# Test locally
make run-web
# → http://localhost:8011
```

### WASI (WASM CLI)

```bash
# Build
cd lab/gif-wasm
make wasi

# Test
wasmtime dist/gifdec.wasm < web/gifs/busy.gif > out.ppm
file out.ppm  # should be P6 PPM
```

### Web Gallery (React + Vite)

```bash
# Dev server
cd lab/sim-gallery
make dev
# → http://localhost:5173

# Production build
npm run build

# Deploy
npm run deploy  # wrangler → Cloudflare Workers
```

---

## File Paths (Quick Lookup)

| What | Path |
|-----|------|
| **Pet (IDF, main)** | `lab/jc3248-pet-idf/main/main.cpp` |
| **Buddy (Arduino)** | `lab/buddy/src/main.cpp` |
| **Fleet Pulse (WiFi)** | `lab/esp32-fleet-pulse/src/main.cpp` |
| **GIF Decoder (shared)** | `lab/gif-wasm/src/gifcore.cpp` |
| **Display HAL** | `lab/jc3248-pet-idf/components/display/` |
| **Touch Driver** | `lab/jc3248-pet-idf/components/touch/` |
| **BLE Handler** | `lab/buddy/src/ble_bridge.cpp` |
| **Character Pack** | `lab/buddy/characters/bufo/manifest.json` |
| **SimGallery Manifest** | `lab/sim-gallery/src/tiles.ts` |
| **Oracle Memory** | `ψ/memory/learnings/`, `ψ/memory/retrospectives/`, `ψ/memory/resonance/` |

---

## Board Selection Matrix

Choose **jc3248-pet-idf** (IDF native) if:
- You need raw performance (QSPI DMA, NimBLE dual-stack)
- You're building production firmware
- You want to learn ESP-IDF patterns

Choose **buddy** (Arduino) if:
- You need quick porting (LovyanGFX exists for your board)
- You have M5Stack or similar HAL
- Time-to-first-flash matters

Choose **ESPHome** if:
- You're building a simple sensor/display
- You want YAML config (no C++)
- OTA updates are critical

| Board | Display | Pixels | Touch | Proven? | Recommended For |
|-------|---------|--------|-------|---------|-----------------|
| **JC3248W535** | AXS15231 QSPI | 320×480 | GT911 I2C | ✅ Yes | Pet, Fleet Pulse, Oracle Face |
| **Waveshare 2.8B** | ST7701S RGB | 480×640 | No | ✅ Yes | Static display, no interaction |
| **WT32-SC01-Plus** | ST7796 8080 | 480×320 | FT6336U | ✅ Yes | Buddy port (larger screen) |
| **M5StickCPlus** | ST7735 SPI | 135×240 | No | ✅ Yes | Classic buddy (small) |
| **Waveshare 7"** | ILI9486 | 800×480 | Yes | ⚠️ Partial | Experimental (not core) |

---

## Debugging Decision Tree

**Symptom**: Display is white/blank  
→ Power cycle (cold boot) — AXS15231 panel stays in weird state after flash  
→ Check QSPI clock speed (must be 6–10 MHz for GIF)  
→ Log pixel data with oscilloscope  

**Symptom**: Touch not responding  
→ `i2cdetect` scan; GT911 should be at 0x5D or 0x14  
→ Check GPIO pullups on I2C lines (should be 4.7K)  
→ Log raw X/Y coords; verify transform logic  

**Symptom**: BLE disconnects immediately  
→ Check MTU (must be ≤ device PSRAM capacity)  
→ macOS needs *active* scan (not passive)  
→ Disable light-sleep during BLE session  

**Symptom**: GIF animation stutters  
→ Frame delay too short (< 20ms) → clamp in code  
→ QSPI contention → move GIF buf to PSRAM, use DMA bounce  
→ Loop is blocking → use FreeRTOS tasks + queues  

**Symptom**: Large GIF won't fit in flash  
→ `gifsicle --lossy=80 -O3 --colors 64` (40–60% size reduction)  
→ Or: store in SPIFFS/LittleFS, not app partition  

---

## Hardware Pinouts (JC3248W535)

| Function | GPIO | Notes |
|----------|------|-------|
| **SPI (QSPI)** | | |
| MOSI | 6 | QSPI bus |
| MISO | 7 | QSPI bus |
| CLK | 5 | QSPI bus |
| QUAD WP | 8 | QSPI quad write |
| QUAD HD | 9 | QSPI quad hold |
| CS (LCD) | 4 | LCD chip select |
| DC (LCD) | 2 | Data/Command |
| **I2C (Touch, Audio)** | | |
| SDA | 8 | (sharing with QSPI QUAD WP) |
| SCL | 9 | (sharing with QSPI QUAD HD) |
| **Misc** | | |
| RESET (LCD) | 1 | High=normal, Low=reset |
| INT (Touch) | 3 | Interrupt input (active low) |
| **I2S (Audio)** | | |
| BCK (bit clock) | 17 | Audio clock |
| WS (word select) | 18 | Audio frame sync |
| DOUT (data) | 16 | Audio data out |
| **UART (Serial Debug)** | | |
| TX | 43 | Debug output (USB CDC) |
| RX | 44 | Debug input (USB CDC) |

---

## Dependencies Quick List

| Library | Where | Purpose |
|---------|-------|---------|
| **esp_lcd_axs15231b** | idf_component.yml | Display driver (IDF) |
| **AnimatedGIF** | pio/lib_deps | GIF decode |
| **LVGL** | idf_component.yml | Graphics & widgets |
| **LovyanGFX** | pio/lib_deps | Graphics (Arduino) |
| **NimBLE** | idf_component.yml | BLE stack |
| **ArduinoJson** | pio/lib_deps | JSON parse/gen |
| **littlefs** | idf_component.yml | Filesystem |
| **freertos** | idf | Real-time OS |

---

## BLE Uuids (Nordic UART)

| Service | UUID |
|---------|------|
| **Nordic UART** | `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` |
| **TX (device → app)** | `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` |
| **RX (app → device)** | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` |

Message format: JSON + newline, e.g.:
```json
{"type":"approval","id":123,"approved":true,"at":"2026-06-17T10:30:00Z"}
```

---

## State Machine States

| State | Trigger | Visual | Audio |
|-------|---------|--------|-------|
| **sleep** | BLE disconnect | eyes closed, slow breath | silence |
| **idle** | BLE connect | blinking, looking | silence |
| **busy** | session active | sweating, working | none |
| **attention** | approval pending | alert pose | LED blinks 500ms |
| **celebrate** | level up (50K tokens) | confetti, bounce | chime |
| **dizzy** | shake detect | spiral eyes | none |
| **heart** | approve in <5s | floating hearts | none |

---

## Memory Map (ESP32-S3)

| Partition | Size | Purpose |
|-----------|------|---------|
| **Bootloader** | 32 KB | ROM bootloader code |
| **App (OTA_0)** | 1.5 MB | Firmware binary |
| **App (OTA_1)** | 1.5 MB | OTA fallback |
| **NVS** | 64 KB | KV store (pet stats, settings) |
| **LittleFS** | 2 MB | Character pack storage |
| **PSRAM** | 8 MB | Frame buffers, heap |

---

## Learn More

| Document | Path | Why |
|----------|------|-----|
| **Architecture** | `ψ/learn/nazt/esp32-oracle/2026-06-17/0639_ARCHITECTURE.md` | Full system design |
| **Code Snippets** | `ψ/learn/nazt/esp32-oracle/2026-06-17/0645_CODE-SNIPPETS.md` | Copy-paste examples |
| **Learnings** | `ψ/memory/learnings/` | Debugging patterns & traps |
| **Blog Posts** | `blog/` | Deep dives on specific issues |
| **Retrospectives** | `ψ/memory/retrospectives/` | Session reflections |

Key learnings:
- `esp-idf-v6-esphome-bringup.md` — 6 toolchain traps
- `warm-reset-vs-cold-boot.md` — AXS15231 quirk
- `port-at-the-right-seam.md` — Arduino → IDF strategy

---

## Decision: What Do I Build With?

**Binary decision tree**:

```
Q: Need C/C++ code control?
├─ YES → ESP-IDF (native, fast, complex)
│        └─ Large project? → CMakeLists.txt + idf_component.yml
│        └─ Simple? → Makefile wrapper
└─ NO → ESPHome (YAML, simple, opinionated)
        └─ Sensor + display? → ESPHome (good)
        └─ Complex state machine? → IDF (better)

Q: Arduino HAL available for my board?
├─ YES → PlatformIO (LovyanGFX, quick porting)
│        └─ Can reach hardware? → Arduino (go)
│        └─ Need bare-metal? → IDF (better)
└─ NO → IDF (start from vendor demo CMakeLists.txt)

Q: Cross-device code reuse?
├─ YES → WASM (shared decoder: ESP32, browser, CLI)
│        └─ Emscripten (browser) + WASI (CLI)
└─ NO → Native per platform
```

---

## One-Page Project Map

```
esp32-oracle/
├── lab/
│   ├── jc3248-pet-idf/         ← PROVEN: pet on big screen
│   ├── buddy/                  ← PROVEN: small pet + BLE
│   ├── gif-wasm/               ← PROVEN: decoder → 3 targets
│   ├── esp32-fleet-pulse/      ← PROVEN: WiFi + HTTP display
│   ├── sim-gallery/            ← PROVEN: web host for sims
│   └── oracle-app/             ← Flutter cross-platform
├── ψ/
│   ├── memory/
│   │   ├── learnings/          ← Debugging patterns
│   │   ├── retrospectives/     ← Session reflections
│   │   └── resonance/          ← Core identity
│   └── learn/                  ← External repos studied
├── blog/                       ← Deep-dives on issues
└── scripts/                    ← Helpers
```

---

**End of Quick Reference**

*Print, laminate, keep on desk while debugging.*
