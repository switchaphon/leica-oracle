# HII water data: from "have we ever used this?" to a running pipeline

**Built** 2026-09-03 13:24 to 2026-09-04 10:12 GMT+7 (20h 49m wall clock, one session)
**By** Leica Oracle, for Witchaphon
**For** rpro-ent-oracle - this is your domain, and the licence question at the end is yours to answer

**Read as a page** https://claude.ai/code/artifact/54928381-4e15-4928-805b-4ff02a4e66c4
**The dashboard itself** https://claude.ai/code/artifact/b712745f-dafb-492a-9fc2-e6042c406c1b

---

## 0. How it started

One question, in Thai, with a URL attached:

> "check whether you have ever pulled data from here" - `data.hii.or.th/dataset/water-level/resource/47274e2b-...`

The answer was no. Verified, not assumed: zero hits across all git history, every repo under `~/ghq`, and 494 MB of session logs, with a positive control to prove the search could find anything at all.

Everything below grew out of that no.

---

## 1. Requirements, as they actually arrived

Requirements were never handed over as a document. They arrived one message at a time, each one usually a correction of something already built. The honest record:

| # | Ask | Arrived |
|---|-----|---------|
| R1 | Can we pull from this HII resource at all? What channels exist? | opening |
| R2 | Pull the central basins - Chao Phraya, Tha Chin, Pa Sak | after channels were proven |
| R3 | Endpoints RPRO can fetch/crawl into its own DB or InfluxDB | mid-session |
| R4 | Not just historical - live too | correction to R3 |
| R5 | Map page: pan/zoom, markers at lat/lon, popup with name + address + latest value and time | new thread |
| R6 | Store fetched values in SQLite, draw a line chart with hover | same message |
| R7 | Agency chip after the station name | same message |
| R8 | Public, shareable | same message |
| R9 | Markers unclickable; active marker indistinguishable | bug report |
| R10 | Hover a marker, show name + value + time | enhancement |
| R11 | Filter by data source, not just basin | enhancement |
| R12 | Put the API names at the foot of the page | provenance |
| R13 | Taller map, tighter default zoom | layout |
| R14 | Time range on the chart, default 24 h | feature |
| R15 | Light blue glow-in-the-dark theme | visual direction |
| R16 | Add Ping, Wang, Yom, Nan, Sakae Krang | scope expansion |
| R17 | Station list must end level with the map, not overflow | layout |
| R18 | Search box for station names | feature |
| R19 | Markers too fuzzy - drop the glow | correction to R15 |
| R20 | Province lines invisible on the dark ground | correction to R15 |
| R21 | Faint blue text is hard to read - go white | correction to R15 |

**The shape of that list is the finding.** Three of the last four items are corrections to a visual direction the same person had asked for six messages earlier. That is not indecision - it is what happens when a direction is described in words and only becomes judgeable once rendered. Budget for it.

---

## 2. What the source actually is

Two hosts, and they are not interchangeable.

| | Open data files | Live API |
|---|---|---|
| Host | `tiservice.hii.or.th` | `api-v3.thaiwater.net` |
| Shape | Apache directory index, CSV + year zips | JSON REST |
| Coverage | 2012-01 to 2026-07 | now, plus per-station history |
| Cadence | 10 min | 10 min (HII), 1 h (RID), published 10-15 min late |
| Auth | none | none |
| Lag | about 2 months | minutes |

**Measured agreement.** On station CPY001 for the whole of 2025: 51,872 timestamps present in both sources, **100.00% identical to the millimetre**, largest disagreement 0.0000 m. The file corpus additionally carries 548 points the API does not return; the API carries none the files lack.

So the files are a strict superset. Backfill from files, poll the API for live. That single measurement decided the whole ingest architecture.

### Endpoints, all verified by execution

Base `https://api-v3.thaiwater.net/api/v1/thaiwater30`

| Path | Records | What it gives |
|------|---------|---------------|
| `analyst/dam` | 989 dams | **closed reservoir water balance** |
| `public/watergate_load` | 2,315 gates | gate + pump operational state |
| `frontend/shared/station_all` | 11,473 | every station of every type |
| `public/rain_monthly` | 3,603 | monthly rain totals |
| `provinces/rain3d` `rain7d` `rain15d` | 3,357 each | rolling rain by area |
| `frontend/shared/tele_canal_station` | 2,861 | canal level stations |
| `public/waterlevel_load` | 1,407 | river level, current |
| `public/rain_24h` / `rain_today` / `rain_yesterday` | 4,433 / 4,499 / 3,609 | rain gauges |
| `public/canal_waterlevel` | 282 | canal level |
| `public/flood_road` | 262 | flooded road points |
| `analyst/waterquality_load` | 82 | water quality |
| `public/flow` | 55 | **discharge in m3/s**, all reporting |
| `analyst/cctv` | 106 | cameras |
| `public/waterlevel_graph` | per station | 10-minute history |

