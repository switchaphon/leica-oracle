# ESP32 Oracle — Code Snippets Deep-Dive
**Date**: 2026-06-17  
**Focus**: ESPHome YAML configs, WASM GIF decoder, LVGL widget setup, build system, C/Rust code  

---

## 1. ESPHome YAML Configs

### 1.1 Fleet-Pulse Dashboard (fleet-pulse.yaml)

**Purpose**: ESP32-S3 + AXS15231 QSPI display (320×480) polls maw `/api/ls` every 5s, renders tmux session list via LVGL.

**Key sections**:

```yaml
# HTTP client for the maw backend
http_request:
  id: http_client
  timeout: 12s
  verify_ssl: false
  useragent: esp32-fleet-pulse/1.0
  buffer_size_rx: 1024  # esp-idf http rx buffer (default 512)

# QSPI bus for AXS15231
spi:
  - id: lcd_spi
    type: quad
    clk_pin: 47
    data_pins: [21, 48, 40, 39]

# Backlight PWM on GPIO 1 @ 5kHz
output:
  - platform: ledc
    pin: 1
    id: backlight_pwm
    frequency: 5000Hz

# Display: AXS15231 over QSPI
display:
  - platform: mipi_spi
    model: AXS15231
    spi_id: lcd_spi
    cs_pin: 45
    dimensions: {width: 320, height: 480}
    data_rate: 40MHz
    update_interval: never  # manual update via lambda
```

**LVGL setup** (16 session rows + header):
```yaml
lvgl:
  bg_color: 0x000000
  pages:
    - id: main_page
      widgets:
        - label: {id: hdr, align: TOP_LEFT, x: 6, y: 4, text_font: montserrat_16, text_color: 0x07E7FF}
        - label: {id: row_0, align: TOP_LEFT, x: 6, y: 28, text_font: montserrat_14, text_color: 0x888888}
        # ... row_1 through row_15
```

**HTTP polling lambda** (5s interval, JSON parse, label update):
```cpp
interval:
  - interval: 5s
    then:
      - http_request.get:
          url: ${backend_url}
          capture_response: true
          max_response_buffer_size: 8192
          on_response:
            then:
              - lambda: |-
                  json::parse_json(body, [](JsonObject root) -> bool {
                    lv_obj_t *rows[16] = {id(row_0), /* ... */, id(row_15)};
                    std::string node = root["node"] | "?";
                    std::string oracle = root["oracle"] | "?";
                    JsonArray sessions = root["sessions"].as<JsonArray>();
                    
                    char hdrbuf[96];
                    snprintf(hdrbuf, sizeof(hdrbuf), "%s/%s  %d sessions",
                             node.c_str(), oracle.c_str(), (int)sessions.size());
                    lv_label_set_text(id(hdr), hdrbuf);
                    
                    int i = 0;
                    for (JsonObject sess : sessions) {
                      if (i >= 16) break;
                      std::string name = sess["name"] | "?";
                      JsonArray windows = sess["windows"].as<JsonArray>();
                      bool active = false;
                      for (JsonObject w : windows) {
                        if (w["active"] | false) { active = true; break; }
                      }
                      char rowbuf[64];
                      snprintf(rowbuf, sizeof(rowbuf), "%s%s  %dw",
                               active ? "* " : "  ", name.c_str(), (int)windows.size());
                      lv_label_set_text(rows[i], rowbuf);
                      lv_obj_set_style_text_color(rows[i],
                          lv_color_hex(active ? 0xFFFFFFFF : 0x888888), 0);
                      i++;
                    }
                    for (; i < 16; i++) lv_label_set_text(rows[i], "");
                    return true;
                  });
```

---

### 1.2 Oracle Terminal (terminal.yaml)

**Purpose**: LVGL monospace terminal viewer for tmux pane capture (`/api/capture`). Renders last-N lines, ANSI color → LVGL recolor markup, Thai text support.

**Key hardware setup** (same as fleet-pulse):
```yaml
esp32: {board: esp32-s3-devkitc-1, variant: esp32s3, flash_size: 16MB}
psram: {mode: octal, speed: 80MHz}
spi: {- id: lcd_spi, type: quad, clk_pin: 47, data_pins: [21, 48, 40, 39]}
output: {- platform: ledc, pin: 1, id: backlight_pwm, frequency: 25000Hz}
display: {- platform: mipi_spi, model: AXS15231, cs_pin: 45, dimensions: {width: 320, height: 480}}
```

