# HII / ThaiWater ingest for RPRO

Everything below was executed against the live services on 2026-09-03, not read
off documentation. Numbers are measured.

## Before anything else: the licence gate

The open data portal states **Creative Commons Attribution Non-Commercial**.
RPRO is a commercial platform. That is a direct conflict and it is not a
technical problem, so no script here solves it.

`api-v3.thaiwater.net` publishes no terms page that I could find, which means
its status is unknown rather than permissive. Do not read silence as consent.

**Action for Un:** get written permission from สสน. (HII) for commercial use, or
confine this data to the research side. Everything below is ready to run the
moment that is settled.

## The two systems, and which one is authoritative

| | Open data files | Live API |
|---|---|---|
| Host | `tiservice.hii.or.th` | `api-v3.thaiwater.net` |
| Shape | Apache directory index, CSV + year zips | JSON REST |
| Coverage | 2012-01 to 2026-07 | now, plus per-station history |
| Cadence | 10 min | 10 min, published with a 10-15 min lag |
| Auth | none | none |
| Lag | about 2 months behind | minutes |

**Measured on CPY001 for 2025, the two sources agree exactly.** 51,872 shared
timestamps, 100.00% identical to the millimetre, largest disagreement 0.0000 m.
The open-data file additionally carries 548 points the API does not return, and
the API carries none the file lacks.

So the file corpus is a strict superset. Backfill from files, not from the API.

## Endpoints, all verified

Base: `https://api-v3.thaiwater.net/api/v1/thaiwater30`

| Path | Returns | Verified |
|------|---------|----------|
| `public/waterlevel_load` | 1,407 stations, current reading | 200, 2.4 MB |
| `public/rain_24h` | 4,433 rain gauges, 24 h total | 200, 4.6 MB |
| `public/rain_today` | 4,499 gauges | 200, 4.3 MB |
| `public/rain_yesterday` | 3,609 gauges | 200, 5.8 MB |
| `public/waterlevel_graph` | one station, 10-min history | 200, see cap below |
| `analyst/cctv` | 106 cameras | 200 |
| `shared/cctv_load` | - | **403**, needs a session |

Returning 404 despite appearing in our June 2026 notes: `dam_daily`,
`dam_load`, `dam_medium_small`, `waterquality_load`, `wl_load_all`,
`situation_level`, `public_warning`, `rain_5m`, `weather_load`,
`sea_waterlevel`, `thaiwater_hourly`. Those notes came from other Oracles via
Discord and were never verified here. Treat that endpoint list as stale.

### waterlevel_graph and its silent cap

```
GET public/waterlevel_graph
  ?station_type=tele_waterlevel
  &station_id=568
  &start_date=2025-01-01 00:00     (urlencode the space)
  &end_date=2026-01-01 00:00
```

**It caps at 52,704 points and does not tell you.** Asking for 2 years, 6.7
years and 14.7 years all returned the identical 52,704 points with HTTP 200.
Window every request to a single year and stitch, or you will silently ingest a
truncated series and never see an error.

Our June 2026 note said this endpoint dies past a 4-day window with a server
500. **That is no longer true** - 365 days returned 52,704 points cleanly.

Response body also carries the rating context, worth storing once per station:
`min_bank`, `warning_level`, `critical_level`, `ground_level`, `qmax`.

## The join key between the two systems

The live API's `station.tele_station_oldcode` is the same string as the
open-data CSV filename. `station_id=568` is `CPY001` is `2025/202511/CPY001.csv`.
That is the whole mapping, and `hii_live.py stations` dumps it as a 1,407-row
CSV.

## Ingest design

```
one-off backfill        2012-2026 year zips  ->  790 MB down, per-station CSV
   hii_pull.py bulk

steady state            waterlevel_load every 10-15 min  ->  1,407 points/poll
   hii_live.py live                                          about 200k/day

monthly reconciliation  new month appears on tiservice  ->  replay over live
   hii_pull.py bulk --from-year <this year>                  rows, authoritative

gap fill only           waterlevel_graph, one station, one year max
   hii_live.py backfill
```

Poll cost at 10-minute cadence: 1,407 water level + 4,433 rain = 5,840 points
per cycle, about 840k points/day. Trivial for Influx.

## Influx schema

`hii_live.py` emits line protocol directly. Timestamps in the API carry no
timezone and are Asia/Bangkok; they are converted to UTC nanoseconds here.

