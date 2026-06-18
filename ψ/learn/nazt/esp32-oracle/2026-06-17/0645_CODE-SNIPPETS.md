# ESP32 Oracle — Code Snippets & Patterns

**Date**: 2026-06-17  
**Purpose**: Copy-paste examples for common tasks: init sequences, state machines, BLE handlers, GIF decode, display render  
**Audience**: Developers building new firmware on this family; porting to new boards

---

## Display Init (ESP-IDF + Managed Component)

**File**: `jc3248-pet-idf/main/main.cpp` (simplified)

```cpp
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_axs15231b.h"

void display_init() {
    // QSPI bus config
    spi_bus_config_t buscfg = {
        .mosi_io_num = 6,
        .miso_io_num = 7,
        .sclk_io_num = 5,
        .quadwp_io_num = 8,
        .quadhd_io_num = 9,
        .max_transfer_sz = 480 * 320 * 2,  // full frame
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI3_HOST, &buscfg, SPI_DMA_CH_AUTO));

    // LCD I/O config (QSPI-DBI)
    esp_lcd_panel_io_spi_config_t io_config = {
        .cs_gpio_num = 4,
        .dc_gpio_num = 2,
        .spi_mode = 0,
        .pclk_hz = 6 * 1000 * 1000,  // 6 MHz (critical for GIF flicker)
        .trans_queue_depth = 10,
    };
    esp_lcd_panel_io_handle_t io_handle;
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(
        SPI3_HOST, &io_config, &io_handle));

    // Panel config
    esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = 1,
        .rgb_endian = LCD_RGB_ENDIAN_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor_config,  // AXS15231 init cmds
    };
    esp_lcd_panel_handle_t panel_handle;
    ESP_ERROR_CHECK(esp_lcd_new_panel_axs15231(
        io_handle, &panel_config, &panel_handle));

    // Reset & init
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel_handle));
    
    // Test: vertical color bars
    uint16_t *buf = heap_caps_malloc(480 * 320 * 2, MALLOC_CAP_SPIRAM);
    for (int y = 0; y < 320; y++) {
        for (int x = 0; x < 480; x++) {
            buf[y * 480 + x] = (x / 60) << 11 | 0x0F00;  // red gradient
        }
    }
    ESP_ERROR_CHECK(esp_lcd_panel_draw_bitmap(
        panel_handle, 0, 0, 480, 320, buf));
    
    free(buf);
    global_panel = panel_handle;
}
```

---

## GIF Decode & Render Loop

**File**: `jc3248-pet-idf/components/gif/gif.cpp` (simplified)

```cpp
#include "AnimatedGIF.h"

static AnimatedGIF gif;
static uint16_t *gif_buf;  // PSRAM framebuffer (320 * 480 * 2 bytes)

void gif_init(const uint8_t *gif_data, size_t gif_size) {
    gif_buf = (uint16_t *)heap_caps_malloc(320 * 480 * 2, MALLOC_CAP_SPIRAM);
    
    GifFileType *file = (GifFileType *)gif_data;
    gif.begin(LITTLE_ENDIAN);
    gif.openGif((uint8_t *)gif_data, gif_size);
}

void gif_play_frame(int frame_index, esp_lcd_panel_handle_t panel) {
    // Decode one frame into the 320×480 RGBA canvas
    gif.reset();
    for (int i = 0; i <= frame_index; i++) {
        if (gif.playFrame(true, NULL) == 0) break;  // last frame
    }
    
    // Get decoded RGBA
    uint16_t *pixels = (uint16_t *)gif.getBuffer();
    int w = gif.getWidth();
    int h = gif.getHeight();
    
    // Byte-swap RGB565 (little-endian → big-endian for QSPI panel)
    for (int i = 0; i < w * h; i++) {
        uint16_t rgb = pixels[i];
        uint8_t *p = (uint8_t *)&rgb;
        gif_buf[i] = (p[1] << 8) | p[0];  // swap bytes
    }
    
    // Blit to panel via QSPI DMA
    ESP_ERROR_CHECK(esp_lcd_panel_draw_bitmap(
        panel, 0, 0, w, h, (uint8_t *)gif_buf));
    
    // Frame delay (clamped: AnimatedGIF can return < 10ms)
    int delay_ms = gif.getDelayMs();
    if (delay_ms < 20) delay_ms = 20;
    vTaskDelay(pdMS_TO_TICKS(delay_ms));
}
```

---

## State Machine (Pet Logic)

**File**: `jc3248-pet-idf/main/main.cpp` (simplified)

