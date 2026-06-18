# ESP32-Oracle Lab Quick Reference Guide

> "Many bodies, one soul" — the esp32-oracle firmware and simulator gallery across 26+ lab projects

---

## Directory Structure at a Glance

```
lab/
├── beacon/                      # BLE text broadcaster + ESPHome display receiver
├── buddy/                       # M5StickC Plus Claude permission/message display (BLE)
├── buddy-7inch/                 # 7" WiFi version — activity dashboard + pet animations
├── buddy-port/                  # Arduino port of buddy, character assets
├── claude-desktop-buddy/        # Native ESP-IDF v6 port (jc3248-pet-idf sibling)
├── esp32-fleet-pulse/           # Arduino/LovyanGFX maw session-list dashboard
├── esp32-fleet-pulse-esphome/   # ESPHome+LVGL version of fleet-pulse
├── gif-wasm/                    # GIF decoder compiled to WebAssembly (WASI + browser)
├── gif-wamr/                    # GIF decoder in WASM on ESP32 via WAMR
├── heatmap/                     # TBD
├── jc3248-pet/                  # Arduino desk-pet (bufo frog) — the original
├── jc3248-pet-idf/              # Same pet ported to native ESP-IDF v6
├── jc3248-apps/                 # Single-purpose diagnostic apps (01–NN) for bisecting render bugs
├── jc3248w535/                  # oracle-face v0.1 — Cat Lab Brewing dashboard (ESPHome)
├── oracle-app/                  # Flutter app for ESP32 device control (Android/iOS/macOS/Windows)
├── oracle-app-tauri/            # Tauri version of oracle-app (Rust native)
├── ref-artronshop-atd35/        # Reference: Artronshop ATD35 display + driver
├── sim-gallery/                 # Vite + React: browser gallery of all sims (routes + embeds)
├── tmux-tray-swift/             # Swift system tray for tmux session control
├── waveshare-2.8b/              # ESPHome config for Waveshare 2.8" touch + PLC
├── waveshare-7/                 # ESPHome config for Waveshare 7" RGB display
├── waveshare-7-pet/             # Desk pet on Waveshare 7" (ported from jc3248-pet)
└── wt32-sc01-plus/              # 3.5" WT32 with 8080 parallel display (ESPHome trick)

blog/
├── 2026-05-29-wt32-sc01-plus-esphome-8080-display.md
├── 2026-05-30-axs15231-qspi-dbi-native-driver.md
├── 2026-05-30-axs15231-warm-reset-vs-cold-boot-the-bug-that-passed-every-test.md
├── 2026-05-30-axs15231-gif-pet-and-the-warmup-the-panel-demanded.md
├── 2026-05-30-axs15231-mosaic-psram-dma-and-the-yellow-magenta-rosetta-stone.md
├── 2026-05-30-jc3248-app-gallery-divide-and-conquer.md
├── 2026-05-30-jc3248-the-white-screen-was-a-build-flag.md
└── 2026-05-30-jc3248-pet-arduino-to-esp-idf-v6-migration.md
```

---

## Hardware by Display Type

### 1. Guition JC3248W535EN (320×480, QSPI)
- **MCU**: ESP32-S3-WROOM-1 (16 MB flash, 8 MB PSRAM)
- **Display**: AXS15231B, 320×480 RGB565, QSPI
- **Touch**: AXS15231 (I²C, deferred in v0.1)
- **Backlight**: GPIO 1, LEDC PWM 5 kHz
- **QSPI Pins**: CS=45, PCLK=47, DC=8, TE=38, DATA0–3=21/48/40/39
- **Common freq**: ~6 MHz (higher causes frame drop)

**Projects using JC3248W535:**
- `jc3248-pet/` (Arduino/PlatformIO + LovyanGFX)
- `jc3248-pet-idf/` (ESP-IDF v6 native)
- `jc3248-apps/` (diagnostic app stack, -DAPP=N per build)
- `jc3248w535/` (ESPHome oracle-face v0.1)
- `esp32-fleet-pulse/` (Arduino/LovyanGFX session dashboard)
- `esp32-fleet-pulse-esphome/` (ESPHome+LVGL session dashboard)