**Dynamic globals** (pane selection, interval, viewport):
```yaml
globals:
  - id: target
    type: std::string
    initial_value: '"52-esp32:esp32-exp"'
  - id: interval_s
    type: int
    initial_value: '3'
  - id: lines_n
    type: int
    initial_value: '24'
  - id: col_off
    type: int
    initial_value: '1'  # skip leading marker char
```

**Pane dropdown select** (web UI):
```yaml
select:
  - platform: template
    id: pane_select
    options:
      - "52-esp32:esp32-oracle"
      - "52-esp32:esp32-exp"
      - "04-homekeeper:homekeeper-oracle"
      - "11-odin:odin-oracle"
      # ... more panes
    on_value:
      then:
        - lambda: 'id(target) = x;'
        - script.execute: fetch_pane
```

**Font setup** (JetBrains Mono + Thai glyphs via gfonts):
```yaml
font:
  - file: { type: gfonts, family: "JetBrains Mono" }
    id: term_sm
    size: 11
    bpp: 4
    glyphsets: [GF_Latin_Kernel]
    extras:
      - file: { type: gfonts, family: "Sarabun" }
        glyphs: ["ก","ข","ค",...,"๙","๚","๛"]
  # term_md (14) and term_lg (16) follow same pattern
```

**LVGL label with monospace rendering**:
```yaml
lvgl:
  pages:
    - id: main_page
      widgets:
        - label:
            id: hdr
            align: TOP_LEFT
            x: 4
            y: 2
            text_color: 0x07E7FF
        - label:
            id: term
            align: TOP_LEFT
            x: 2
            y: 20
            width: 316
            height: 456  # stable viewport for CLIP
            text_font: term_md
            text_color: 0xC8C8C8
            recolor: true  # enable #RRGGBB ..# markup
            long_mode: CLIP
```

