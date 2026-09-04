# HII open data - water level telemetry

Verified working 2026-09-03. No API key, no auth, no registration.

- Catalogue: https://data.hii.or.th/dataset/water-level (CKAN, package `334aa20b-8187-430a-b8c5-d924f37334fe`)
- Data source: https://tiservice.hii.or.th/opendata/data_catalog/water_level/ (plain Apache directory index)
- Owner: สถาบันสารสนเทศทรัพยากรน้ำ (HII / สสน.)
- Licence: **Creative Commons Attribution Non-Commercial**
- `accessible_condition`: ไม่มีการจำกัดการเข้าถึงข้อมูล
- `update_frequency_unit`: เดือน (monthly)

## Three ways in, tested

| # | Channel | Result |
|---|---------|--------|
| 1 | Direct file GET on `tiservice.hii.or.th` | works, http 200, supports range (206) so downloads resume |
| 2 | CKAN `datastore_search` (station metadata only) | works, `datastore_active: true`, paginated JSON |
| 3 | CKAN `datastore_search_sql` | **blocked** - returns a WAF HTML page, not JSON |

Only the metadata resource is loaded into CKAN's datastore. The time-series itself
lives only as files on `tiservice.hii.or.th`, so channel 1 is the one that matters.

## What is actually there

```
water_level/
  0all_stn_metadata.csv     1,396 stations (516 ระดับน้ำ + 880 น้ำฝน), 436 KB
  0zip_file/2012.zip .. 2026.zip     15 year archives, 790 MB total compressed
  2012/ .. 2026/
    YYYYMM/
      0station_metadata.csv
      <STATION_CODE>.csv    ~350-400 stations per month
```

- Cadence: **every 10 minutes** (144 rows/day, 4,320 rows in a 30-day month)
- Unit: ม.รทก. (metres above mean sea level)
- Coverage: **2012-01 through 2026-07**. 202608 onward are empty folders, so
  expect roughly a two-month publication lag.
- **Schema changed in 2025. There are two forms and you must handle both:**

  | Years | Header | Missing marker |
  |-------|--------|----------------|
  | 2012-2024 | `date,time,water_lv` | `-` |
  | 2025-2026 | `station_code,measure_datetime,water_level,quality_flag` | `quality_flag` = `null` |

  I originally wrote "schema is stable" here after checking only 2025 and 2026.
  That was wrong: 35.4M rows across 2012-2024 use the three-column form, and a
  naive concatenation under one header silently corrupts every merged file.
  `hii_pull.py bulk` now normalises the old form into the new one.
- Missing data: `quality_flag` = `null`, and/or `water_level` in `-999`, `9999`,
  `999999`, `-`. Missing rate varies a lot by station-month (0.2% to 17% observed).

## Why this matters to us

The 2026-06-15 retro recorded this as Friction 1: the `api-v3.thaiwater.net`
feed gives only current snapshots, and `waterlevel_graph` dies with a server 500
past about a 4-day window, so we could not build a season-over-season comparison.
This portal closes that gap - 15 years at 10-minute resolution, bulk downloadable.

Verified on the Hat Yai flood, station SLA001 (หาดใหญ่):

| Month | Peak (ม.รทก.) |
|-------|---------------|
| 2025-10 | 3.11 |
| **2025-11** | **9.84** on 24 Nov 06:00 |
| 2025-12 | 4.62 |

ONE037 (สะพานข้ามคลองอู่ตะเภา) peaked 3.23 on 25 Nov 08:00.

**Open discrepancy:** the 2026-06-15 learning file records "Khlong U-Tapao,
station 1109526, peak 2.510m on 26 Nov 2025", sourced from another Oracle via the
thaiwater.net graph endpoint. Measured here, ONE037 peaks at 3.23 on 25 Nov.
`1109526` is a thaiwater.net internal id and `ONE037` is an HII station code -
I have not confirmed they are the same station, so treat both numbers as
unreconciled rather than assuming one supersedes the other.

## Usage

```bash
# which stations exist
python3 hii_pull.py stations --province สงขลา --type ระดับน้ำ

# which months actually hold files
python3 hii_pull.py months --year 2026

# per-station monthly CSVs (skips what it already has)
python3 hii_pull.py pull --station SLA001 ONE037 --from 202510 --to 202512 --out ./hii_data

# whole year in one zip
python3 hii_pull.py year --year 2025 --out ./hii_data

# quick peak / missing-rate summary of what you pulled
python3 hii_pull.py peak ./hii_data/*.csv
```

## Central Thailand pull (Chao Phraya + Tha Chin)

Water-level stations by basin, from the 516 in the metadata:

| Basin | Stations |
|-------|----------|
| เจ้าพระยา | 80 |
| ท่าจีน | 21 |
| ป่าสัก | 10 |
| แม่กลอง | 9 |
| สะแกกรัง | 5 |
| **central region total** (`Region_name` = ภาคกลาง) | **161** |

The Chao Phraya + Tha Chin set is 101 stations. Of those, 69 have 2025 files;
the other 32 only appear in earlier years, so pull the full range to get them.

Pull the whole thing with the `bulk` verb, which fetches year archives once and
extracts only the stations you asked for, merged into one file per station:

```bash
python3 hii_pull.py bulk --basin เจ้าพระยา ท่าจีน \
  --from-year 2012 --to-year 2026 \
  --cache ~/hii-data/_zips --out ~/hii-data/chaophraya-thachin
```

Cost: 790 MB of archives downloaded once, about 2.6 GB of merged CSV out.
Archives are cached and re-runs skip whole files, so extending the year range
later costs only the new years. **Keep the output out of this repo** - leica-oracle
is public and this is 2.6 GB of third-party CC BY-NC data.

### Data quality is very uneven, check before you model

2025, 69 stations, 3.6M rows, 12.4% missing overall - but the spread is what matters:

| Station | Name | Missing |
|---------|------|---------|
| CPY001-005 | สะพานเดชาติวงศ์ down to สรรพยา | 0.1-0.3% |
| CPY013 | บางไทร | 3.3% |
| ATG162 | ท้ายปตร.ยางมณี | 39.3% |
| ATG171 | เหนือปตร.ผักไห่-เจ้าเจ็ด | 41.4% |
| THA007 | บางเลน | 48.6% |
| BKK005 | คลองภาษีเจริญ | 52.8% |

The CPY main-stem chain (นครสวรรค์ -> ชัยนาท -> สิงห์บุรี -> อ่างทอง -> อยุธยา -> บางไทร)
is the clean spine. Gate and canal stations are far patchier.

### Caveat on the flood-wave demo

Taking each station's November 2025 monthly maximum, most of the main chain
clusters at +40 to +46 hours after CPY001, with บางไทร at +56h. That looks like a
wave travelling downstream, but CPY004, CPY011 and CPY012 do not fit the ordering,
and monthly max is too crude to separate one wave from another. Treat it as
evidence the data is usable, **not** as a measured travel time.

## Constraint to respect

CC BY-NC. Fine for research and for the PhD Oracle PM2.5/flood work. **RPRO is a
commercial platform** - check the licence before any of this reaches a paying
deployment. Attribute HII on anything published.