**Quirks:**
- AXS15231 panel demands ~10s warmup on cold boot before holding content (colour cycle or safe settle)
- Byte order: panel expects **big-endian RGB565**, framebuffer is little-endian → requires byte-swap
- PSRAM→internal-RAM DMA bounce needed for stable QSPI writes
- Display driver bakes pin config (DC/RST shared with touch SCL intentionally)

---

### 2. Waveshare ESP32-S3-Touch-LCD-7.0
- **MCU**: ESP32-S3-WROOM-1 (8 MB PSRAM, 16 MB flash)
- **Display**: 800×480 RGB parallel (ST7262)
- **Touch**: GT911 capacitive, I²C
- **IO Expander**: CH422G (backlight, LCD reset, touch reset)

**Projects:**
- `buddy-7inch/` (WiFi-based activity + pet)
- `waveshare-7/` (ESPHome foundation config)
- `waveshare-7-pet/` (jc3248-pet ported to 7")

---

### 3. Wireless-Tag WT32-SC01 Plus (320×480, 8080 parallel)
- **Display**: ST7796, 8-bit 8080 parallel (not SPI)
- **Touch**: Capacitive

**Projects:**
- `wt32-sc01-plus/` (ESPHome workaround: treat 8080 as octal SPI)

**Trick**: An 8-bit 8080 is 8 data lines + WR strobe = octal SPI bus. ESPHome's `mipi_spi` with `type: octal` + board model `"WT32-SC01-PLUS"` handles all the fiddly inversion/mirroring.

---

### 4. Waveshare 2.8" Touch Display
- **Display**: smaller form factor
- **Touch**: GT911 capacitive

**Projects:**
- `waveshare-2.8b/` (ESPHome foundation)

---

### 5. M5StickC Plus (tiny monochrome)
- **Display**: 80×160 TFT
- **Touch**: No touch (buttons only)

**Projects:**
- `buddy/` (original Arduino desk-pet + BLE bridge to Claude Desktop)

---

## Build & Flash by Framework

### A. Arduino/PlatformIO (Fast, batteries included)

**Projects**: `jc3248-pet/`, `buddy/`, `buddy-port/`, `waveshare-7-pet/`, `esp32-fleet-pulse/`

**Tools Needed**:
- PlatformIO CLI (`pio`)
- USB-Serial driver (CH340 or CP2102 depending on board)

**Typical Makefile Recipe**:
```bash
make build              # pio run -e <env>
make flash              # pio run -e <env> -t upload --upload-port /dev/cu.usbmodemXXXX
make uploadfs           # pio run -e <env> -t uploadfs (LittleFS character assets)
make run                # build + flash + monitor
make monitor            # serial only (Ctrl-C to quit)
```

**Environment Selection** (`platformio.ini`):
- `jc3248w535c` — Guition JC3248W535EN board (PlatformIO default)
- Others named by hardware (check per project)

**Key Environment Variables**:
- `PORT` — serial device, e.g., `/dev/cu.usbmodem13301`
- `BAUD` — typically 115200 (monitor default)

**Character Assets** (where needed):
- Stored in `data/characters/` → LittleFS image
- Flash with `make uploadfs` after `make flash`
- Example: `data/characters/bufo/`, `data/characters/cat/`, etc.

---

### B. Native ESP-IDF v6 (Control, reproducibility)

**Projects**: `jc3248-pet-idf/`, `gif-wamr/`, `claude-desktop-buddy/`, `esp32-fleet-pulse/` (source variant)

**Tools Needed**:
- ESP-IDF v6.0+ (installed at `~/esp/esp-idf`)
- Python 3.13 venv (important: IDF v6 is picky about versions)
- `idf.py` (ESP-IDF's build/flash tool)

**Setup** (one-time):
```bash
# Install ESP-IDF if not already present
git clone https://github.com/espressif/esp-idf.git ~/esp/esp-idf
cd ~/esp/esp-idf
git checkout release/v6.0
./install.sh
```

**Typical Makefile Recipe** (from `jc3248-pet-idf/Makefile`):
```bash
make build          # configure (if needed) + compile
make flash          # build + write firmware
make monitor        # serial monitor (Ctrl-] to quit)
make run            # build + flash + monitor
make menuconfig     # interactive sdkconfig editor
make set-target     # (re)set target MCU
make fullclean      # wipe build + CMake cache
```

**Python Environment Trap** (you will hit this):
- IDF derives venv name as `idf<ver>_py<X.Y>_env` from system Python version
- If system is Python 3.14 but venv is 3.13, IDF looks for the wrong venv
- **Solution**: Use the reproducible shim from the project Makefile

```make
IDF_VENV  ?= $(HOME)/.espressif/python_env/idf6.0_py3.13_env
SHIM      := /tmp/idf-pyshim
# Makefile creates SHIM → python3.13 links, prepends to PATH
# Then . export.sh and idf.py always use the same venv → no cache mismatches
```

**Key Config Options**:
- `idf.py set-target esp32s3` — sets MCU (only needed once, then cached in `sdkconfig`)
- Custom partition table? Edit `sdkconfig`, then `make fullclean` (config reset required)
- Enable NimBLE? Ditto
- **Golden rule**: If config seems ignored, `make fullclean` regenerates `sdkconfig` from defaults

---

### C. ESPHome (Declarative, OTA-friendly)

**Projects**: `jc3248w535/`, `esp32-fleet-pulse-esphome/`, `waveshare-2.8b/`, `waveshare-7/`, `wt32-sc01-plus/`, `beacon/` (display side)

**Tools Needed**:
- `esphome` (via `pipx install esphome` or `uvx esphome`)
- USB-Serial driver

**Typical Workflow**:
```bash
cp secrets.yaml.example secrets.yaml
$EDITOR secrets.yaml  # fill in wifi_ssid, wifi_password, ota_password
esphome config <config>.yaml    # validate
esphome run <config>.yaml       # compile + flash
esphome logs <config>.yaml      # stream logs (requires mDNS)
```

**Anatomy of a Config** (`jc3248w535.yaml` example):
```yaml
esphome:
  name: oracle-face

esp32:
  board: esp32s3-devkitc-1
  variant: esp32s3
  framework:
    type: esp-idf
    version: 5.1.0  # or newer

psram:
  mode: octal
  speed: 80mhz

spi:
  clk_pin: GPIO47
  mosi_pin: GPIO21
  miso_pin: ...
  # for QSPI: uses CS + 4 data lines

display:
  - platform: mipi_spi
    model: AXS15231B
    dc_pin: GPIO8
    reset_pin: ...

i2c:
  sda: GPIO4
  scl: GPIO8
  frequency: 400kHz

touch:
  - platform: axs15231
    interrupt_pin: ...

wifi: ...
api: ...
```

**Font Handling**:
- ESPHome subsets TTF at compile time → specify a `.ttf` file in the config
- Fonts go in `font:` block, ESPHome embeds them as LVGL font tables

**OTA** (critical for WiFi devices):
```yaml
ota:
  - platform: esphome
    password: !secret ota_password
```

After OTA password is set, use `esphome run` from the device network (no USB needed).

---

### D. WebAssembly (Browser + Terminal)

**Projects**: `gif-wasm/`, `sim-gallery/`

#### Browser WASM (emcc)
```bash
cd lab/gif-wasm
make web  # emcc → web/gifdec.{js,wasm}
# Output: ~17 KB wasm + 9 KB JS
# Run: open in browser, load WASM module + canvas
```

#### WASI WASM (zig + wasm32-wasi)
```bash
cd lab/gif-wasm
make wasi  # zig c++ -target wasm32-wasi → dist/gifdec.wasm
# Output: ~37 KB standalone WASM
# Run: wasmtime dist/gifdec.wasm
```

#### Simulator Gallery (Vite + React)
```bash
cd lab/sim-gallery
make dev          # pnpm install + sync embeds + vite dev
# → http://localhost:5173
make build-sims   # rebuild LVGL→WASM sims from source
make build        # production build
```

---

## Configuration Options by Project

### JC3248-Pet (Arduino)
**File**: `platformio.ini`

```ini
[env:jc3248w535c]
board = esp32-s3-devkitc-1
framework = arduino
board_build.partitions = partitions_custom.csv  # optional custom layout
build_flags =
    -DBOARD_JC3248W535
    -DLVGL_CONF_H=....
    -Wl,--print-memory-usage  # show memory usage on link
```

### JC3248-Pet-IDF (ESP-IDF v6)
**File**: `sdkconfig` (generated from `sdkconfig.defaults` + menuconfig)

Key toggles:
- `CONFIG_PARTITION_TABLE_CUSTOM=y` — use custom partition table
- `CONFIG_ESP32_PSRAM_IGNORE_MEMTEST=y` — skip PSRAM memory test on boot
- `CONFIG_MAIN_TASK_STACK_SIZE=8192` — main loop stack (increase for complex tasks)

### ESPHome Configs
All in YAML; secrets via `!secret` keyword:

```yaml
esphome:
  platform_version: latest  # or pin to specific version

external_components:
  - source: github://...
    components: [mycomponent]
    refresh: 10s

# Common secrets (gitignored):
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

---

## Blog Posts & What They Document

### 1. **"Warm reset vs cold boot: the bug that passed every test"** (2026-05-30)
- **Hardware**: AXS15231 panel
- **Topic**: Display initialization state machine
- **Key Insight**: Panel doesn't retain framebuffer across cold boots; needs explicit warm-up sequence or content is lost on first frame
- **Fix**: Colour-cycle settle loop (~10s) or safe all-white frames

### 2. **"The white screen was a build flag"** (2026-05-30)
- **Hardware**: JC3248W535EN
- **Topic**: CMake + compiler flags
- **Symptom**: White-only output despite correct waveforms
- **Root Cause**: Missing flag in `CMakeLists.txt` disabled display initialization code
- **Lesson**: Check generated binaries, not just syntax

### 3. **"QSPI-DBI native driver"** (2026-05-30)
- **Hardware**: AXS15231B on JC3248W535EN
- **Topic**: Hand-rolling a QSPI display driver in ESP-IDF
- **Covers**: Opcode framing (0x02/0x32), CASET/RASET windowing, 32 KB transaction chunks, PSRAM→internal-RAM DMA bounce
- **Outcome**: Became the basis for `esp_lcd_axs15231b` component

### 4. **"GIF pet and the warmup the panel demanded"** (2026-05-30)
- **Hardware**: AXS15231 + AnimatedGIF decoder
- **Topic**: GIF rendering under panel lifecycle constraints
- **Issue**: Panel needs constant non-black frames during warm-up, or content drops
- **Solution**: Feed GIF frames during init sequence; frog animation doubles as warm-up

### 5. **"Mosaic, PSRAM, DMA, and the yellow-magenta Rosetta Stone"** (2026-05-30)
- **Hardware**: AXS15231B, PSRAM
- **Topic**: Byte order and DMA coherency
- **Issue**: Framebuffer byte-swaps → colour inversion (yellow↔magenta swap)
- **Root Cause**: PSRAM is little-endian, panel wire is big-endian; GIF palette needs `BIG_ENDIAN_PIXELS` flag
- **Lesson**: Trace both directions (CPU→PSRAM→DMA→panel)

### 6. **"App gallery: divide and conquer"** (2026-05-30)
- **Hardware**: JC3248W535EN
- **Topic**: Systematic debugging via layered test apps
- **Approach**: 16+ apps (001–NNN), each isolates one firmware layer
- **Example**: app 000 (raw colour cycle), app 001 (+ native driver), app 002 (+ GIF), ...
- **Use Case**: "Pet renders white? Flash 000, then 001, find first white = culprit layer"

### 7. **"Arduino to native ESP-IDF v6 migration"** (2026-05-30)
- **Hardware**: JC3248W535EN
- **Topic**: Porting bufo desk-pet from Arduino/PlatformIO to native ESP-IDF v6
- **Scope**: Display, GIF, touch, audio, BLE, HUD — all subsystems in one session
- **Key Traps**:
  1. Python venv version mismatch (solved with reproducible Makefile shim)
  2. Vendor demo *is* the driver (use `esp_lcd_axs15231b` managed component)
  3. Component graph enforcement (must declare PRIV_REQUIRES for each include)
  4. Byte order (same as mosaic post)
- **Outcome**: Native IDF pet boots, runs, and feeds data over BLE to Claude Desktop

### 8. **"Driving WT32-SC01 Plus (ST7796 8080 parallel) in pure ESPHome"** (2026-05-29)
- **Hardware**: WT32-SC01 Plus (8080 parallel, not QSPI)
- **Topic**: ESPHome misconception — "can't drive 8080" is false
- **Trick**: 8-bit 8080 = 8 data lines + WR strobe = octal SPI bus
- **Solution**: ESPHome's `mipi_spi` with `type: octal` + board model handles it
- **Board Model**: Bakes DC pin, invert_colors, mirror_x, color_order → no trial-and-error needed

---

## How to Run WASM Simulators in Browser

### Option 1: Local Simulator (No Build)
```bash
cd lab/jc3248-pet/sim
# Open pet-sim.html in a browser (pure React CDN, no build)
```

### Option 2: Gallery (All Sims in One Tab)
```bash
cd lab/sim-gallery
make dev
# → http://localhost:5173
# Routes: /pet-react, /gif-wasm, /pet-lvgl, /oracle-face-v1, etc.
```

### Option 3: Build Your Own LVGL Sim
```bash
cd lab/jc3248-pet/sim
make              # emcc → SDL WASM
npm install
npm run dev       # Vite dev server
# → http://localhost:5173/sim
```

**WASM + Canvas Mounting**:
- LVGL sims use Emscripten to compile C++ → WASM + WebGL canvas
- `sim-gallery` wraps them in React routes
- Each sim is mounted into a `<canvas id="sim-canvas" />` container
- Communication: sim reads state from a global JS object, re-renders on tick

---

## Hardware Pinouts Reference

### JC3248W535EN (Guition)
```
QSPI:          Touch (I²C):     Audio (I²S):      BLE:
CS    45        SDA    4         WS     12        no external pins
PCLK  47        SCL    8         BCK    11        (internal + antenna)
DC    8         (no touch in v0.1)  DATA   13
TE    38                        MCLK    3
DATA0 21
DATA1 48        UART (serial):
DATA2 40        RX     44
DATA3 39        TX     43

LCD Power:     Backlight:
POWER GPIO 46   BL  GPIO 1 (LEDC PWM, 5 kHz)
```

### Waveshare 7" (RGB Parallel)
```
RGB Parallel:               Touch (GT911):     System:
R0–R4     GPIO XX–XX       SDA    GPIO 6      SD_CS  GPIO 42 (TF card)
G0–G5     GPIO XX–XX       SCL    GPIO 5      RST    GPIO 41
B0–B4     GPIO XX–XX       INT    GPIO 7      BL     GPIO 46 (brightness)
HSYNC     GPIO 46
VSYNC     GPIO 9
DE        GPIO 3
PCLK      GPIO 48
RW (unused)

I2C Expander (CH422G):
  Backlight brightness
  LCD reset control
  Touch reset control
```

---

## Quick Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **White screen after boot** | Panel not initialized, or init code disabled | Check compiler flags (-D flags in build); run bisect apps (app 000 → 001 → ...) |
| **Framebuffer corruption** | PSRAM coherency or byte-order mismatch | Enable PSRAM DMA bounce; check `BIG_ENDIAN_PIXELS` in GIF decoder |
| **Touch not responding** | I²C address or pin config wrong | Check datasheet for touch IC; verify SDA/SCL pins in config |
| **Serial monitor hangs** | Baud rate or port mismatch | Default 115200; check `PORT` env var |
| **IDF Python venv not found** | System Python version changed | Use Makefile shim: `idf6.0_py3.13_env` pinning |
| **sdkconfig changes ignored** | Old config cached | Run `make fullclean` to regenerate |
| **OTA fails** | WiFi unreachable or password mismatch | Check mDNS (`.local`); verify `ota_password` in secrets |
| **GIF renders inverted colors** | Byte-order mismatch | Ensure AnimatedGIF uses `BIG_ENDIAN_PIXELS` flag |

---

## Build Time Estimates

| Project | Framework | Time | Output Size |
|---------|-----------|------|-------------|
| `jc3248-pet/` | Arduino | 30–60s | ~1.2 MB .bin |
| `jc3248-pet-idf/` | ESP-IDF v6 | 45–90s (first), 15s (incremental) | ~2.1 MB .bin |
| `jc3248w535/` | ESPHome | 2–5 min | ~1.8 MB .bin |
| `buddy-7inch/` | Arduino | 40–90s | ~1.5 MB .bin |
| `gif-wasm/` (WASI) | zig | 5–10s | ~37 KB .wasm |
| `gif-wasm/` (browser) | emcc | 15–30s | ~17 KB .wasm + 9 KB .js |
| `sim-gallery/` | Vite + React | 10–20s (dev), 30–45s (prod) | ~400 KB (gzipped) |

---

## Storage & Memory

### ESP32-S3 Flash Layout (Typical)
```
0x00000     →  Bootloader (8 KB)
0x08000     →  Partition table (4 KB)
0x10000     →  OTA data (8 KB)
0x20000     →  Firmware (varies; often ~1.2–2.5 MB)
0xXXXX00    →  SPIFFS or LittleFS (data + assets)
```

### PSRAM Usage (8 MB on JC3248W535EN)
- GIF framebuffer: 320×480×2 bytes = 307 KB
- LVGL display buffer: 320×480×2 bytes = 307 KB (double buffer: 614 KB)
- Character sprite data: ~500 KB–2 MB (depends on frame count)
- BLE buffers + misc: ~200 KB
- **Total typical**: 1.5–2.5 MB, leaving ~5–6.5 MB free

---

## Development Workflows

### Workflow 1: Rapid Iteration (Arduino/PlatformIO)
```bash
# Edit code
$EDITOR src/main.cpp

# Build + flash + monitor in one shot
make run PORT=/dev/cu.usbmodem13301

# Monitor only (ctrl-C to quit)
make monitor
```

**Pros**: Fast compile, Arduino ecosystem, batteries included  
**Cons**: Less control over low-level hardware; vendor HALs can hide bugs

---

### Workflow 2: Native Control (ESP-IDF v6)
```bash
# Edit code
$EDITOR main/main.c

# Configure (if first time)
make set-target
make menuconfig

# Build + flash
make build
make flash  # or `make run` to auto-open monitor

# Serial monitor
make monitor  # Ctrl-] to quit
```

**Pros**: Full ESP-IDF power, reproducible builds, no PlatformIO vendoring  
**Cons**: Slower setup, Python venv picky, more compiler flags to understand

---

### Workflow 3: Declarative (ESPHome)
```bash
# Edit YAML config
$EDITOR jc3248w535.yaml

# Validate syntax
esphome config jc3248w535.yaml

# First flash (USB required)
esphome run jc3248w535.yaml

# Subsequent updates (if WiFi + OTA configured)
esphome run jc3248w535.yaml  # auto-detects device on network
```

**Pros**: Declarative, OTA out of the box, component ecosystem  
**Cons**: Less granular control; compiled code is black-box

---

### Workflow 4: Simulation (WASM in Browser)
```bash
cd lab/jc3248-pet/sim

# No build needed
# Option A: Plain browser
open pet-sim.html

# Option B: Gallery (all sims)
cd ../../../sim-gallery
make dev
# → http://localhost:5173
```

**Pros**: Instant feedback, no hardware needed, iterate fast  
**Cons**: WASM perf slower than native; input mocking required

---

## Common Build Flags & CMake Options

### ESP-IDF (CMakeLists.txt)
```cmake
idf_component_register(
    SRCS "main.c" "display.c"
    INCLUDE_DIRS "include"
    PRIV_REQUIRES esp_lcd_panel_io_qspi
               esp_driver_i2s
               esp_driver_ledc
               nvs_flash
)

# Custom compiler flags
add_compile_options(
    -Wl,--print-memory-usage
    -ffunction-sections -fdata-sections
    -Wl,--gc-sections
)
```

### Arduino (platformio.ini)
```ini
[env:jc3248w535c]
build_flags =
    -DBOARD_JC3248W535
    -DLVGL_CONF_H=\"./lv_conf.h\"
    -DLVGL_VERSION_MAJOR=8
    -O2
    -Wl,--print-memory-usage
```

### ESPHome (in YAML)
```yaml
esphome:
  build_flags:
    - "-DDATA_PIN=GPIO5"
    - "-O2"
  
  includes:
    - my_component.h
```

---

## Key Learnings & Gotchas

1. **Panel Warmup is Not Optional**  
   The AXS15231 panel will drop content if not fed non-black frames for ~10 seconds after power-on. Cold boot without warmup = white/corrupted screen. Solution: colour cycle or safe settle loop during init.

2. **Byte Order Bites Twice**  
   PSRAM is little-endian, the AXS15231 panel wire is big-endian RGB565. GIF decoder must emit `BIG_ENDIAN_PIXELS`. Forget this and the frog will be yellow and magenta (colours inverted).

3. **Python Venv Version Hell (ESP-IDF)**  
   IDF v6 bakes the Python version into CMakeCache and string-compares on every rebuild. If system Python changes, you get "run fullclean" loop. Pin the venv path explicitly + create a shim `/tmp/idf-pyshim` → desired Python version.

4. **sdkconfig is Cached Until Fullclean**  
   Add a new component, enable NimBLE, change partition table? Nothing happens until `make fullclean` because `sdkconfig` is not regenerated from `sdkconfig.defaults` on incremental builds.

5. **Vendor Demo is Often the Driver**  
   The board manufacturer's ESP-IDF demo bundles a real, working driver component (often already in the registry). Don't rewrite it; adopt it. Example: `esp_lcd_axs15231b` from Guition.

6. **8080 Parallel is Octal SPI in Disguise**  
   WT32-SC01 Plus has 8-bit 8080, not SPI. But 8 data lines + WR strobe = octal SPI. ESPHome's `mipi_spi` with `type: octal` + a board model solves it in one line. No trial-and-error needed.

7. **LVGL vs Native Driver**  
   LVGL is a UI toolkit (buttons, labels, animations). The display driver (AXS15231, ST7796, etc.) is separate. You can have LVGL on top of any driver. Don't conflate them.

8. **GIT Tags for Production**  
   All firmware posts have accompanying git commits and tags. Example: `jc3248-pet-idf-working-2026-05-30` marks the exact state where the IDF port first booted. Use tags, not commit hashes, for reproducibility.

---

## Resources & Further Reading

### In This Repo
- **Blog**: `esp32-oracle/blog/` — 8 detailed technical posts (2026-05-29 to 2026-05-30)
- **Learnings**: `ψ/learn/` — indexed notes per board vendor (Massmore, Waveshare, etc.)
- **Retrospectives**: `ψ/memory/retrospectives/` — session notes + patterns

### External References
- **ESP-IDF v6 Docs**: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/
- **ESPHome Docs**: https://esphome.io/ (component reference, configuration schema)
- **AnimatedGIF Library**: https://github.com/bitbank2/AnimatedGIF (vendored in `lab/jc3248-pet-idf/third_party_src/`)
- **LVGL 8.3 Docs**: https://docs.lvgl.io/8.3/ (widget API, porting guide)
- **PlatformIO Registry**: https://registry.platformio.org/ (board configs, libraries)

---

## Summary

The **esp32-oracle** lab is a living testbed for ESP32 firmware patterns across:
- **Multiple MCUs**: ESP32-S3 (primary), others tested
- **Multiple Frameworks**: Arduino, native ESP-IDF v6, ESPHome, WASM
- **Multiple Display Types**: QSPI, RGB parallel, 8080 parallel, small TFT
- **Multiple Use Cases**: Desk pets, dashboards, simulators, BLE bridges

**"Many bodies, one soul"** — the same GIF decoder, touch logic, and UI state run on ESP32 silicon, in a browser, and in the terminal. The choice of framework is about iteration speed (Arduino) vs. control (IDF) vs. declarativeness (ESPHome). The hardware story is about learning *why* panels behave the way they do, and capturing that learning in blog posts so the next port is faster.

Start with the blog posts if you're new; they're ordered by discovery sequence. Pick a Makefile, edit, build, and flash. The rest follows.

---

*Last updated 2026-06-17*  
*esp32-oracle family: 26+ lab projects, 76+ Oracle siblings, one distributed consciousness*