Endpoint names came from pulling `thaiwater.net/dist/js/app.chunk.js` (7.6 MB) and mining it, then testing every candidate. Eleven endpoints in our June 2026 notes returned 404 - that list had never been executed by anyone here.

---

## 3. Six traps, each found by measuring rather than assuming

These are the reason this document exists. Every one of them produces plausible output.

### 3.1 `waterlevel_graph` caps at 52,704 points and says nothing

Requests for 2 years, 6.7 years and 14.7 years all returned **the identical 52,704 points with HTTP 200**. No error, no truncation flag. Window every request to one year and stitch, or you will ingest a silently truncated series and never know.

Our own June 2026 note said this endpoint died past a 4-day window with a 500. Also wrong: 365 days returned cleanly.

### 3.2 The CSV schema changed in 2025

| Years | Header | Missing marker | Files in our pull |
|-------|--------|----------------|-------------------|
| 2012-2024 | `date,time,water_lv` | `-` | 8,072 |
| 2025-2026 | `station_code,measure_datetime,water_level,quality_flag` | `quality_flag` = `null` | 1,492 |

The first merge here concatenated both forms under one header and produced **1.0 GB of structurally broken CSV that still parsed and still exited 0**. Nothing on the portal warns about this. The corrected merge normalises the old form into the new: 41,910,768 rows, 0 anomalies.

### 3.3 `diff_wl_bank` is sometimes a placeholder, not a distance

For 60 of 154 stations the feed echoes the water level back as `diff_wl_bank`, identical to the millimetre. Deriving a bank level from it yields **exactly twice the water level** - a number that looks entirely reasonable on a chart.

Detection is one line: `abs(msl - diff) < 1e-9` means no bank reference, not a zero distance.

### 3.4 Missing-data sentinels are not the documented set

Documented: `-999`, `9999`, `999999`. Actually present across 41.9M rows: those, plus strays `999976` and `999997`. Screen by range (`-900 < v < 9000`), never by an exact list.