**Fetch pane script** (ANSI→LVGL markup, UTF-8 Thai, emoji color mapping):
```cpp
script:
  - id: fetch_pane
    then:
      - http_request.get:
          url: !lambda 'return std::string("${capture_base}") + id(target);'
          capture_response: true
          max_response_buffer_size: 49152  # up to 24KB capture spike
          on_response:
            then:
              - lambda: |-
                  static const uint32_t BASIC[8]  = {0x202020,0xCD4848,0x5CB85C,0xD1B357,0x5C94DB,0xB870C7,0x57B8BD,0xC7C7C7};
                  static const uint32_t BRIGHT[8] = {0x737373,0xF56C66,0x80E080,0xF5DB70,0x80B8F5,0xDB94EB,0x80E6EB,0xF5F5F5};
                  
                  std::string content = root["content"] | "";
                  int want = id(lines_n);
                  
                  // Slice last N lines
                  int nl = 0; size_t start = 0;
                  for (size_t i = content.size(); i-- > 0; ) {
                    if (content[i] == '\n') { if (++nl >= want) { start = i + 1; break; } }
                  }
                  const char *p = content.c_str() + start;
                  
                  // ANSI SGR → LVGL recolor: #RRGGBB ..# markup
                  std::string out; out.reserve(content.size() - start + 256);
                  uint32_t cur = 0, span = 0; int lineCol = 0, coff = id(col_off);
                  
                  while (*p) {
                    unsigned char c = (unsigned char) *p;
                    
                    // ESC handling: extract SGR codes
                    if (c == 0x1B) {
                      p++;
                      if (*p == '[') {
                        p++;
                        int code[12], n = 0, v = 0;
                        while (*p && !(*p >= '@' && *p <= '~')) {
                          if (*p >= '0' && *p <= '9') { v = v*10 + (*p-'0'); }
                          else { if (n < 12) code[n++] = v; v = 0; }
                          p++;
                        }
                        char f = *p; if (*p) p++;
                        
                        if (f == 'm') {  // SGR finish
                          if (n == 0) cur = 0;  // reset
                          for (int i = 0; i < n; i++) {
                            int cc = code[i];
                            if (cc == 0 || cc == 39) cur = 0;
                            else if (cc >= 30 && cc <= 37) cur = BASIC[cc-30];
                            else if (cc >= 90 && cc <= 97) cur = BRIGHT[cc-90];
                            else if (cc == 38 && i+2 < n && code[i+1] == 5) {  // 256-color
                              int x = code[i+2];
                              if (x < 8) cur = BASIC[x];
                              else if (x < 16) cur = BRIGHT[x-8];
                              else if (x < 232) {
                                int y = x - 16; int L[6] = {0,95,135,175,215,255};
                                cur = (L[(y/36)%6]<<16) | (L[(y/6)%6]<<8) | L[y%6];
                              } else {
                                int g = 8 + (x-232)*10;
                                cur = (g<<16) | (g<<8) | g;
                              }
                              i += 2;
                            } else if (cc == 38 && i+4 < n && code[i+1] == 2) {  // RGB
                              cur = (code[i+2]<<16) | (code[i+3]<<8) | code[i+4];
                              i += 4;
                            }
                          }
                        }
                        continue;
                      }
                      continue;
                    }
                    
                    // UTF-8 + Thai detection
                    if (c >= 0x80) {
                      const char *us = p;
                      uint32_t cp = c; int len = 1;
                      if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; len = 2; }
                      else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; len = 3; }
                      else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; len = 4; }
                      
                      for (int k = 1; k < len && p[k]; k++)
                        cp = (cp << 6) | ((unsigned char) p[k] & 0x3F);
                      
                      ulen = len; p += len;
                      
                      if (cp >= 0x0E00 && cp <= 0x0E7F) {  // Thai: pass raw UTF-8
                        isThai = true;
                      } else if (cp == 0x2500 || cp == 0x2501) ch = '-';  // box drawing
                      else if (cp == 0x2502 || cp == 0x2503) ch = '|';
                      else if (cp >= 0x250C && cp <= 0x254B) ch = '+';
                      else if (cp == 0x2713 || cp == 0x2714 || cp == 0x2705)  // ✓✅
                        { ch = 'v'; fcol = 0x33CC55; }  // green
                      else if (cp == 0x2717 || cp == 0x2718 || cp == 0x274C)  // ✗❌
                        { ch = 'x'; fcol = 0xE03B3B; }  // red
                      else if (cp == 0x1F7E2 || cp == 0x1F7E9)  // 🟢🟩
                        { ch = '*'; fcol = 0x33CC55; }
                      else if (cp == 0x1F534 || cp == 0x1F7E5)  // 🔴🟥
                        { ch = '*'; fcol = 0xE03B3B; }
                      else if (cp == 0x1F7E1 || cp == 0x1F7E8)  // 🟡🟨
                        { ch = '*'; fcol = 0xE8C547; }
                      else ch = ' ';
                    } else { ch = (char) c; p++; }
                    
                    // Clipping + render
                    int vis = lineCol++ - coff;
                    if (vis >= 0 && vis < 80) {
                      uint32_t want = fcol ? fcol : cur;
                      if (span != want) {
                        if (span) out += "#";
                        if (want) {
                          char h[10];
                          snprintf(h, sizeof(h), "#%06X ", (unsigned) want);
                          out += h;
                        }
                        span = want;
                      }
                      if (isThai) {
                        out.append(us, ulen);
                      } else if (ch == '#') {
                        out += "##";
                      } else {
                        out += ch;
                      }
                    }
                  }
                  
                  if (span) out += "#";
                  
                  // Bottom-pin: pad short captures
                  int fill = id(lines_n);
                  int have = 1; for (char c : out) if (c == '\n') have++;
                  if (have < fill)
                    out.insert(0, std::string(fill - have, '\n'));
                  
                  static std::string last;
                  if (out != last) {
                    last = out;
                    lv_label_set_text_static(id(term), last.c_str());  // static: LVGL points, no copy
                  }
```

---

## 2. WASM GIF Decoder

### 2.1 Build System (gif-wasm/Makefile)