```
water_level,station_code=CPY001,station_id=568,station_type=tele_waterlevel,\
basin=ลุ่มน้ำเจ้าพระยา,agency=สสน.,province=ภาคเหนือ,amphoe=เมืองนครสวรรค์,\
river=แม่น้ำเจ้าพระยา msl=18.73,msl_prev=18.74,storage_percent=59.71,\
diff_wl_bank=7.32,situation_level=3.0 1788418200000000000
```

- tags: `station_code`, `station_id`, `station_type`, `basin`, `agency`, `province`, `amphoe`, `river`
- fields: `msl`, `msl_prev`, `level_m`, `flow_rate`, `discharge`, `storage_percent`, `diff_wl_bank`, `situation_level`
- rain feeds reuse the same tag set with `rain_24h` / `rain_today` / `rainfall`

Sentinels `-999`, `9999`, `999999` are dropped rather than written, so a gap
stays a gap instead of becoming a spike.

```bash
python3 hii_live.py live | curl -s --data-binary @- \
  -H "Authorization: Token $INFLUX_TOKEN" \
  "http://influx:8086/api/v2/write?org=rpro&bucket=hii&precision=ns"
```

## The schema break, and why a naive merge corrupts everything

**The CSV format changed in 2025.** This is the single biggest trap in the corpus
and nothing on the portal warns you about it.

| Years | Header | Missing marker | Files in our pull |
|-------|--------|----------------|-------------------|
| 2012-2024 | `date,time,water_lv` | `-` | 8,072 |
| 2025-2026 | `station_code,measure_datetime,water_level,quality_flag` | `quality_flag` = `null` | 1,492 |

A first pass here concatenated both forms under one header and produced 1.0 GB
of structurally broken CSV that still parsed and still exited 0. The corrected
merge normalises the old form into the new one: **41,910,768 rows, 0 anomalies.**

If RPRO writes its own ingest, normalise on read. Do not trust the header of the
first file you open.

## Quality control, measured not assumed

Across the 85-station Chao Phraya and Tha Chin corpus, 41.9M rows:

| Class | Rows | Share |
|-------|------|-------|
| Plausible readings | 34,874,638 | 83.2% |
| Blank or `-` | 6,991,930 | 16.7% |
| High sentinels | 44,200 | 0.11% |

The high sentinels are `999999` (44,196 rows) plus strays `999976` and `999997`
(4 rows). The documented list of `-999` / `9999` / `999999` does not cover the
strays, so **screen by range, not by an exact list.** Both scripts here reject
anything outside `-900 < v < 9000`.

That is still not enough. A range filter passes physically impossible readings:
CPY001 holds a -20.10 and a 34.86 among 545,346 otherwise clean values, at a
station whose ground level is 7.878 and bank 26.06. Only 62 rows out of 545,346
(0.011%), but they will wreck any min/max or normalisation you compute.

**Gate per station.** `hii_live.py bounds` derives the envelope from one live
snapshot: `bank_level = waterlevel_msl + diff_wl_bank`. Verified against the
graph endpoint's own `min_bank` for CPY001 - derived 26.05, reported 26.06.

```
station_code,station_id,name_th,msl_now,diff_wl_bank,bank_level,accept_min,accept_max
CPY001,568,สะพานเดชาติวงศ์,18.73,7.32,26.05,-3.95,36.05
```

One request gives bounds for all 1,407 stations.

## Data quality, do not skip this

Missing rates differ by an order of magnitude between stations. Measured on the
2025 Chao Phraya and Tha Chin set:

- CPY001 to CPY005 (main stem, นครสวรรค์ down to สรรพยา): 0.1 to 0.3% missing
- ATG162, ATG171 (gates): 39 to 41%
- THA007 บางเลน: 48.6%
- BKK005 คลองภาษีเจริญ: 52.8%

Gate and canal stations are far patchier than the river main stem. Filter on
observed completeness before any of this reaches a forecast.

## What has already been pulled

`~/hii-data/chaophraya-thachin/` - 85 stations, 2012-01 to 2026-07, 41,910,768 rows, 1.3 GB,
เจ้าพระยา plus ท่าจีน. Year archives cached in `~/hii-data/_zips/` (790 MB), so
re-running only fetches what is new.

16 of the 101 matched stations have no files in any year (`AIT001`, `FROC01-02`,
`TCP001-009`, and others) - they are in the metadata but were never published.
