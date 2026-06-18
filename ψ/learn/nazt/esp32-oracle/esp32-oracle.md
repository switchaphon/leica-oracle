# esp32-oracle Learning Index

## Source
- **Origin**: ./origin/ (from Nat's esp32-source-trimmed.zip)
- **Author**: nazt_ (Nat)

## Explorations

### 2026-06-17 0639 (deep)
- [Architecture](2026-06-17/0639_ARCHITECTURE.md)
- [Code Snippets](2026-06-17/0639_CODE-SNIPPETS.md)
- [Quick Reference](2026-06-17/0639_QUICK-REFERENCE.md)
- [Testing](2026-06-17/0639_TESTING.md)
- [API Surface](2026-06-17/0639_API-SURFACE.md)

**Key insights**:
- "Many bodies, one soul" — single C++ GIF decoder (gifcore.cpp) compiles to ESP32, WASM browser, WASI CLI, desktop apps
- WASM runs on ESP32 AND in browser — same 17KB binary, different runtimes
- Pet state machine: idle → busy → attention → celebrate → dizzy → sleep → heart
- AXS15231 panel requires cold boot + non-black warmup frames (warm reset trap)
- ESPHome fleet-pulse polls maw /api/ls every 5s → LVGL labels with Thai font support
- 26 lab projects spanning firmware, simulators, desktop apps, web gallery
- Blog posts document real hardware bugs: DMA cache, PSRAM, byte order, panel warmup
- sim-gallery = React + Vite + LVGL/SDL→WASM, deploy to Cloudflare Workers