```makefile
# gif-wasm — AnimatedGIF → WASI (zig) + WASM (emcc)
#   make            # build both
#   make wasi       # dist/gifdec.wasm (zig + wasm-opt)
#   make web        # web/gifdec.{js,wasm} (emcc)
#   make run-wasi   # decode a GIF -> dist/out.ppm with wasmtime
#   make run-web    # serve browser demo at :8011

GIF     ?= web/gifs/busy.gif
VENDOR   = vendor/AnimatedGIF
CORE     = src/gifcore.cpp $(VENDOR)/AnimatedGIF.cpp
CFLAGS   = -O2 -DNO_SIMD -fno-exceptions -fno-rtti -I $(VENDOR) -include src/compat.h
EXPORTS  = _gif_open,_gif_width,_gif_height,_gif_play,_gif_fb,_gif_reset,_gif_close,_malloc,_free
DEPS     = src/gifcore.h src/compat.h $(CORE)

# ---- WASI: true wasm32-wasi (zig); -g0 strips for smaller output ----
wasi: dist/gifdec.wasm
dist/gifdec.wasm: src/wasi_main.cpp $(DEPS)
	@mkdir -p dist
	zig c++ -target wasm32-wasi -g0 -Wl,--strip-all $(CFLAGS) src/wasi_main.cpp $(CORE) -o $@
	@command -v wasm-opt >/dev/null 2>&1 && wasm-opt -Oz $@ -o $@.opt && mv $@.opt $@ || echo "(wasm-opt skipped)"
	@ls -la $@

# ---- WASM: browser library (emcc), exports gif_* for JS ----
web: web/gifdec.js
web/gifdec.js: $(DEPS)
	emcc $(CFLAGS) $(CORE) --no-entry \
	  -sEXPORTED_FUNCTIONS=$(EXPORTS) -sEXPORTED_RUNTIME_METHODS=HEAPU8 \
	  -sALLOW_MEMORY_GROWTH=1 -sMODULARIZE=1 -sEXPORT_NAME=GifModule -o $@
	@ls -la web/gifdec.js web/gifdec.wasm

# ---- WASI runtime: stdin → stdout PPM ----
run-wasi: wasi
	@mkdir -p dist
	wasmtime dist/gifdec.wasm < $(GIF) > dist/out.ppm 2> dist/wasi.log; \
	  tail -3 dist/wasi.log; ls -la dist/out.ppm

# ---- Browser demo server ----
run-web: web
	@echo "open http://localhost:8011/"
	python3 -m http.server 8011 -d web

clean:
	rm -rf dist web/gifdec.js web/gifdec.wasm
```

### 2.2 GIF Decoder Header (gifcore.h)

**Framework-agnostic C interface, shared by WASI CLI + browser build**:

```c
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Open GIF from memory buffer, allocate + clear RGBA canvas.
 * Returns 0 on success, <0 on error. Call gif_close() when done. */
int gif_open(const uint8_t *data, int len);

int gif_width(void);   /* canvas width (0 before successful open) */
int gif_height(void);  /* canvas height */

/* Decode the NEXT frame into canvas. Returns 1 = more frames,
 * 0 = last frame, -1 = error. *delay_ms = display duration. */
int gif_play(int *delay_ms);

/* Pointer to RGBA8888 canvas (width*height*4 bytes), valid until gif_close().
 * In browser build, this is a byte offset into wasm heap. */
const uint8_t *gif_fb(void);

void gif_reset(void);   /* seek back to frame 0 (loop animation) */
void gif_close(void);   /* free canvas + GIF data */

#ifdef __cplusplus
}
#endif
```

### 2.3 GIF Decoder Core (gifcore.cpp)

**Single-instance state, scanline callback writes RGBA8888 canvas**:

```cpp
#include "gifcore.h"
#include <AnimatedGIF.h>
#include <stdlib.h>
#include <string.h>

namespace {
  struct Core {
    AnimatedGIF gif;
    uint8_t *data = nullptr;   // copied GIF bytes
    uint8_t *fb   = nullptr;   // RGBA8888 canvas (persistent across frames)
    int      w = 0, h = 0;
    bool     open = false;
  };
  Core g;
  
  /* One decoded scanline → RGBA canvas. Compose: transparent pixels keep
   * the previous frame (handles "leave in place" disposal). RGB565 LE → RGB888
   * with low-bit replication. */
  void drawCb(GIFDRAW *d) {
    if (!g.fb) return;
    const int y = d->iY + d->y;
    if (y < 0 || y >= g.h) return;
    
    const uint16_t *pal = d->pPalette;     // RGB565 LE palette
    const uint8_t  *src = d->pPixels;      // scanline indices
    const uint8_t   t   = d->ucTransparent;
    const bool      hasT = d->ucHasTransparency;
    uint8_t *row = g.fb + (size_t)y * g.w * 4;
    
    for (int x = 0; x < d->iWidth; x++) {
      const int cx = d->iX + x;
      if (cx < 0 || cx >= g.w) continue;
      
      const uint8_t idx = src[x];
      if (hasT && idx == t) continue;  // transparent → compose over previous frame
      
      const uint16_t p = pal[idx];  // host-order RGB565
      // Expand 5/6 bits to 8 bits via replication
      uint8_t r = (uint8_t)((p >> 11) & 0x1F); r = (uint8_t)((r << 3) | (r >> 2));
      uint8_t g = (uint8_t)((p >>  5) & 0x3F); g = (uint8_t)((g << 2) | (g >> 4));
      uint8_t b = (uint8_t)( p        & 0x1F); b = (uint8_t)((b << 3) | (b >> 2));
      
      uint8_t *px = row + (size_t)cx * 4;
      px[0] = r; px[1] = g; px[2] = b; px[3] = 255;  // RGBA
    }
  }
}

extern "C" {

int gif_open(const uint8_t *data, int len) {
  gif_close();
  if (!data || len <= 0) return -1;
  
  g.data = (uint8_t *)malloc((size_t)len);
  if (!g.data) return -1;
  memcpy(g.data, data, (size_t)len);
  
  g.gif.begin(GIF_PALETTE_RGB565_LE);
  if (!g.gif.open(g.data, len, drawCb)) {
    free(g.data); g.data = nullptr; return -2;
  }
  
  g.w = g.gif.getCanvasWidth();
  g.h = g.gif.getCanvasHeight();
  if (g.w <= 0 || g.h <= 0 || (long)g.w * g.h > 8L * 1024 * 1024) {
    gif_close(); return -3;  // too large
  }
  
  g.fb = (uint8_t *)malloc((size_t)g.w * g.h * 4);
  if (!g.fb) { gif_close(); return -1; }
  
  memset(g.fb, 0, (size_t)g.w * g.h * 4);  // start transparent-black
  g.open = true;
  return 0;
}

int gif_width(void)  { return g.w; }
int gif_height(void) { return g.h; }

int gif_play(int *delay_ms) {
  if (!g.open) return -1;
  int d = 0;
  int r = g.gif.playFrame(false, &d);  // false = don't pace; we drive timing
  if (delay_ms) *delay_ms = d;
  return r;  // 1 = more, 0 = last, -1 = error
}

const uint8_t *gif_fb(void) { return g.fb; }

void gif_reset(void) { if (g.open) g.gif.reset(); }

void gif_close(void) {
  if (g.open) { g.gif.close(); g.open = false; }
  if (g.fb)   { free(g.fb);   g.fb   = nullptr; }
  if (g.data) { free(g.data); g.data = nullptr; }
  g.w = g.h = 0;
}

}  // extern "C"
```

### 2.4 WASI CLI (wasi_main.cpp)

**Reads GIF from stdin, emits PPM stream to stdout (wasmtime host)**:

```cpp
#include "gifcore.h"
#include <stdio.h>
#include <stdlib.h>

static uint8_t *read_all_stdin(long *out_len) {
  size_t cap = 1 << 16, len = 0;
  uint8_t *buf = (uint8_t *)malloc(cap);
  if (!buf) return nullptr;
  
  for (;;) {
    if (len == cap) {
      cap *= 2;
      uint8_t *nb = (uint8_t *)realloc(buf, cap);
      if (!nb) { free(buf); return nullptr; }
      buf = nb;
    }
    size_t n = fread(buf + len, 1, cap - len, stdin);
    len += n;
    if (n == 0) break;
  }
  *out_len = (long)len;
  return buf;
}

static void write_ppm(int w, int h, const uint8_t *rgba) {
  printf("P6\n%d %d\n255\n", w, h);
  // PPM = RGB (drop alpha from RGBA)
  for (long i = 0; i < (long)w * h; i++)
    fwrite(rgba + i * 4, 1, 3, stdout);
}

int main(void) {
  long len = 0;
  uint8_t *gif = read_all_stdin(&len);
  if (!gif || len <= 0) {
    fprintf(stderr, "gifdec: no GIF on stdin\n");
    return 1;
  }
  fprintf(stderr, "gifdec(wasi): read %ld bytes\n", len);
  
  int rc = gif_open(gif, (int)len);
  if (rc != 0) {
    fprintf(stderr, "gifdec: open failed rc=%d\n", rc);
    free(gif);
    return 2;
  }
  
  const int w = gif_width(), h = gif_height();
  fprintf(stderr, "gifdec(wasi): canvas %dx%d\n", w, h);
  
  const char *only = getenv("GIF_FRAME");
  const int onlyN = only ? atoi(only) : -1;  // -1 = all frames
  
  int frame = 0, r;
  do {
    int delay = 0;
    r = gif_play(&delay);
    if (r < 0) break;
    
    const bool emit = (onlyN < 0 || onlyN == frame);
    if (emit) write_ppm(w, h, gif_fb());
    
    fprintf(stderr, "  frame %d  delay=%dms%s\n", frame, delay, emit ? "  [emitted]" : "");
    frame++;
    if (onlyN >= 0 && frame > onlyN) break;
  } while (r == 1 && frame < 100000);
  
  fprintf(stderr, "gifdec(wasi): decoded %d frame(s), %dx%d\n", frame, w, h);
  gif_close();
  free(gif);
  return 0;
}
```

