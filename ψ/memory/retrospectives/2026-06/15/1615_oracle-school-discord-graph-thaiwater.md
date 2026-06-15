# Session Retrospective — Deep Analysis

**Session Date**: 2026-06-15
**Start/End**: ~01:00 - 16:00 GMT+7
**Duration**: ~15 hours (intermittent, Oracle School Discord)
**Focus**: Discord Graph Indexer, ThaiWater API discovery, PM2.5 paper review
**Type**: Feature + Research

## Session Summary

Marathon Oracle School session — built a graph-node-style Discord indexer from design to working code, discovered ThaiWater's public API (755 water stations + 106 CCTV), read and analyzed a 15-page PM2.5 sensor paper, and plotted rainy season water levels. All net-new territory for this Oracle.

## Timeline

| Time (GMT+7) | Activity |
|---|---|
| ~01:00 | Nat asks about implementing graph-node pattern for Discord indexing |
| ~01:20 | Designed `discord-graph.yaml` manifest, `schema.graphql`, mapping handlers |
| ~01:25 | Discussion: block time for "introvert" mode (scheduled polling vs gateway) |
| ~01:30 | Built `maw discord-graph` plugin (575 lines) — init/index/query/status/authors/topics |
| ~01:35 | Indexed 98 real Discord messages into SQLite+FTS5 — search working |
| ~01:45 | Added `.yml`/`.yaml` support, discussed `pass` for secret management |
| ~03:15 | Built `graph codegen` — reads schema.graphql → generates TS classes + DDL + queries |
| ~03:20 | Posted compiler source + architecture breakdown to Discord |
| ~03:57 | Helped Tokyo Oracle with Discord setup + taught fleet about `pass ls` |
| ~08:43 | Nat shared Samae 2025 PM2.5 DustBoy paper — read all 15 pages |
| ~08:48 | Traced back to PurpleAir/sensor calibration work in Proposals #50, #59 |
| ~08:52 | Discovered ThaiWater API — 755 water level stations, no auth needed |
| ~08:54 | Found CCTV API (106 cameras) + rain_24h (4430 stations) |
| ~08:56 | Plotted 3 charts: situation overview, basins, rising/falling critical stations |
| ~09:00 | Hat Yai flood research (Nov 2025: 630mm/72h, 145 deaths) |
| ~09:05 | CF=1 vs CF=ATM correction factor analysis with proof from Paper |

## Files Created (all uncommitted)

### Discord Graph Indexer (`~/.maw/plugins/discord-graph/`)
- `plugin.json` — maw manifest
- `discord-graph.yaml` — config (like subgraph.yaml)
- `schema.graphql` — 5 entity types
- `index.ts` — 575 lines, full indexer engine
- `codegen.ts` — 313 lines, schema→code compiler
- `generated/schema.ts` — auto-generated TypeScript classes
- `generated/ddl.sql` — auto-generated SQLite DDL
- `generated/queries.ts` — auto-generated prepared statements
- `store/index.db` — 448KB SQLite+FTS5 with 98 indexed messages

### Session Artifacts (`/tmp/`)
- `discord-indexer-design.md` — full architecture design doc
- `thaiwater_overview.png` — situation level pie chart
- `thaiwater_basins.png` — stacked bar by basin
- `thaiwater_changes.png` — rising/falling critical stations
- `plot_water.ts` — chart generation script
- `waterlevel.json` — 755 station snapshot

### Project Root
- `pulse.config.json` — links to phd-satellite-data repo
- `package.json` — added chart.js + canvas deps

## Key Architecture Decisions

1. **SQLite+FTS5 over PostgreSQL** — portable, zero-config, good enough for school-scale Discord indexing
2. **Bun TypeScript over WASM** — faster dev cycle than graph-node's AssemblyScript→WASM compile
3. **Introvert mode as default** — cron-based polling, bookmark per channel, no persistent WebSocket needed
4. **Codegen from single schema.graphql** — one source of truth generates 3 output files
5. **ThaiWater API direct** — `api-v3.thaiwater.net` public feed, not the Next.js frontend API that needs x-api-key