```cpp
typedef enum {
    STATE_SLEEP = 0,
    STATE_IDLE,
    STATE_BUSY,
    STATE_ATTENTION,
    STATE_CELEBRATE,
    STATE_DIZZY,
    STATE_HEART,
} pet_state_t;

typedef struct {
    pet_state_t state;
    uint32_t last_activity_ms;
    bool ble_connected;
    bool approval_pending;
    uint32_t tokens_total;
} pet_t;

static pet_t pet = {
    .state = STATE_SLEEP,
    .ble_connected = false,
};

void state_machine_update(uint32_t now_ms, const char *event) {
    // Timeouts
    if (pet.state != STATE_SLEEP && 
        (now_ms - pet.last_activity_ms) > 30000) {
        // 30s idle → sleep
        pet.state = STATE_SLEEP;
    }
    
    // BLE events
    if (strstr(event, "ble:connect")) {
        pet.ble_connected = true;
        if (pet.state == STATE_SLEEP) pet.state = STATE_IDLE;
    }
    if (strstr(event, "ble:disconnect")) {
        pet.ble_connected = false;
        pet.state = STATE_SLEEP;
    }
    
    // Approval prompt
    if (strstr(event, "approval:pending")) {
        pet.approval_pending = true;
        pet.state = STATE_ATTENTION;
        led_blink_start(500);  // 500ms blink
    }
    if (strstr(event, "approval:done")) {
        pet.approval_pending = false;
        pet.state = STATE_HEART;
        led_blink_stop();
    }
    
    // Level up (every 50K tokens)
    if (strstr(event, "tokens:update")) {
        uint32_t new_total = 0;
        sscanf(event, "tokens:update %u", &new_total);
        if ((new_total / 50000) > (pet.tokens_total / 50000)) {
            pet.tokens_total = new_total;
            pet.state = STATE_CELEBRATE;
        }
    }
    
    // Shake detector
    if (strstr(event, "shake")) {
        pet.state = STATE_DIZZY;
    }
    
    // Touch
    if (strstr(event, "touch:")) {
        pet.last_activity_ms = now_ms;
        if (pet.approval_pending && strstr(event, "top")) {
            ble_send_approval(true);
        }
        if (pet.approval_pending && strstr(event, "bottom")) {
            ble_send_approval(false);
        }
    }
}

void app_main() {
    display_init();
    touch_init();
    audio_init();
    ble_init();
    
    gif_init(bufo_busy_data, bufo_busy_size);
    
    uint32_t last_frame_ms = 0;
    uint32_t frame_index = 0;
    
    while (1) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        
        // Poll events (touch, BLE, timer)
        char event[64] = {0};
        if (touch_read_event(event, sizeof(event))) {
            state_machine_update(now, event);
        }
        if (ble_read_message(event, sizeof(event))) {
            state_machine_update(now, event);
        }
        
        // Render current state
        const char *gif_name = state_to_gif_name(pet.state);
        gif_play_frame(frame_index, global_panel);
        frame_index = (frame_index + 1) % gif_total_frames(gif_name);
        
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
```

---

## BLE Nordic UART (buddy)

**File**: `buddy/src/ble_bridge.cpp` (simplified)

```cpp
#include <NimBLEDevice.h>

static NimBLEServer *ble_server;
static NimBLECharacteristic *nus_tx;
static NimBLECharacteristic *nus_rx;

class NUSCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic *chr) override {
        std::string data = chr->getValue();
        // Handle approval prompt
        if (data.find("approval") != std::string::npos) {
            JsonDocument doc;
            deserializeJson(doc, data);
            int approval_id = doc["id"];
            bool approved = doc["approved"];
            
            if (approved) {
                pet_state = STATE_CELEBRATE;
            } else {
                pet_state = STATE_IDLE;
            }
        }
    }
};

void ble_init() {
    NimBLEDevice::init("buddy");
    ble_server = NimBLEDevice::createServer();
    
    // Nordic UART Service
    NimBLEService *nus = ble_server->createService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");
    
    // TX (device → app): 6E400002-...
    nus_tx = nus->createCharacteristic(
        "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",
        NIMBLE_PROPERTY::NOTIFY);
    
    // RX (app → device): 6E400003-...
    nus_rx = nus->createCharacteristic(
        "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",
        NIMBLE_PROPERTY::WRITE);
    nus_rx->setCallbacks(new NUSCallbacks());
    
    nus->start();
    
    // Advertise
    NimBLEAdvertising *adv = NimBLEDevice::getAdvertising();
    adv->addServiceUUID(nus->getUUID());
    adv->start();
}

void ble_send_approval_response(int id, bool approved) {
    JsonDocument doc;
    doc["type"] = "approval";
    doc["id"] = id;
    doc["approved"] = approved;
    
    std::string json_str;
    serializeJson(doc, json_str);
    json_str += "\n";  // line-delimited
    
    nus_tx->setValue((uint8_t *)json_str.c_str(), json_str.length());
    nus_tx->notify();
}
```

