---
title: Graph-node pattern is a universal event indexer
date: 2026-06-15
source: "rrr --deep: leica-oracle"
confidence: high
tags: [architecture, graph-node, indexer, discord, maw-plugin, codegen, thaiwater, pm2.5]
---

## Pattern: Manifest + Schema + Handlers + Store

The graph-node architecture (subgraph.yaml → schema.graphql → mapping.ts → PostgreSQL → GraphQL) is not blockchain-specific. It works for any ordered event stream:

| Source | Event | Block ID | Store |
|--------|-------|----------|-------|
| Ethereum | Transaction/Log | Block number | PostgreSQL |
| Discord | Message | Snowflake ID | SQLite+FTS5 |
| ThaiWater | Water level reading | Timestamp | DuckDB |
| DustBoy | PM2.5 sensor reading | Timestamp | TimescaleDB |

Key insight: Discord Snowflake IDs are monotonically increasing AND encode timestamps — they're a natural block number equivalent with zero reorg risk.

## Codegen from Single Schema

`schema.graphql` → codegen → 3 outputs:
- TypeScript entity classes (load/save/all)
- SQLite DDL (CREATE TABLE + FTS5 + triggers)
- Prepared statement factories (insert/upsert/getById/count/all)

One source of truth, no hand-written ORM. Add entity to schema → re-run codegen → done.

## Introvert Mode (Bookmark Pattern)

For non-realtime indexing (no persistent connection):
- Poll on schedule (cron)
- Bookmark = last processed ID per channel
- Fetch `?after=bookmark` → process batch → advance bookmark
- Resumable, idempotent, rate-limit friendly

## Sensor Calibration as ML Features (from Samae 2025 Paper)

Three-layer correction for DustBoy PM2.5 data:
1. CF type (CF=1: +6.4% bias, CF=ATM: +2.5%)
2. Sensor age (<1yr, 1-2yr, >2yr → drift 10-19% SD)
3. Concentration range (<100 vs >100 µg/m³ → nonlinear correction)

Paper: Samae et al. 2025, Atmosphere 16(1):76, doi:10.3390/atmos16010076

## Secret Management: `pass` > `.env`

Fleet standard: `pass insert discord/<oracle>-token` → GPG-encrypted, git-backed.
Never hardcode tokens. Agents read via `pass show`. `.env` is plaintext on disk.

## ThaiWater Public API

```
Base: https://api-v3.thaiwater.net/api/v1/thaiwater30/public/
  waterlevel_load  → 755 stations (realtime, JSON)
  rain_24h         → 4430 stations

Base: https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/
  cctv             → 106 cameras (with URLs)
```

No auth needed. Gotcha: HEAD returns 404, only GET works.