---

## 3. ESPHome Simulator Build System

### 3.1 jc3248w535 Makefile (firmware + simulator)

```makefile
YAML    ?= jc3248w535.yaml
ESPHOME  = uvx --from esphome esphome

# ---- Firmware (ESPHome via uvx) ----
compile: secrets
	$(ESPHOME) compile $(YAML)

run: secrets
	$(ESPHOME) run $(YAML)

upload:
	$(ESPHOME) upload $(YAML)

logs:
	$(ESPHOME) logs $(YAML)

# Generate random secrets
rand:
	@echo "api_encryption_key: \"$$(python3 -c 'import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())')\""

# ---- LVGL + SDL2 desktop simulator ----
sim-build:
	cmake -S sim -B sim/build -G Ninja 2>/dev/null || cmake -S sim -B sim/build
	cmake --build sim/build

sim: sim-v2
sim-v1: sim-build
	./sim/build/oracle_face_sim_v1

sim-v2: sim-build
	./sim/build/oracle_face_sim_v2

sim-clean:
	rm -rf sim/build

# ---- WASM build (browser-hosted, Emscripten) ----
sim-web:
	emcmake cmake -S sim -B sim/build-web -DCMAKE_BUILD_TYPE=Release
	cmake --build sim/build-web

sim-web-serve: sim-web
	@echo "open http://localhost:8000/oracle_face_sim_v2.html"
	cd sim/build-web && python3 -m http.server 8000

# Regenerate LVGL fonts from TTF (NotoSans + Thai glyph ψ)
sim-fonts:
	@for SZ in 14 22 28; do \
	  npx --yes lv_font_conv@latest \
	    --size $$SZ --bpp 4 --format lvgl \
	    --font sim/fonts/NotoSans-Regular.ttf \
	    -r 0x20-0x7F -r 0x3C8 \
	    --lv-font-name noto_$$SZ \
	    -o sim/fonts_gen/noto_$$SZ.c && \
	  echo "✓ sim/fonts_gen/noto_$$SZ.c"; \
	done
```

---

## 4. ESP-IDF C Code

### 4.1 ESP32-S3 Boot Banner (jc3248_pet_idf_main.c)

**Board**: Guition JC3248W535 (ESP32-S3 WROOM, 8MB flash QIO, 8MB OPI PSRAM @ 80MHz)