---

## Touch Input (GT911 I2C)

**File**: `jc3248-pet-idf/components/touch/touch.cpp` (simplified)

```cpp
#include "driver/i2c_master.h"

#define GT911_ADDR 0x5D
#define GT911_INT_PIN 3

static i2c_master_dev_handle_t gt911_handle;

void touch_init() {
    i2c_master_bus_config_t i2c_mux_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .i2c_port = I2C_NUM_0,
        .sda_io_num = 8,
        .scl_io_num = 9,
        .flags = {.enable_internal_pullup = true},
    };
    i2c_master_bus_handle_t bus_handle;
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_mux_config, &bus_handle));

    i2c_device_config_t dev_config = {
        .dev_addr_length = I2C_ADDR_BIT_7,
        .device_address = GT911_ADDR,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_config, &gt911_handle));

    // GPIO for interrupt
    gpio_config_t gpio_conf = {
        .pin_bit_mask = (1ULL << GT911_INT_PIN),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .intr_type = GPIO_INTR_NEGEDGE,
    };
    gpio_config(&gpio_conf);
}

bool touch_read(uint16_t *x, uint16_t *y, uint8_t *points) {
    uint8_t buf[7];
    ESP_ERROR_CHECK(i2c_master_transmit_receive(gt911_handle, NULL, 0, buf, 7, 1000));
    
    if (buf[0] & 0x80) {  // touch detected
        *points = buf[0] & 0x0F;
        *x = ((buf[2] << 8) | buf[3]);
        *y = ((buf[4] << 8) | buf[5]);
        return true;
    }
    return false;
}

void touch_read_zone(uint16_t x, uint16_t y, const char *out_zone) {
    // JC3248W535 is 320×480 portrait
    if (y < 160) {
        strcpy(out_zone, "top");      // scroll up
    } else if (y > 320) {
        strcpy(out_zone, "bottom");   // scroll down
    } else {
        strcpy(out_zone, "middle");   // state change or approval
    }
}
```

---

## WASM GIF Decode (Emscripten)

**File**: `gif-wasm/src/gifcore.cpp` (C-linkage API)

```cpp
extern "C" {
    #include "AnimatedGIF.h"
    
    static AnimatedGIF gif;
    static uint32_t *canvas;
    
    // Open GIF from memory
    int gif_open(const uint8_t *data, size_t size) {
        canvas = (uint32_t *)malloc(512 * 512 * 4);  // max 512×512 RGBA
        gif.begin(LITTLE_ENDIAN);
        return gif.openGif((uint8_t *)data, size);
    }
    
    // Advance to frame N and decode
    int gif_play(int frame_num) {
        return gif.playFrame(true, NULL);
    }
    
    // Get pointer to decoded RGBA canvas
    uint32_t gif_fb() {
        return (uint32_t)gif.getBuffer();
    }
    
    // Get dimensions
    int gif_width() { return gif.getWidth(); }
    int gif_height() { return gif.getHeight(); }
    int gif_frames() { return gif.getFrameCount(); }
    
    // Get delay for current frame (ms)
    int gif_delay_ms() {
        int delay = gif.getDelayMs();
        return (delay < 20) ? 20 : delay;
    }
    
    void gif_close() {
        free(canvas);
        gif.close();
    }
}
```

**JavaScript consumer** (`gif-wasm/web/index.html`):

```html
<canvas id="canvas"></canvas>
<input type="file" id="file" accept=".gif" />

<script>
let module;
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Load WASM module (emcc-compiled)
fetch('gifdec.wasm').then(r => r.arrayBuffer()).then(wasm => {
    module = new WebAssembly.instantiate(wasm, {
        env: { /* emscripten glue */ }
    }).then(instance => {
        module = instance.instance;
        return module;
    });
});

document.getElementById('file').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const data = await file.arrayBuffer();
    
    const ptr = module._malloc(data.byteLength);
    module.HEAPU8.set(new Uint8Array(data), ptr);
    
    if (module._gif_open(ptr, data.byteLength) < 0) {
        console.error('Failed to open GIF');
        return;
    }
    
    const width = module._gif_width();
    const height = module._gif_height();
    const frameCount = module._gif_frames();
    
    canvas.width = width * 3;   // 3× pixelated
    canvas.height = height * 3;
    
    let frameNum = 0;
    const renderFrame = () => {
        module._gif_play(frameNum);
        
        const fbPtr = module._gif_fb();
        const imageData = ctx.createImageData(width, height);
        const pixels = new Uint8Array(module.HEAPU8.buffer, fbPtr, width * height * 4);
        imageData.data.set(pixels);
        
        // Scale 3×
        ctx.scale(3, 3);
        ctx.putImageData(imageData, 0, 0);
        
        const delay = module._gif_delay_ms();
        frameNum = (frameNum + 1) % frameCount;
        
        setTimeout(renderFrame, delay);
    };
    
    renderFrame();
});
</script>
```