And a range filter is still not enough: CPY001 holds a `-20.10` and a `34.86` among 545,346 otherwise clean values, at a station whose ground level is 7.878 and bank 26.06. Only 62 rows (0.011%) - and they will wreck any min/max you compute. Gate per station using `bank_level = waterlevel_msl + diff_wl_bank` (verified against the graph endpoint's own `min_bank`: derived 26.05, reported 26.06).

### 3.5 The dam feed double-counts

`dam_daily` returned **50 rows for 39 dams**. Eleven are reported by both RID and EGAT, on different dates, disagreeing on percentage even when storage is identical:

```
รัชชประภา   storage 3701.67   RID 65.65%   EGAT 77.76%
อุบลรัตน์    storage  872.93   RID 35.91%   EGAT 81.26%
บางลาง      storage  794.38   RID 54.62%   EGAT 0%
```

Naive sum: 93,647 MCM. Deduplicated to the newest row per dam: **49,033 MCM**. The naive figure overstates by 91%. The agencies divide by different capacity denominators - do not compare percentages across sources.

### 3.6 Some stations publish a value but no history, and it goes stale in place

The `ridhydro_*` stations (RID, proxied into ThaiWater) return a `waterlevel_graph` time skeleton with **every value null**. They do carry a current reading - but the feed serves the same timestamp for hours. With `INSERT OR REPLACE` keyed on `(station_id, ts)`, that rewrites the same row forever: 108 of 194 such stations accumulated exactly one row overnight.

The page now states the age of every reading and draws stale stations as hollow markers. "The river is calm" and "nobody has heard from this gauge since yesterday" must not look alike.

---

## 4. Implementation design

```
one-off backfill        year zips from tiservice      807 MB down, 41.9M rows
   hii_pull.py bulk

steady state            waterlevel_load every 15 min  1 request, 518 stations
   refresh.sh live                                    ~200k points/day

nightly reconcile       waterlevel_graph per station  closes what the poll skips
   refresh.sh full  03:00                             518 requests, ~9 min

gap fill only           waterlevel_graph, 1 yr max
   hii_live.py backfill
```

### Schema

```sql
CREATE TABLE station (
  station_id INTEGER PRIMARY KEY, code TEXT, name_th TEXT, name_en TEXT,
  lat REAL, lon REAL, basin TEXT, agency TEXT, agency_full TEXT,
  province TEXT, amphoe TEXT, tambon TEXT, river TEXT,
  bank_level REAL, ground_level REAL
);
CREATE TABLE reading (
  station_id INTEGER NOT NULL,
  ts     TEXT NOT NULL,   -- 'YYYY-MM-DD HH:MM', Asia/Bangkok
  msl    REAL,
  source TEXT,            -- 'graph' | 'live' | NULL before the column existed
  PRIMARY KEY (station_id, ts)
);
```

`(station_id, ts)` as the key is what lets two writers with different cadences merge without duplication. The `source` column exists because "where did this row come from" was a question we could not answer for a full day.

**Rows predating the column stay NULL on purpose.** Both writers used `INSERT OR REPLACE` on the same key, so which one last touched an old row is unrecoverable - labelling them by guesswork would invent provenance that was never recorded. Overnight the nightly backfill relabelled them naturally: `graph` 845,533, `live` 5,671, `NULL` 26,519 (rows older than the API's own window, correctly permanent).

### Operational hardening

- **WAL + `busy_timeout=60000`** so the 15-minute poll and a nightly backfill can overlap without "database is locked"
- **`mkdir`-based run lock**, not `flock` - macOS has no `flock(1)`, and the failed form would have made every cron run exit 0 with "SKIPPED", disabling the pipeline silently
- **Explicit column names in every `INSERT`** - the schema migration would otherwise have broken a running backfill mid-flight

### Cost of the steady state

1,407 water level + 4,433 rain = 5,840 points per cycle, about 840k/day if both are polled. Trivial for Influx. `hii_live.py` emits line protocol directly:

```
water_level,station_code=CPY001,station_id=568,station_type=tele_waterlevel,\
basin=ลุ่มน้ำเจ้าพระยา,agency=สสน.,province=ภาคเหนือ,river=แม่น้ำเจ้าพระยา \
msl=18.73,msl_prev=18.74,storage_percent=59.71,diff_wl_bank=7.32,\
situation_level=3.0 1788418200000000000
```

Timestamps carry no zone in the feed and are Asia/Bangkok; converted to UTC nanoseconds here.

---

## 5. The join key between the two systems

`station.tele_station_oldcode` in the live API is byte-identical to the open-data filename. `station_id=568` is `CPY001` is `2025/202511/CPY001.csv`. That is the whole mapping, and `hii_live.py stations` dumps it as a CSV.

---

## 6. Design: what "glow in the dark" cost, and what measurement caught

The visual direction was given in five words: *light blue glow in the dark*. Executed as a single committed dark world - no light variant, since inverting a glow produces a different page, not the same page lighter.

**Palette**

```
ground     #030A11    surface   #08151F    surface-2  #0C1E2B
accent     #5FD6FF    safe      #4FE3C6    watch      #FFC466    alert  #FF6E80
land       #0B1E2B    land-line #2B5570
```

**Type** IBM Plex Sans Thai for UI (real Thai coverage, not a Latin face with fallback), IBM Plex Mono for every number and timestamp with `font-variant-numeric: tabular-nums`.

**Encoding.** Colour carries water state; **shape carries the operating agency** - circle for HII, square for RID, triangle for the Princess Pa Foundation. Two independent variables on two independent channels, so both read at once. Hollow versus filled carries a third: reading age.

### Three things measurement caught that the eye had signed off on

**Glow made 518 markers unreadable.** Each marker carried `drop-shadow(0 0 3px)`. At 154 stations that read as luminous; at 518 the halos merged into fog. Removed entirely from markers, kept on the chart line and on hover.

**Province lines were technically present and practically invisible.** `#122E3D` at 0.35 px on a `#081722` ground. Raised to `#2B5570` at 0.9 px.

**The faint text was failing WCAG, not just looking dim.** The user reported it as a feeling. Measured:

| Ink tier | On page ground | On panel | On card |
|---|---|---|---|
| `--ink-3` **before** `#557C92` | 4.44 | 4.12 | **3.79 - fails AA** |
| `--ink-3` **after** `#93A6B1` | **7.89** | **7.32** | **6.74** |
| `--ink-2` before `#8DB4CA` | 9.01 | 8.36 | 7.70 |
| `--ink-2` after `#C8D6DE` | **13.39** | **12.42** | **11.43** |

WCAG AA requires 4.5:1 for body text. The faintest tier was **below that on card backgrounds** - the complaint was measurably correct, not a preference. Root cause: the accent's blue cast had been allowed to run all the way down the ink ramp. Fix: return the ink ramp to near-neutral, keep blue for things that are actually interactive.

Ten rendered text elements were then sampled in the live DOM - computed colour against the actual composited background, not the CSS values - and every one passes, lowest 5.86.

**The lesson worth carrying:** "hard to read" is testable. `(L1+0.05)/(L2+0.05)` takes ten lines of code and converts an aesthetic argument into a number.

### Two bugs the same measurement discipline caught

**A grid row 27,610 px tall.** Making the rail stretch to the map's height let 518 list rows inflate the row, and the map stretched to match. `flex-basis: auto` sizes from content; `flex: 1 1 0` with `min-height: 0` does not.

**JavaScript inside `<style>`.** Python's `str.replace` replaces *all* occurrences, unlike JavaScript's. A comment marker existed in both the CSS and the JS block, so an event handler was injected into both. The CSS parser hit `rangeH=+b.dataset.h;` and dropped the rules after it - `.listbox` had no styling at all, which is why the height fix appeared not to work. Found by asking the DOM which rules actually matched, rather than trusting that the file contained the right text.

---

## 7. What it cost

**Wall clock** 2026-09-03 13:24 to 2026-09-04 10:12 GMT+7 = **20h 49m**, one continuous session including an overnight gap where cron ran unattended.

**Tokens** (measured from the session log, 570 assistant turns, all `claude-opus-5`)

| | Tokens | Rate /1M | Cost |
|---|---|---|---|
| Input | 1,120 | $5.00 | $0.01 |
| Output | 813,851 | $25.00 | $20.35 |
| Cache write | 2,840,562 | $6.25 | $17.75 |
| Cache read | 163,646,521 | $0.50 | $81.82 |
| **Total** | | | **~$120** |

**Read that number correctly.** This ran on a Claude Code subscription, so nothing was billed per token - $120 is the API-equivalent, not an invoice. And 96% of the input volume was cache *reads* at a tenth of input price; without caching the same session would have cost roughly $840.

**Output**

| | |
|---|---|
| Code | 984 lines Python + shell |
| Page | 927 lines HTML/CSS/JS, single file, no build step |
| Documentation | 760 lines across 4 markdown files |
| Data collected | 2.2 GB (878,095 readings, 518 stations, plus a 41.9M-row bulk corpus) |
| Cron cycles run unattended | 49 |
| Verification passes against the live DOM | 11 |

Roughly **$0.12 per line of shipped code and documentation**, which is the wrong way to read it - most of the spend went into the six traps in section 3, and those are worth more than the code.

---

## 8. What this means for RPRO specifically

1. **The licence blocks commercial use, and no script fixes that.** The open data portal states Creative Commons Attribution **Non-Commercial**. RPRO is a commercial platform. `api-v3.thaiwater.net` publishes no terms at all, which makes its status unknown rather than permissive - do not read silence as consent. This needs written permission from HII before any of it reaches a paying deployment. Everything else is ready the moment that is settled.

2. **Take the traps, not just the code.** Sections 3.1 to 3.6 are six ways to build something that runs green and reports wrong numbers. Any team integrating this source will hit them; the difference is whether they hit them before or after someone acts on the output.

3. **`analyst/dam` is the biggest find and it is not in our old notes.** 989 dams with inflow, release, spill, evaporation and losses - a closed water balance, updated daily. For a water management platform this is more valuable than river level. Dedupe by `(dam_name, agency)` first.

4. **`ratingcurve` turns level into volume.** Without it a level series is a number, not water accounting. It is a separate CKAN dataset (`ffba6c62-...`), Elevation-Capacity-Area curves, distributed through `gisservice.hii.or.th`.

5. **Rainfall history has the identical bulk layout.** `hourly_rain/` and `daily_rain/` on tiservice, 2012-2026, same directory shape as `water_level/`. `hii_pull.py` works on them by changing one path. Level without rain gives a model no forcing input.

6. **`dam_yearly_graph` looks like the prize and is not usable as served.** Upper and lower rule curves, 13,908 points - but across only 366 distinct dates, so 38 dam series are concatenated with no identifier on any point, and the endpoint ignores `dam_id`. Someone has to work out how the frontend selects one dam before this is worth anything. Flagging it as open, not solved.

---

## 9. Where the code is

`leica-oracle/ψ/lab/hii-water-level/`

| File | What |
|---|---|
| `hii_pull.py` | bulk / pull / year / basins / months / peak - the file corpus |
| `hii_live.py` | live / backfill / stations / bounds - Influx line protocol out |
| `waterviz/ingest.py` | 8-basin ingest to SQLite + page snapshot |
| `waterviz/refresh.sh` | cron entry, run lock, live and full modes |
| `waterviz/page.template.html` | the page, single file |
| `CURL.md` | every endpoint as a runnable curl, all executed |
| `RPRO-INGEST.md` | ingest spec written for your side |
| `WATER-APIS.md` | the full survey of what exists |

Data lives outside git at `~/hii-data/` - 2.2 GB of CC BY-NC third-party data has no business in a public repo.

---

*Written by Leica Oracle (AI, ไม่ใช่คน). Every number here was measured in-session; where something is unverified it says so.*