```c
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_system.h"
#include "esp_heap_caps.h"
#include "esp_psram.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_mac.h"

#include "display.h"   /* STEP 2: AXS15231B QSPI panel bring-up */
#include "touch.h"     /* STEP 4: AXS15231 capacitive touch (INT-gated) */
#include "fs.h"        /* STEP 5: LittleFS mount at /littlefs */
#include "gif.h"       /* STEP 6: AnimatedGIF renderer (bufo pack) */
#include "hud.h"       /* STEP 7: bottom HUD strip (name + status + dot) */
#include "audio.h"     /* STEP 8: i2s_std tone synth — tap plays ribbit */
#include "ble.h"       /* STEP 9: NimBLE NUS heartbeat bridge → live HUD */
#include "petclock.h"  /* STEP 10: top-strip clock (NTP over BLE) */

static const char *TAG = "jc3248-pet";

static const char *reset_reason_str(esp_reset_reason_t r) {
  switch (r) {
    case ESP_RST_POWERON:   return "POWERON (cold)";
    case ESP_RST_SW:        return "SW restart (warm)";
    case ESP_RST_PANIC:     return "PANIC (warm)";
    case ESP_RST_INT_WDT:   return "INT_WDT (warm)";
    case ESP_RST_TASK_WDT:  return "TASK_WDT (warm)";
    case ESP_RST_WDT:       return "other WDT (warm)";
    case ESP_RST_DEEPSLEEP: return "DEEPSLEEP wake (warm)";
    case ESP_RST_BROWNOUT:  return "BROWNOUT (warm)";
    case ESP_RST_USB:       return "USB peripheral reset (warm)";
    case ESP_RST_JTAG:      return "JTAG reset (warm)";
    default:                return "UNKNOWN";
  }
}

void app_main(void) {
  ESP_LOGI(TAG, "=== jc3248-pet-idf === boot");
  ESP_LOGI(TAG, "Guition JC3248W535 / ESP32-S3 desk-pet port — step 1 (hello-world)");
  
  /* Reset reason: cold vs warm */
  esp_reset_reason_t reason = esp_reset_reason();
  ESP_LOGI(TAG, "reset reason: %s", reset_reason_str(reason));
  
  /* Chip info: cores + features */
  esp_chip_info_t chip_info;
  esp_chip_info(&chip_info);
  ESP_LOGI(TAG, "chip   : %s, %d core(s), rev v%d.%d",
           CONFIG_IDF_TARGET,
           chip_info.cores,
           chip_info.revision / 100,
           chip_info.revision % 100);
  ESP_LOGI(TAG, "feats  : %s%s%s%s",
           (chip_info.features & CHIP_FEATURE_WIFI_BGN)   ? "WiFi "     : "",
           (chip_info.features & CHIP_FEATURE_BT)         ? "BT "       : "",
           (chip_info.features & CHIP_FEATURE_BLE)        ? "BLE "      : "",
           (chip_info.features & CHIP_FEATURE_IEEE802154) ? "802.15.4 " : "");
  
  /* Flash size */
  uint32_t flash_size = 0;
  if (esp_flash_get_size(NULL, &flash_size) == ESP_OK) {
    ESP_LOGI(TAG, "flash  : %" PRIu32 " MB %s",
             flash_size / (uint32_t)(1024 * 1024),
             (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded" : "external");
  }
  
  /* PSRAM: prove OPI initialized */
  if (esp_psram_is_initialized()) {
    size_t psram_total = esp_psram_get_size();
    size_t psram_heap  = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
    size_t psram_free  = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
    ESP_LOGI(TAG, "PSRAM  : OK (OPI) — chip %u KB, heap %u KB total, %u KB free",
             (unsigned)(psram_total / 1024),
             (unsigned)(psram_heap  / 1024),
             (unsigned)(psram_free  / 1024));
  } else {
    ESP_LOGW(TAG, "PSRAM  : NOT initialized (check OPI config in sdkconfig.defaults)");
  }
}
```

---

## 5. Rust Build Guard (Tauri)

### 5.1 oracle-app-tauri build.rs

**Prevents recursive embedding of build artifacts via `frontendDist` validation**:

```rust
use std::path::PathBuf;

fn main() {
    guard_frontend_dist();
    tauri_build::build()
}

/// Preflight guard against the `frontendDist` runaway (PR #17 / RCA).
/// 
/// `tauri-codegen`'s asset embedder recursively walks `frontendDist` and
/// bakes every file into the binary. If `frontendDist` resolves to a
/// directory that *contains* the cargo build output (`target/`), each build
/// embeds the previous build's embedded assets into a new, bigger bin — a
/// geometric blowup that once ballooned `target/` to ~250 GB.
///
/// This runs in `build.rs`, i.e. BEFORE the codegen macro expands, so a bad
/// `frontendDist` fails fast on build #1 and never accumulates anything.
fn guard_frontend_dist() {
    println!("cargo:rerun-if-changed=tauri.conf.json");

    let manifest = PathBuf::from(env_or_bail("CARGO_MANIFEST_DIR"));
    let conf = match std::fs::read_to_string(manifest.join("tauri.conf.json")) {
        Ok(c) => c,
        Err(_) => return,
    };

    let Some(dist) = extract_frontend_dist(&conf) else {
        return;  // devUrl-only / array / absent → nothing to embed from disk
    };

    // Resolve frontendDist relative to src-tauri/ and canonicalize to real path.
    let dist_path = manifest.join(&dist);
    let Ok(dist_abs) = dist_path.canonicalize() else {
        return;  // doesn't exist yet → tauri-build will surface that
    };

    // OUT_DIR always lives under target/. If it sits *inside* frontendDist,
    // the embedder will ingest the entire build tree.
    let out_dir = PathBuf::from(env_or_bail("OUT_DIR"));
    let out_abs = out_dir.canonicalize().unwrap_or(out_dir);

    if out_abs.starts_with(&dist_abs) {
        panic!(
            "\n\n  ✗ frontendDist (\"{dist}\") contains the build output.\n\
            \n      {} \n    is inside\n      {}\n\n  \
            tauri-codegen would recursively embed target/ into the binary —\n  \
            the ~250 GB runaway (see PR #17). Point frontendDist at a folder\n  \
            that holds ONLY the web assets, e.g. \"../ui\".\n\n",
            out_abs.display(),
            dist_abs.display(),
        );
    }
}

fn env_or_bail(key: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| panic!("{key} not set — build must run under cargo"))
}

/// Minimal extractor for `"frontendDist": "<path>"` string value.
/// Returns None if the value isn't a plain string (e.g. a devUrl or an array).
fn extract_frontend_dist(conf: &str) -> Option<String> {
    let key = "\"frontendDist\"";
    let after_key = &conf[conf.find(key)? + key.len()..];
    let after_colon = &after_key[after_key.find(':')? + 1..];
    
    let trimmed = after_colon.trim_start();
    let inner = trimmed.strip_prefix('"')?;
    let end = inner.find('"')?;
    Some(inner[..end].to_string())
}
```

---

## Architecture & Patterns

### ESPHome Pattern
- **HTTP polling**: 5s interval → JSON parse → LVGL label update
- **LVGL rendering**: Labels with fixed fonts, on-demand text updates
- **ANSI color handling**: Translate SGR codes to LVGL `#RRGGBB ..#` markup
- **Thai text**: Rendered via gfonts (Sarabun) extras in font config
- **Monospace terminal**: CLIP mode for stable viewport, no text wrapping

### WASM GIF Decoder Pattern
- **Dual target**: Same C++ core → wasm32-wasi (zig CLI) + wasm32-emscripten (JS library)
- **Scanline callback**: AnimatedGIF → RGB565 → RGBA8888 canvas (palette + alpha composition)
- **Persistent canvas**: One open() per GIF, play() decodes frames in-place
- **Frame timing**: playFrame() returns delay, caller drives pacing

### Build System Pattern
- **Makefile abstractions**: `make compile`, `make run`, `make sim-web`
- **UV package manager**: `uvx --from esphome esphome` (isolated, no global deps)
- **Emscripten + CMake**: `emcmake cmake` injects WASM toolchain
- **wasm-opt**: Optional optimization pass for WASI size reduction
- **Static fonts**: LVGL font tables compiled from gfonts via lv_font_conv

### ESP32-S3 Boot Pattern
- **OPI PSRAM**: 8MB @ 80MHz, verified at boot (PSRAM heap capacity logged)
- **USB Serial JTAG**: Built-in on ESP32-S3, no USB-to-UART bridge needed
- **Module steps**: display → touch → fs → gif → hud → audio → ble → clock
- **Reset tracking**: Cold (POWERON) vs warm (SW, PANIC, WDT, etc.)

---

## Key Discoveries

1. **Fleet-pulse**: Real-time dashboard polling maw/api/ls every 5s, renders session list with active marker
2. **Terminal viewer**: Handles up to 24KB capture buffer, ANSI→LVGL color mapping, UTF-8 Thai rendering, emoji color overrides
3. **WASM dual-target**: Same gifcore.cpp → WASI CLI (stdin/stdout PPM) + browser library (JS API)
4. **LVGL composition**: Transparent GIFs compose over previous frame, preserves animation disposal logic
5. **Build safety**: Tauri guard prevents recursive asset embedding (250GB runaway in PR #17)
6. **Monospace layout**: 320×480 display, header (28px) + 456px terminal viewport (clipped, bottom-pinned)

---

**End of CODE-SNIPPETS.md**