---

## PlatformIO Build Config (Multiple Boards)

**File**: `buddy/platformio.ini` (excerpt)

```ini
[env:jc3248w535]
platform = https://github.com/pioarduino/platform-espressif32/releases/download/55.03.38-1/platform-espressif32.zip
board = esp32-s3-devkitc-1
framework = arduino
board_build.filesystem = littlefs
board_build.partitions = no_ota.csv
board_build.f_cpu = 240000000L
board_build.arduino.memory_type = qio_opi
upload_port = /dev/ttyACM1
monitor_port = /dev/ttyACM1

build_flags =
    -DCORE_DEBUG_LEVEL=0
    -DBOARD_JC3248W535C=1
    -DBOARD_ATD35_S3=1
    -DLGFX_USE_QSPI=1
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
    -DBOARD_HAS_PSRAM=1

build_src_filter = +<*> +<buddies/>

lib_deps =
    lovyan03/LovyanGFX @ ^1.2.0
    bitbank2/AnimatedGIF @ ^2.1.1
    bblanchon/ArduinoJson @ ^7.0.0

# Build & flash
# pio run -e jc3248w535 -t upload -t monitor
```

---

## Character Pack Format (manifest.json)

**File**: `buddy/characters/bufo/manifest.json`

```json
{
  "name": "bufo",
  "colors": {
    "body": "#6B8E23",
    "bg": "#000000",
    "text": "#FFFFFF",
    "textDim": "#808080",
    "ink": "#000000"
  },
  "states": {
    "sleep": "sleep.gif",
    "idle": ["idle_0.gif", "idle_1.gif", "idle_2.gif"],
    "busy": "busy.gif",
    "attention": "attention.gif",
    "celebrate": "celebrate.gif",
    "dizzy": "dizzy.gif",
    "heart": "heart.gif"
  }
}
```

**Python prep tool** (`buddy/tools/prep_character.py`):

```bash
# Resize GIFs to 96px wide, crop tight, optimize
python tools/prep_character.py characters/bufo
# → characters/bufo_prep/ with 96px GIFs

# Compress for flash (1.8MB limit per device)
gifsicle --lossy=80 -O3 --colors 64 *.gif
```

---

## Makefile Snippets (ESP-IDF Build)

**File**: `jc3248-pet-idf/Makefile` (helper wrapper)

```makefile
IDF_PATH ?= $(HOME)/esp/esp-idf
IDF_PYTHON_ENV_PATH ?= $(HOME)/.espressif/python_env/idf6.0_py3.13_env
PORT ?= /dev/ttyUSB0

# Ensure Python venv exists and is pinned
export IDF_PYTHON_ENV_PATH
IDFPY = "$(IDF_PYTHON_ENV_PATH)/bin/python3" "$(IDF_PATH)/tools/idf.py"

build:
	$(IDFPY) build

flash:
	$(IDFPY) flash -p $(PORT)

monitor:
	$(IDFPY) monitor -p $(PORT)

clean:
	$(IDFPY) fullclean

build-flash-monitor: build flash monitor

.PHONY: build flash monitor clean build-flash-monitor
```

---

## CMakeLists.txt for IDF (Minimal)

**File**: `jc3248-pet-idf/CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.22)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

project(jc3248_pet_idf)

# Managed dependencies
idf_component_register(
    SRCS
        "main/main.cpp"
    INCLUDE_DIRS
        "main"
    REQUIRES
        esp_lcd
        esp_driver_i2s
        esp_driver_ledc
        esp_driver_gpio
        nvs_flash
        freertos
        lvgl
        littlefs
        nimble
)
```

---

## Quick Refs

**Serial Monitor** (IDF):
```bash
idf.py monitor -p /dev/ttyUSB0 --baud 115200
# Ctrl+] to exit
```

**Rebuild from scratch** (IDF):
```bash
idf.py fullclean && idf.py build
```

**Flash filesystem only** (PlatformIO):
```bash
pio run -t uploadfs
```

**Test WASI WASM locally**:
```bash
wasmtime dist/gifdec.wasm < gifs/busy.gif > out.ppm
# View: open out.ppm (or convert to PNG)
```

**Build web simulator**:
```bash
cd lab/sim-gallery
make dev
# → http://localhost:5173
```

---

**End of Code Snippets**

*Copy-paste, adapt, verify on hardware.*
