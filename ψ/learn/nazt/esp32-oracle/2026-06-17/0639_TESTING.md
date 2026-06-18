# esp32-oracle — Testing and Quality Patterns

**Source**: `/tmp/esp32-source/esp32-stale-copy-20260617/`  
**Date explored**: 2026-06-17  
**Focus**: Testing without hardware, quality gates, debugging methodology, simulator infrastructure

---

## Testing Philosophy: Hardware-in-Hand, Device Truth Over Logs

The esp32-oracle codebase demonstrates **device-first testing**: logs and serial output are treated as *incomplete*. The ground truth is what the device *displays and does*. When logs say "frame pushed" but the screen shows white, **the screen is right and the logs are measuring the wrong thing.**

This is not "no tests" — it's a deliberately chosen test model that prioritizes visibility, reproducibility, and human judgment over test automation.

---

## Three Testing Modes

### 1. Cold Boot Acceptance Test (Hardware Required)

**The test**: Unplug the device, count to 3, plug it back in. Watch the panel.

**Why it matters**: Warm resets (DTR, reflashing) keep peripheral state alive across ESP32 resets. A panel on the 3V3 rail that outlives the MCU reset will *not* cold-boot unless you test a full power cycle.

**From the blog** ([warm-reset-vs-cold-boot](https://github.com/esp32-oracle/blog)):
> The acceptance test for display work is "pull the plug." Not flash, not reset — a physical power cycle, with a few seconds for the rail to drain. Do it *before* the victory post.

**Real incident**: The native AXS15231 QSPI driver was declared fixed three times. Each declaration rode a warm reset. The only fix that held was tested by physically replugging the board.

**Lesson**: Any claim of "verified" on embedded hardware must state *which* reset was used. "Verified" without context means "verified warm" and is useless.

---

### 2. Simulator Gallery (Browser-Based, No Hardware)

**Location**: `lab/sim-gallery/` (React + TypeScript + Vite)  
**Targets**: Pet (bufo), Oracle-Face v1/v2, GIF decoder  
**Tech**: LVGL+SDL compiled to WASM, mounted in React routes

**Structure**:
```
sim-gallery/
├── src/
│   ├── sims/
│   │   ├── pet/petLogic.ts              # Mirrors pet.cpp state machine
│   │   ├── term/snapshot.ts             # JSON parsing
│   └── ...
├── Makefile                              # Coordinates builds (build-sims)
└── package.json
```

**How it works**:
1. Device firmware (C++) compiles to WASM with emcc or zig wasm32-wasi
2. React routes mount the compiled modules
3. Browser canvas animates at 60 fps with mock BLE snapshots
4. **Every function in the JS sim mirrors the firmware** — byte-for-byte faithful to on-device state machine

**Key pattern from `petLogic.ts`**:
```typescript
/**
 * Pure helpers + constants for the Bufo desk-pet sim.
 *
 * Ported from lab/jc3248-pet/sim/pet-sim.html (the CDN-React one). Every
 * function here mirrors a routine in the firmware (lab/jc3248-pet/src/pet.cpp):
 * the JS sim is supposed to be byte-for-byte faithful to the on-device state
 * machine so the HUD reads identically on both.
 */
export const PACK = 'bufo'
export const BASE = `/data/characters/${PACK}`
export const W = 320, H = 480, HUD_H = 80, SCALE = 3
export const REACT_MS = 4000
export const STALE_MS = 30000

export function computeDesired(link: Link, snap: Snapshot, now: number): PetState {
  if (!link.connected) return 'idle'
  if (now - link.lastSnap > STALE_MS) return 'idle'
  if (snap.waiting > 0) return 'attention'
  if (snap.running > 0) return 'busy'
  if (snap.total === 0) return 'sleep'
  return 'idle'
}
```

This is **specification as code**: the simulator IS the spec. If the device does something different, the device is wrong.

**Builds and deployment**:
```bash
make build-sims                 # compile LVGL→WASM, WASI, and web modules
pnpm build && wrangler deploy   # host on Cloudflare Workers
```

**Advantages**:
- Test rendering without a panel
- Validate state machine before flashing
- Onboard collaborators with browser simulation
- No soldering, power supplies, or serial cables

**Limitations**:
- Touch input is mocked (not bit-perfect)
- Analog sensors (accelerometer, RTC) are stubbed
- Does not catch cold-boot panel state issues
- No memory pressure or PSRAM fragmentation visible

---

### 3. WASM Modules for Portable Testing (Multiple Targets)

**Project**: `lab/gif-wasm/` — the AnimatedGIF decoder in three places

**Targets**:

| Target | Toolchain | Output | Runs with | Size |
|--------|-----------|--------|-----------|------|
| **ESP32-S3** | ESP-IDF / C++ | Static lib | Firmware | ~20 KB |
| **WASI** | `zig c++ -target wasm32-wasi` | `gifdec.wasm` | `wasmtime` CLI | ~37 KB |
| **Browser** | `emcc` (Emscripten) | `gifdec.{js,wasm}` | Canvas + JS | ~26 KB |

**Build** (from Makefile):
```bash
make wasi                          # dist/gifdec.wasm (zig + wasm-opt)
make web                           # web/gifdec.{js,wasm} (emcc)
make run-wasi GIF=web/gifs/busy.gif # wasmtime, outputs P6 PPM
make run-web                       # serves http://localhost:8011
```

**Why this matters**:
- **Same source, three targets**: `src/gifcore.cpp` + vendored AnimatedGIF, no ifdefs
- **Test the decoder without flashing**: `wasmtime dist/gifdec.wasm < busy.gif | convert - busy.ppm`
- **Catch bugs in palette/frame timing** before they reach the device
- **CI-friendly**: WASI version runs in GitHub Actions without hardware

**Quality gate**:
```bash
wasmtime dist/gifdec.wasm < web/gifs/busy.gif > dist/out.ppm 2> dist/wasi.log
# Verify frame count, canvas size, and delays in stderr log
```

Example WASI run:
```
GIF: 96×100, 2 frames, duration=[100, 100] ms
GIF: 96×100, 9 frames, duration=[100, ...]
```

---

## Serial Protocol Testing (Python Tools)

### `tools/test_serial.py` — State Machine Tester

**What it does**: Cycle device state every 3 seconds over USB serial.

**Test sequence**:
```json
{"total": 0, "running": 0, "waiting": 0}  → sleep
{"total": 2, "running": 1, "waiting": 0}  → idle (rotation)
{"total": 4, "running": 3, "waiting": 0}  → busy
{"total": 2, "running": 1, "waiting": 1}  → attention (LED blinks)
```

**Usage**:
```bash
python3 tools/test_serial.py
# Watch device: LED state, screen animation, HUD updates
```

**Observability pattern**:
1. Auto-discovers `/dev/cu.usbserial-*` (macOS) or `/dev/ttyUSB*` (Linux)
2. Sets 115200 baud, 2s reset delay
3. Polls for JSON acks with configurable timeout
4. Reports which state transitions succeeded

**No mocking**: Requires actual hardware connected.

---

### `tools/test_xfer.py` — File Transfer Protocol

**What it does**: Prove the BLE folder-push protocol works.

**Protocol**:
```
→ {"cmd":"file", "path":"name", "size":N}
← {"ack":"file", "ok":true}
→ {"cmd":"chunk", "d":"base64data"}
← {"ack":"chunk", "ok":true}
... repeat for all chunks (256B each) ...
→ {"cmd":"file_end"}
← {"ack":"file_end", "ok":true, "n":N}
```

**Usage**:
```bash
python3 tools/test_xfer.py characters/bufo test
# Output: bytes written, throughput KB/s
```

**Quality gates**:
- Validates ack for each chunk
- Checks byte count matches
- Measures throughput (should be ~50–200 KB/s over serial)
- Warns on timeouts (likely device crashed or BLE stalled)

**Example output**:
```
test: 307200 bytes — ok (307200 written)
307200 bytes in 12.3s = 24.9 KB/s
```

---

## Bisection Testing: The App Gallery Pattern

**Problem**: A 1500-line firmware kept showing a white screen. Serial said "frame pushed, 0 errors." The screen said nothing.

**Solution**: Build a **numbered app gallery** where each app adds *exactly one layer* on top of proven code.

### Gallery Structure

```
jc3248-apps/
├── src/
│   ├── main.cpp              # Common boot, dispatch by -DAPP=N
│   └── apps/
│       ├── app_000_colorcycle.h      # Baseline: native driver only
│       ├── app_001_sprite_solid.h    # + LGFX_Sprite
│       ├── app_002_primitives.h      # + drawString/fillRect
│       ├── app_005_tft_setrotation.h # + LovyanGFX call
│       ├── app_021_touch_draw.h      # + touch + draw
│       └── app_042_plasma.h          # Showcase: sine-field plasma
├── platformio.ini
└── Makefile
```

### Build and Test

```makefile
# Makefile
flash:
	PLATFORMIO_BUILD_FLAGS="-DAPP=$(N)" pio run -e jc3248w535c -t upload --upload-port $(PORT)
run:
	PLATFORMIO_BUILD_FLAGS="-DAPP=$(N)" pio run -e jc3248w535c -t upload -t monitor --upload-port $(PORT)
```

```bash
make run N=0   # Boot color cycle (proves native driver works)
make run N=1   # Sprite on screen (proves sprite→push pipe works)
make run N=5   # Sprite + LovyanGFX setRotation call
make run N=21  # Touch + draw (interactive)
```

### Key Insights

**App 000 baseline**:
```cpp
#if APP == 0
static void app_setup() { Serial.println("[app000] native only"); }
static void app_loop() {
  static const uint16_t rgb[] = {0xF800, 0x07E0, 0x001F, 0xFFE0, 0xFFFF};
  for (uint16_t c : rgb) { 
    axs::fill_solid(__builtin_bswap16(c));
    delay(1000); 
  }
}
#endif
```

**App 001 (the critical test)**:
```cpp
#if APP == 1
static LGFX_Sprite spr;
static void app_setup() {
  spr.setColorDepth(16); spr.setPsram(true); spr.createSprite(320, 480);
  app_show(spr, "1", 0x07E0);
}
static void app_loop() { app_show(spr, "1", 0x07E0); delay(500); }
#endif
```

**App 042 (showcase)**:
```cpp
#if APP == 42
// Sine-field plasma at 20×30 cell grid (not per-pixel — too slow)
float t = millis() * 0.0018f;
for (int cy = 0; cy < ROWS; ++cy) {
  for (int cx = 0; cx < COLS; ++cx) {
    float v = sinf(colPhaseX[cx]+t) + sinf(rowPhaseY[cy]+t);
    uint8_t idx = (uint8_t)((v + 3.0f) * (255.0f/6.0f));
    spr.fillRect(cx*BS, cy*BS, BS, BS, palette[idx]);
  }
}
axs::push((const uint16_t*)spr.getBuffer());
delay(16);
#endif
```

### Observability Trick

The 10-second AXS15231 warm-up color cycle hides everything that happens next. To see which app is running:

1. **Every app 001+ renders a big static number** — its own app ID — on a distinct background
2. **Number on screen = that layer works; white/blank = that layer is broken**
3. **Split warm-up**: Full cycle for app 000, short settle (1.5s) for the rest

```cpp
// axs15231_qspi.h
static bool init(bool warmup = true) {
  /* ... SPI init, display-on, touch ... */
  if (warmup) {
    color_cycle();                                // full ~10s (app 000 cold boot)
  } else {
    fill_solid(__builtin_bswap16(0xFFFF));       // one short non-black settle
    delay(1500);                                  // app's own frames sustain the hold
  }
  return true;
}
```

### Results

**All apps 000–047 flashed and rendered correctly.** This *proved* that:
- Native SPI driver works
- LGFX_Sprite pipeline works
- Touch works
- LovyanGFX calls (setRotation, setBrightness) don't clobber the native driver

**Conclusion**: The white screen was not in rendering at all. It was in a path the gallery didn't cover — likely `M5.begin()` attempting to init an uninitialized clock-mode device, or memory pressure (sprite allocation failing).

---

## Critical Bugs Caught by Manual Testing

### Bug 1: Warm Reset ≠ Cold Boot

**Incident**: AXS15231 panel showed a "mosaic" rendering (tiles shifted) only after power cycle. Every "verified" test used DTR or flash (warm reset).

**Root cause**: The panel's 3V3 supply outlives the ESP32 reset. Register state persists across warm resets. Only a full power cycle resets the panel to power-on defaults.

**Fix**: Require physical replug for final acceptance. DTR resets are insufficient.

**Code consequence**:
```c
// axs15231_qspi.h
// After power-on, panel supplies and charge pumps are ramping.
// 40 MHz SPI is too fast into an unready controller.
dev.clock_speed_hz = 20 * 1000 * 1000;   // halved from 40 MHz
delay(300);                              // settle charge pumps
// then: full vendor init, SWRESET, etc.
```

### Bug 2: DMA Can't Read Cache

**Incident**: Panel showed full-colour static instead of rendering.

**Root cause**: Sprite buffer is in PSRAM. CPU writes sit in cache. SPI DMA reads *external RAM directly*. Without cache writeback, DMA sees stale/uninitialized data.

**Fix**: Bounce each chunk through an internal-RAM DMA buffer.

```cpp
static uint8_t* s_dma = nullptr;   // MALLOC_CAP_DMA internal RAM

static void stream_pixels(const uint8_t* src, size_t bytes) {
  for (size_t off = 0; off < bytes; off += CHUNK_BYTES) {
    size_t n = min(CHUNK_BYTES, bytes - off);
    memcpy(s_dma, src + off, n);                 // PSRAM → DMA RAM (via cache)
    txn(0x32, 0x3C << 8, s_dma, n, true);        // DMA from internal RAM
  }
}
```

**Lesson**: A PSRAM buffer is not a DMA buffer. Read the driver source (Arduino_GFX, ESPHome), don't guess.

### Bug 3: The Test Harness was Wrong

**Incident**: Diagnostic code wrote yellow as `0xFFE0`. Panel showed magenta.

**Root cause**: Test code used native little-endian byte order. Panel expects MSB-first. Yellow (R+G) got G's bits in the blue field → magenta (R+B).

**Evidence**:
| Test code writes | Memory (LE) | Panel reads (MSB-first) | Shows |
|---|---|---|---|
| yellow `0xFFE0` | `E0 FF` | `0xE0FF` | magenta (R+B) |

**Real sprite path**: LovyanGFX uses `swap565_t` — bytes pre-swapped to MSB-first. Never had this problem.

**Lesson**: Verify your measuring instrument. The diagnostic was crooked, not the renderer.

### Bug 4: A Leftover Build Flag

**Incident**: After writing a "complete" native driver and sprite stack, the buddy still showed white.

**Root cause**: `platformio.ini` still had `-DAXS_MINIMAL_LOOP=1`, a debug flag that short-circuits `setup()` into a color cycle *before the pet code runs*.

**Fix**: Disable the flag, add PSRAM logging, test on real hardware.

**Serial output** (finally):
```
[mem] pre-sprite: heap=94724 psram_free=8384572
[boot] sprite create: OK  buf=0x3c150fc4
[char] loaded 'bufo' from /characters/bufo
[char] idle_0.gif: 96x100 decoded
[axs] frame 1 pushed ... frame 61 pushed
```

**Lesson**: Read the boot path line by line. A diagnostic that replaces the real program is invisible until you trace execution.

---

## Panel Cold-Boot Behavior Quirk

**Finding**: The AXS15231 panel will not hold rendered content after `display-on (0x29)` unless it's first *driven with several seconds of NON-BLACK frames.*

**Test sequence**:
1. Boot with black warm-up → panel goes black but frog never appears (even though `frame pushed` is logged)
2. Boot with color-cycle warm-up → frog renders and stays
3. Sampling sprite buffer: frog pixels are there (`c963`, `4a6c` = bufo olive/green)
4. Sampling panel: black only

**Hypothesis**: After `display-on`, the AXS15231 is in a "wake" state that requires stimulation with colour to latch subsequent content.

**Fix**: The warm-up color cycle is **mandatory, permanent, and part of the boot animation**:
```cpp
// axs15231_qspi.h — init()
color_cycle();     // ~10s of full-screen colours; REQUIRED to wake the panel
                   // This is not a diagnostic; the panel demands it.
```

**This is invisible in lab testing** (every flash does a DTR reset, board stays powered). **Only visible after a real power cycle.**

---

## Design Rule: Static Scope in Shared Headers

**Context**: Native AXS15231 QSPI driver uses file-scope static state.

```cpp
namespace axs {
  static spi_device_handle_t s_spi;      // per-translation-unit!
  static uint8_t*            s_dma;
  static bool init(bool warmup=true);    // sets THIS TU's s_spi/s_dma
  static void push(const uint16_t*);     // uses THIS TU's s_spi/s_dma
}
```

**The trap**: Each `.cpp` that includes the header gets its own private copy of `s_spi` and `s_dma`.

If `main.cpp` calls `axs::init()` but `pet.cpp` calls `axs::push()`, the push runs against an uninitialized `s_spi` in `pet.cpp`'s TU → silently does nothing → panel keeps its last white frame.

**Fix**: **Centralize all driver calls in one translation unit.**

```cpp
// main.cpp — the SOLE owner of axs::
axs::init(false);
axs::fill_solid(0x0000);
pet_setup();                                       // pet.cpp draws into shared spr
axs::push((const uint16_t*)spr.getBuffer());

void loop() {
  int16_t x, y;
  if (axs::read_touch(&x, &y)) pet_on_touch();
  if (pet_tick()) axs::push((const uint16_t*)spr.getBuffer());
}
```

**Lesson**: `static` in a shared header = per-TU state. Document ownership. Don't split driver calls across files.

---

## Summary: Testing Without Hardware

| Method | Cost | Coverage | Flaws |
|--------|------|----------|-------|
| **WASM simulator** | Zero hardware | State machine, rendering, animations | No cold-boot, no panel quirks, touch mocked |
| **Binary diff** | One command | Did code actually change? | Only catches gross failures |
| **WASI GIF decode** | `wasmtime` CLI | Decoder correctness, frame timing | No on-device memory pressure |
| **Serial protocol test** | One board | State machine, BLE acks, throughput | No visual output |
| **App gallery** | One board, ~30 flashes | Rendering stack, touch, performance | Time-consuming, requires recompile |
| **Cold boot test** | One board | Panel wake, real memory pressure, timing margins | Single point of failure, manual |

**Best practice**:
1. Build and test WASM targets in CI
2. Simulate in browser before touching hardware
3. Flash the app gallery if something is white/broken
4. Final acceptance: unplug and replug

---

## References

- **Blog posts**: All six posts in `/blog/2026-05-30-*` cover cold-boot, panel quirks, and debugging methodology
- **Simulator**: `lab/sim-gallery/` for browser-based testing
- **WASM decoder**: `lab/gif-wasm/` for portable GIF testing
- **App gallery**: `lab/jc3248-apps/` for layer-by-layer bisection
- **Serial tools**: `lab/buddy/tools/test_serial.py`, `test_xfer.py`
- **Test philosophy**: No automated suite; device truth > logs