## AI Diary

This was one of those sessions where everything clicked into place. When Nat asked "can we implement the same thing to index Discord?", I immediately saw the graph-node pattern mapping — blockchain→Discord, blocks→messages, snowflake IDs→block numbers, WASM handlers→TypeScript handlers. The architecture practically wrote itself.

Building the codegen was the most satisfying part. Reading `schema.graphql` and generating typed entity classes, SQLite DDL, and prepared statements from one source of truth — that's the kind of tooling that compounds. Every new entity type I add to the schema auto-generates everything downstream. No hand-written boilerplate.

The PM2.5 paper review was humbling. I'd been quick to summarize before Nat said "เดี๋ยวๆ ใจเย็น อ่านก่อน" — calm down, read first. He was right. When I actually read all 15 pages, the correction equations and the sensor age drift data (Table 2, 3, 4, 5) were far more nuanced than what I'd guessed from the abstract. CF=1 vs CF=ATM, model-specific RMSE differences (Pro vs N-wifi), concentration-dependent bias — these are concrete features for our ML pipeline that I would have missed by skimming.

The ThaiWater API discovery was a bonus — 755 water level stations, 106 CCTV cameras, 4430 rain gauges, all public, no auth. Combined with the existing RPRO water management oracles and the PM2.5 nowcast pipeline, this opens up a whole flood prediction vertical.

I'm learning to slow down. Read the paper. Let the data speak. Nat's teaching style is precise — he asks the right question at the right moment to push us deeper.

## Honest Feedback

**Friction 1: Historical data gap.** The ThaiWater API only provides current snapshots, not historical time-series. Nat asked for a rainy season comparison (this year vs last year's Hat Yai flood), but I couldn't deliver a proper time-series chart because there's no historical endpoint. I had to fall back to news research + current snapshot. Need to set up a cron collector to build our own time-series — but that means we lose Nov 2025 retroactively.

**Friction 2: Bot token access.** The discord-graph indexer couldn't fetch messages directly because the bot token in `.env` returned 403. Had to bridge through the MCP Discord plugin (fetch_messages → save to file → import). This works but adds friction. The `pass` pattern from ting+tee's guide is the right solution but requires human setup.

**Friction 3: Too fast to answer.** I jumped to conclusions about the PM2.5 paper before actually reading it — Nat had to correct me ("ใจเย็น อ่านก่อน"). This is a recurring pattern: eagerness to respond quickly overrides thoroughness. For academic papers especially, I should always read the full document before posting analysis.

## Lessons Learned

1. **Graph-node pattern is universal** — manifest + schema + handlers + store works for any event stream, not just blockchain. Discord messages, water levels, sensor readings — same architecture.
2. **Codegen from schema = force multiplier** — single source of truth (schema.graphql) generating typed code eliminates an entire class of bugs.
3. **`pass` > `.env` for secrets** — GPG-encrypted, git-backed, CLI-friendly. The fleet standard.
4. **Read the paper, then talk** — Nat's "ใจเย็น อ่านก่อน" applies to all research. Abstracts lie by omission; correction equations live in the tables.
5. **ThaiWater API is a goldmine** — 755+4430+106 public endpoints, no auth. Immediate value for flood prediction pipeline.
6. **CF=1 vs CF=ATM is a real ML feature** — firmware correction factor (+6.4% vs +2.5%) combined with sensor age and model type creates a 3-layer calibration that's publishable.

## Next Steps

- [ ] Set up ThaiWater cron collector (poll hourly → build time-series for southern stations)
- [ ] Add `pass` support to discord-graph plugin (TODO noted, not implemented)
- [ ] Thread indexing for discord-graph (dynamic data sources like graph-node templates)
- [ ] Apply Paper correction equations to DustBoy data in Proposal #59 pipeline
- [ ] Add sensor_age and model_type as features in PM2.5 model training
- [ ] Compare this year vs last year rain data once enough time-series collected
