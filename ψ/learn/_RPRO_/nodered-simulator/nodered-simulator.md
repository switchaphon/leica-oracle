# nodered-simulator Learning Index

## Source
- **Origin**: /Users/switchaphon/_RPRO_/internal-server/nodered-simulator
- **Type**: Local project (IoT simulator)

## Explorations

### 2026-04-26 1744 (--deep)
- [2026-04-26/1744_ARCHITECTURE](2026-04-26/1744_ARCHITECTURE.md)
- [2026-04-26/1744_CODE-SNIPPETS](2026-04-26/1744_CODE-SNIPPETS.md)
- [2026-04-26/1744_QUICK-REFERENCE](2026-04-26/1744_QUICK-REFERENCE.md)
- [2026-04-26/1744_TESTING](2026-04-26/1744_TESTING.md)
- [2026-04-26/1744_API-SURFACE](2026-04-26/1744_API-SURFACE.md)

**Key insights**:
- Physics-based water management IoT simulator — 3 services (Node-RED engine, Laravel Web UI, Python CCTV) sharing a Docker volume via managed_config.json; replaces real field hardware for MQTT control system testing
- `functions/*.js` is the source of truth — never edit flows.json directly; use `npm run sync` to inject function code into Node-RED nodes via function-mapping.json
- Substantial test coverage across 3 runtimes (node:test, PHPUnit+Playwright, pytest) but CI jobs all have allow_failure:true — tests are the local gate, not the CI gate
