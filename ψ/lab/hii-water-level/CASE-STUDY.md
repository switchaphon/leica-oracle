# HII water data: from "have we ever used this?" to a running pipeline

**Built** 2026-09-03 13:24 to 2026-09-04 10:12 GMT+7 (20h 49m wall clock, one session)
**By** Leica Oracle, for Witchaphon
**For** rpro-ent-oracle - this is your domain, and the licence question at the end is yours to answer

**Read as a page** https://claude.ai/code/artifact/5a4d74f9-4136-49ab-b2e3-30366a090700
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

Two hosts, and they are not interchangeable. (A third, on a near-identical name, turned up a day later and is covered in trap 3.18 - everything in this section describes `api-v3.thaiwater.net`, not `twa-api-public.thaiwater.net`.)

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

## 3. Twenty-five traps, each found by measuring rather than assuming

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


### 3.7 `rain_24h` IS a real rolling window - settled by joining two endpoints

An earlier draft argued this from `rain_24h >= rain_1h in 426/426 raining stations`.
rpro-ent-oracle correctly rejected that: a since-midnight accumulator is ALSO
always >= the last hour, so 426/426 shows only that the sample avoided midnight.

The observation that separates them needs no history. `rain_24h` and `rain_today`
are separate endpoints; pull both in the same minute and join by station. If
`rain_24h` were since-midnight under a misleading name it would have to EQUAL
`rain_today`.

Measured 2026-09-04 11:10 +07, 3,737 stations with both values numeric:

| relation | stations |
|---|---|
| `rain_24h` > `rain_today` | **2,202** |
| `rain_24h` == `rain_today` | 1,434 |
| `rain_24h` < `rain_today` | 101 (see 3.8) |

Largest gap: `rain_24h` = 129.00 mm while `rain_today` = 0.00 mm. A since-midnight
total cannot report 129 mm on a day that has recorded nothing. The rain fell before
midnight and is still inside the window.

**`rain_24h` is a genuine rolling 24-hour window.** It remains non-summable across
stations for the same reason as before; only `rain_1h` and the bulk `rainfall_1h`
column are summable.

### 3.8 `rain_today` is 63% stale, with live values dated as far back as 2017

The 101 stations where `rain_24h < rain_today` are not a rainfall anomaly. They are
dead gauges whose last reading is frozen and never marked:

```
24h=  9.00 @ 2026-09-04 09:00   |   today= 145.00 @ 2025-10-22 08:00
24h=  3.50 @ 2026-09-04 09:00   |   today= 105.50 @ 2026-07-14 07:00
```

Counted across each endpoint on 2026-09-04:

| endpoint | records | timestamp not today | non-zero AND stale |
|---|---|---|---|
| `rain_today` | 4,499 | **2,836 (63.0%)** | **274** |
| `rain_24h` | 4,461 | 1 (0.0%) | 1 |

Stale years present in `rain_today`: 2017 x5, 2018 x84, 2019 x50, 2020 x22,
2021 x43, 2022 x26, 2023 x58, 2024 x37, 2025 x122.

`sum(rainfall_value)` over `rain_today` silently folds 274 non-zero readings, some
from 2017, into a figure presented as today's rainfall.

rpro-ent-oracle pushed back on the 63% headline, correctly: at 11:10 a gauge that
reports once daily at 18:00 shows yesterday's date and is perfectly healthy, so
"timestamp is not today" could conflate DEAD with HAS NOT REPORTED YET. Bucketing
the same 2,836 by **age** rather than by date settles it without a second run:

| age of stale record | count |
|---|---|
| < 24 h | **0** |
| 1-2 days | 6 |
| 2-7 days | 9 |
| 7-30 days | 1,894 |
| > 30 days | 927 |

The population the cadence hypothesis requires does not exist. 2,821 of 2,836
(99.5%) are seven days or older. These are dead gauges, not late ones.

**The same staleness breaks two aggregations in opposite directions:**

| subset | count | effect |
|---|---|---|
| stale AND non-zero | 274 | **inflates** `sum()` |
| stale AND zero | 2,562 | **deflates** `mean()`, and inflates any coverage count |

The mean moves less than expected - 0.7802 mm over all 4,499 versus 0.8334 mm over
the 1,663 fresh, only 1.07x - because most fresh stations also read zero. The severe
damage is to **coverage**: 4,499 records presented as reporting stations against
1,663 actually fresh is a **2.7x overstatement**.

Defence: filter on `rainfall_datetime` before reading `rainfall_value`.

### 3.9 Switching to `rain_24h` costs 762 rows - and recovers 2,798 live gauges

`rain_today` returns 4,499 and `rain_24h` returns 4,461, so the naive reading is
that 38 stations are lost. That is a *net* difference, not an overlap. The anti-join:

| direction | stations |
|---|---|
| in `rain_today`, not in `rain_24h` | **762** |
| in `rain_24h`, not in `rain_today` | **724** |

762 - 724 = the 38 the counts show. The real exposure is twenty times the apparent one.

The recommendation survives only because of what those 762 are: exactly **1** carries
a today timestamp and **0** have non-zero rain today. The coverage lost by preferring
`rain_24h` is almost entirely dead gauges. Never take a net record-count difference
as a coverage delta - anti-join both directions.

**Corrected after rpro-ent-oracle pointed out the ledger was half-counted.** The
anti-join above measures only what switching *costs*. Counting what it *recovers*
reverses the conclusion entirely:

| | rows | fresh | raining now |
|---|---|---|---|
| lost - in `rain_today` only | 762 | **1** | 0 |
| gained - in `rain_24h` only | 724 | 724 | 298 |
| in both, frozen in `rain_today` but **live** in `rain_24h` | 2,074 | 2,074 | 1,245 |

**Live gauges recovered: 2,798. Live gauges lost: 1.** The 1,245 recovered stations
that are raining right now carry **15,082.5 mm** of rainfall that `rain_today` is
currently showing as frozen or zero.

The error in the first version was not arithmetic. It was asking only what the switch
would cost, because the recommendation was already written and the question had become
how to defend it. Anti-joining in one direction answers half a ledger and reads like
diligence.

### 3.10 Units - a bound is one-sided, and this one is still untested

`rain_24h` across 4,461 records: min 0.00, max 176.20, median 0.60. Nothing above
500 mm, nothing above the 1,825 mm world 24-hour record, nothing negative.

That result is weaker than it looks. **A physical bound only catches inflation.** If
the field were centimetres or inches, 176.20 would read 17.6 or 6.9 and pass the
identical check. So a raw tick-count or a 10x-inflated unit is ruled out; mm versus
cm versus inch is not. Settling that needs an external reference for one station on
one day, not a bound.

This completes a family of three:

| the name lies about | what it corrupts | what catches it |
|---|---|---|
| **where** the value is (3.6) | a false zero | `print(list(rec.keys()))` |
| **when** the value is from (3.8) | a real but wrong value | the record's own timestamp |
| **units** the value is in (3.10) | every value, uniformly | a physical bound - and only against inflation |

This is trap 3.6 one layer deeper. **3.6 is a field name that lies about WHERE the
value is; 3.8 is a field name that lies about WHEN the value is from.** Printing
`list(rec.keys())` catches the first and cannot catch the second.

### 3.11 The staleness is not decay - one agency's feed stopped at a single minute

rpro-ent-oracle read the shape of the age histogram and rejected the attrition
reading: two thirds of all staleness inside one 23-day window is the signature of an
event. Re-bucketing the 1,894 by exact last-report date settles it:

| last reported | gauges |
|---|---|
| **2026-08-06** | **1,846 (97.5%)** |
| the other 19 dates in the window, combined | 48 |

And within that day, by timestamp: **1,807 stopped at 07:15**, 36 more at 07:00.

By agency: **1,843 of the 1,846 belong to ทน.** (Department of Water Resources).
In `rain_today`, ทน. has 2,220 stations and **zero** reporting today.

**But the gauges are not dead.** In `rain_24h`, ทน. has 1,992 stations, 1,991 with a
today timestamp, and 1,207 recording rain right now - including the 129.00 mm station
that settled trap 3.7. `rain_today` reports 0.00 mm for the gauge measuring the
heaviest 24-hour rainfall in the country.

The correct statement is therefore neither "1,846 gauges died" nor "the endpoint is
63% rotten". It is: **`rain_today` stopped ingesting the ทน. network at 2026-08-06
07:15 and has not resumed in 29 days, while the same physical sensors continue to
feed `rain_24h` normally.** The endpoint hides the outage by returning the rows with
frozen values rather than omitting them.

The remaining 927 records older than 30 days *are* genuine attrition - spread across
256 distinct dates, largest single date 9.9%. Two populations, two different actions.

### 3.12 Correction: the trap 3.7 evidence was contaminated by trap 3.11

The 2,202 / 1,434 / 101 join in trap 3.7 compared live `rain_24h` values against
`rain_today` rows that, for every ทน. station, were frozen at 2026-08-06. That is not
"today's accumulation versus a 24-hour window", it is "today versus a dead value", and
it inflated the very count the argument rested on.

Re-run restricted to the 1,662 stations whose timestamp is today on **both** sides:

| relation | stations |
|---|---|
| `rain_24h` > `rain_today` | **990** |
| `rain_24h` == `rain_today` | 640 |
| `rain_24h` < `rain_today` | 32 |

Largest clean gaps: 176.20 against 6.60, and 88.40 against 0.00. A since-midnight
total cannot read 88.40 mm while today reads 0.00 at a station that *is* reporting
today. **The rolling-window conclusion holds, now on uncontaminated data.**

The lesson is narrower than the traps around it: a freshness filter is not only a
defence for the values you report, it is a precondition for any comparison you draw
between two feeds. Trap 3.8 was discovered while testing trap 3.7, and then turned
out to have been corrupting trap 3.7's evidence all along.

### 3.13 Units, closed further: a bound cuts more than one way

rpro-ent pointed out the bound was under-credited. Rather than asking whether 176.20
exceeds a limit, ask what 176.20 *means* under each candidate unit:

| if the unit were | 176.20 becomes | verdict |
|---|---|---|
| mm | 176.2 mm/24h | plausible |
| cm | 1,762 mm/24h | survives the 1,825 mm bound |
| inch | 4,475 mm/24h | **already excluded by the measured max** |

So inches died on data already in hand. Centimetres is not excluded by the bound - it
is excluded by requiring today to have produced the second-heaviest 24-hour rainfall
ever recorded on Earth, in Thailand, unremarked. Say that plainly rather than let the
bound take credit for it.

Had the maximum been 8.0 instead of 176.20, nothing would have been excluded. The
bound worked here only because the conversion factors happen to run in the inflating
direction.

To close cm formally without a third party: the bulk `hourly_rain/` corpus carries
`rainfall_1h` for the same stations. One matching station-hour against the API's
`rain_1h` fixes the units to whatever the bulk files document. **Not yet run.**


### 3.14 The bulk corpus has directories for months it has no data for

Closing the unit question needed a station-hour present in both the API and the bulk
`hourly_rain/` corpus. There is none: **the corpus stops at 2026-07.** Directories
exist for all twelve months of 2026, December included; `202608`, `202609` and
`202610` are empty.

| month | files |
|---|---|
| 202606 | 1,750 |
| 202607 | 1,750 |
| 202608 | **0** |
| 202609 | **0** |
| 202610 | **0** |

A directory listing implies coverage the corpus does not have - the same shape as
trap 3.11's frozen rows. Structure present, content absent, no error either way.

### 3.15 Units closed: millimetres, settled on a monthly total

With no overlapping station-hour, a single reading could not do it. A complete month
can, because monthly rainfall has a climatological bound a single hour does not.

`FOP001` (บ้านร้องแง, Nan), July 2026, 744 rows - a complete month:

| if the unit were | peak hour | July total | verdict |
|---|---|---|---|
| **mm** | 24.2 mm/h | **314.4 mm** | northern Thailand in July runs 150-300 mm. Correct. |
| cm | 242.0 mm/h | 3,144 mm | exceeds Thailand's *annual* rainfall, in one month |
| inch | 614.7 mm/h | 7,986 mm | double the world one-hour record, sustained monthly |

**The bulk corpus is in millimetres.** The API agrees by consistency rather than by
identity: the same station read `rain_1h` = 24.40 today, against a bulk July peak of
24.2 mm/h, under near-identical field names. That is a distributional match, not the
exact station-hour match the corpus lag made impossible - worth stating as what it is.

A confession belongs here, because it is the same trap committed while documenting it:
the first pass read the CSV **by position** (`r[-1]`) and returned `quality_flag`
instead of the value. Reading by name fixed it. Trap 3.6 does not stop applying to
the person writing trap 3.6 down.

### 3.16 The unattributed dams are not RID's - with a positive control

`dam.dam` carries `rid_guid` and `rid_office`. Pulled fresh from `analyst/dam`:

| agency | dams | carrying a RID id |
|---|---|---|
| ชป. (RID) | 585 | **481 (82.2%)** |
| ทน. | 60 | 0 |
| สสน. | 60 | 0 |
| กฟผ. | 16 | 0 |
| **unattributed** | **235** | **0** |

The control matters more than the result: the field is only usable as evidence
because it reaches 82% inside RID and produces zero false positives in every other
agency. Absence then means something. Were the 235 RID's, roughly 193 would be
expected to carry the identifier; zero do.

**The RID route does not reach the unattributed dams.** Any route sizing that assumes
they might be RID's is overstated.

Note on reproducibility: this pull gives 989 rows, **958 unique by `dam.id`** - ชป.
585, unattributed 235, กฟผ. 16. Earlier figures circulated in this thread as 838
unique / 569 / 5 / 203, from a session whose dedup method these lab files do not
record. The two do not reconcile and the earlier numbers should stay labelled
reported-not-verified. The conclusion above is unaffected: zero of the unattributed
carry a RID identifier under any dedup.

### 3.17 `r[-1]` is version-dependent, and there is no cutoff year to memorise

I read a bulk CSV by position while writing up trap 3.6, and got `quality_flag`
instead of the rainfall value. rpro-ent-oracle diagnosed it as a consequence of the
2025 schema change in trap 3.2. The mechanism is right; the boundary is not, and the
real shape is worse than a single cutoff.

Measured across the `hourly_rain` corpus:

| period | header | `r[-1]` returns |
|---|---|---|
| 2013 - early 2024 | `date,time,rain` | **`rain`** - the value |
| later | `station_code,measure_datetime,rainfall_1h,quality_flag` | **`quality_flag`** - a flag |

The transition is not at 2024/2025. `202309` through `202403` are all still the old
form, and then:

| station | 202403 | 202407 | 202507 |
|---|---|---|---|
| FOP001 | old | **new** | new |
| ABRT | old | *(no file)* | **new** |

So the rain corpus changed *during* 2024, and **the transition month differs by
station**, because a station with a data gap crosses the boundary invisibly. Trap 3.2
meanwhile records `water_level` changing at 2024/2025. Two corpora with what the
portal calls an identical layout changed schema at different times.

**There is therefore no cutoff year to memorise, for any corpus. Read the header of
every file.** This also narrows an earlier claim in section 2: `hii_pull.py` works
across corpora by changing one path - true for the path, false for the parse.

The slip is worth recording rather than quietly fixing. It happened on a 2026 file,
where `r[-1]` had already been a flag for two years, in the middle of writing the
trap about names that do not mean what they appear to. Knowing the rule and holding
it are different things.

### 3.18 A second API exists on a near-identical name, and disagrees

Everything above concerns `api-v3.thaiwater.net`. On 2026-09-04 a question about a
map URL turned up **`twa.thaiwater.net`**, a Next.js rebuild running on a different
API host, `twa-api-public.thaiwater.net`. Both are live. Neither is a replacement
for the other.

| | `api-v3.thaiwater.net` | `twa-api-public.thaiwater.net` |
|---|---|---|
| Auth | none | `x-api-key` required, 401 without |
| Water level stations | 1,407 | 791 |
| CCTV cameras | 106 | 85 |
| Rain gauges | 4,433 (`rain_24h`) | 2,696 (`rainfall_c1440`) |
| Error language | Thai / English | **Chinese** |

The counts differ because the station sets differ, not because one is stale. The
danger is that both answer to "the ThaiWater API" in conversation, so a figure
quoted from one lands in a document sourced from the other and nothing looks wrong.

**Name the host beside every number.** Section 2's table now describes one of two
sources, not the source.

### 3.19 A count of the top-level keys is not a count of the records

The new API's map routes return `{data: {"<provinceCode>": FeatureCollection}}`.

`len(data)` on `/v2/cctv` is **44**. The camera count is **85**. The keys are
provinces. Flattening is one line, and omitting it produces a number that is
plausible, stable, reproducible and wrong:

```python
rows = [f for fc in payload["data"].values() for f in fc["features"]]
```

I published 44 to myself first. What caught it was the sibling route `/v2/cctv/list`
reporting `totalItems: 85` - two routes disagreeing. A single route read naively
offers nothing to disagree with.

### 3.20 "No permission" was a missing parameter

`/data/platform/v1/public/media?mediaTypeId=30` returns HTTP 500 with
`{"code":1006,"message":"无操作权限"}` - "no operation permission".

That is not the problem. The endpoint requires `startDate` and `endDate`; supplied,
it returns 27 radar image records. The permission reading was falsifiable and I
falsified it before acting on it: `GET /auth/get-public` returns the anonymous
role's manifest, and diffing it against the 159 dataset keys the page declares gives
**159 granted, 0 denied**, radar included.

An error string is the server's theory of what went wrong. It is not evidence.
Reading this one at face value would have cost the entire radar catalogue - the
largest single find of the session.

### 3.21 A hardcoded flag in the vendor's own code 404s the vendor's own images

Media records carry an obfuscated `mediaPath` blob, redeemed at
`platform.thaiwater.net/api/v1/public/media/view`. The site's bundle contains exactly
one URL builder for it, with `isStaticFile=true` baked in. Applied to any radar frame
that returns **404**.

I nearly recorded the radar images as unreachable. The positive control is what
prevented it: the same base URL with a water level cross-section `mediaPath` returned
a 9,004-byte PNG, so host and route were correct and only the flag was wrong.
`isStaticFile=false` returns the frame - 128,784 bytes of JPEG.

Two media classes, one flag, no documentation. **A 404 means "not at that URL", never
"not available"** - and copying the vendor's own call is not a control, because the
vendor calls it correctly somewhere you have not read.

### 3.22 A timezone suffix can be the thing that lies

Trap 3.8 was a name lying about *when*. This is the same failure one level lower, in
the field designed to prevent it.

TMD radar records report `mediaDatetime` as `2026-09-04T09:00:00+07:00` while the
wall clock read 17:11 +07. Taken literally: a seven-hour-old frame from a
fifteen-minute product. The value is the UTC wall clock with `+07:00` appended.

Three independent confirmations, none of which required waiting:

- the filename, `ubn240_202609040900.jpg`, carries the same `0900`
- across the afternoon the newest frame tracked UTC-now minus about 20 minutes
- **the rendered image's own footer reads `CHU 2026-09-04 09:45:00`** - the radar
  stamps its own picture, and it stamps it in UTC

And the convention is not uniform across the one endpoint. `rasisalai` reports
`16:41:06+07:00`, which is true local time - but it is the *ingest* time, while its
filename says `0930`, the frame time.

| field | what it actually holds |
|---|---|
| `mediaDatetime`, most sites | frame time in UTC, labelled `+07:00` |
| `mediaDatetime`, rasisalai | local ingest time, not frame time |
| `filename` | frame time in UTC, on all 40 sites |

**Parse the filename.** It is the only clock that means the same thing at every site.

A timestamp with an explicit offset reads as self-describing, which is why this one
survives: the field that would normally settle the question is the field doing the
lying.

### 3.23 The radar on the map is not Thai

The page's layer code is `rr`, "radar-rain", on a Thai government water portal. The
natural reading is TMD or HII radar.

A browser network capture shows the map painting tiles from
`tilecache.rainviewer.com` - **RainViewer**, a third-party global service, 13 frames
at 10-minute spacing. Thai radar exists on the same site but is a different product
entirely: 40 individual station images, JPEG and CAPPI PNG, not tiles.

This matters twice. Anyone asking for "the radar layer this map shows" gets a
third-party feed under third-party terms, not HII's. And anyone who assumes the
attribution follows the domain will attribute it wrongly.

**Provenance does not inherit from the page it is displayed on.**

### 3.24 `isActive: true`, HTTP 200, and a valid JPEG - all three can be false

All 85 cameras in the new API report `isActive: true`. Following that flag to the
pixels:

| stage | count |
|---|---|
| registered, `isActive: true` on every one | 85 |
| carrying a URL | 64 |
| distinct hostnames | 57 |
| **hostnames that resolve in DNS** | **10** |
| returning a JPEG | 8 |
| **EXIF timestamp matching the wall clock** | **4** |

All 44 `dyndns.org` hostnames are NXDOMAIN; that whole domain family has lapsed.

Then the survivors split again. เขื่อนสิรินธร returns HTTP 200 and a structurally
perfect JPEG with **15/06/2024** burned into the overlay - a frozen frame more than
two years old. เขื่อนรัชชประภา carries EXIF from 2026-07-28. Four cameras carry EXIF
within seconds of now and are genuinely live.

Three defences stack, each catching what the previous one passes: DNS resolution
catches the dead host, HTTP 200 catches the dead service, and only the **EXIF
timestamp inside the image** catches the live service serving a dead picture.

Before concluding any of this I proved the tester could detect a success:
`http://example.com` returned 200 and `http://portquiz.net:5001` returned 200, so
plain HTTP and the non-standard port both work from this machine. Without that
control, "every camera is unreachable" and "my sandbox blocks this" produce an
identical result - and the wrong one of those is a much more comfortable conclusion
to reach about someone else's system.

### 3.25 An error I caused, read back as a property of the system

I tested pagination on the new API by sending `pagination[page]=2` alone and getting
`400 INVALID_DATA`, then `page=2` alone and getting page 1 back. I wrote down that
`/v2/cctv/list` was hard-capped at ten rows with pagination broken.

Then a browser capture showed the site issuing:

```
/v2/agency?pagination[pageSize]=-1&pagination[page]=1&dataset=weather   -> 200
```

**Both parameters are required together.** Sent as a pair, `/v2/cctv/list` returns
all 85. There was no cap. There was a malformed request, and I had promoted it to a
finding about someone else's API.

This is trap 3.9's shape in a different domain - there I answered half a ledger
because the recommendation was already written; here I described my own error as a
limitation because the error arrived first and nothing contradicted it. Both are the
same move: treating the absence of a contradiction as evidence.

`pageSize=-1` is separately unreliable, working on `/v2/agency` and returning 0 rows
on `/v2/cctv/list` - so the correct advice is an explicit page size, or the map route,
which needs no paging at all.

**An error you produced is not a property of the system.** Reproduce the working
client's exact call before writing down a limitation.

## 4. The finding that is not about data quality

> **`rain_today` reports 0.00 mm for the gauge currently recording the heaviest
> 24-hour rainfall in the country.**

Everything above - the 63%, the 2,836, the age histogram - is supporting detail for
that one sentence. Anyone using `rain_today` for flood awareness has been told there
is no rain at the wettest station in Thailand, every day for 29 days.

The mechanism is the part worth carrying to other systems:

> **Omission would have been caught on day one. Freezing looks like complete data.**

Had the endpoint dropped the ทน. rows when their ingest died, every consumer would
have seen the row count fall by 2,220 on 2026-08-06 and investigated that morning.
By returning the rows with their last-known values instead, it presents a complete,
plausible, and entirely current-looking dataset. rpro-ent-oracle reports the same
shape in their own `device_lasts` freeze, which makes this a cross-system pattern
rather than one vendor's bug.

**The defect to report is not "data is missing". It is "rows are returned instead of
omitted, so the outage is invisible downstream."** That distinction is the fix.


## 5. Implementation design

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

## 6. The join key between the two systems

`station.tele_station_oldcode` in the live API is byte-identical to the open-data filename. `station_id=568` is `CPY001` is `2025/202511/CPY001.csv`. That is the whole mapping, and `hii_live.py stations` dumps it as a CSV.

---

## 7. Design: what "glow in the dark" cost, and what measurement caught

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

## 8. What it cost

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

## 9. What this means for RPRO specifically

1. **The licence blocks commercial use, and no script fixes that.** The open data portal states Creative Commons Attribution **Non-Commercial**. RPRO is a commercial platform. `api-v3.thaiwater.net` publishes no terms at all, which makes its status unknown rather than permissive - do not read silence as consent. This needs written permission from HII before any of it reaches a paying deployment. Everything else is ready the moment that is settled.

2. **Take the traps, not just the code.** Sections 3.1 to 3.6 are six ways to build something that runs green and reports wrong numbers. Any team integrating this source will hit them; the difference is whether they hit them before or after someone acts on the output.

3. **`analyst/dam` is the biggest find and it is not in our old notes.** 989 dams with inflow, release, spill, evaporation and losses - a closed water balance, updated daily. For a water management platform this is more valuable than river level. Dedupe by `(dam_name, agency)` first.

4. **`ratingcurve` turns level into volume.** Without it a level series is a number, not water accounting. It is a separate CKAN dataset (`ffba6c62-...`), Elevation-Capacity-Area curves, distributed through `gisservice.hii.or.th`.

5. **Rainfall history has the identical bulk layout.** `hourly_rain/` and `daily_rain/` on tiservice, 2012-2026, same directory shape as `water_level/`. `hii_pull.py` works on them by changing one path. Level without rain gives a model no forcing input.

6. **`dam_yearly_graph` looks like the prize and is not usable as served.** Upper and lower rule curves, 13,908 points - but across only 366 distinct dates, so 38 dam series are concatenated with no identifier on any point, and the endpoint ignores `dam_id`. Someone has to work out how the frontend selects one dam before this is worth anything. Flagging it as open, not solved.

---

## 10. Where the code is

`leica-oracle/ψ/lab/hii-water-level/`

| File | What |
|---|---|
| `hii_pull.py` | bulk / pull / year / basins / months / peak - the file corpus |
| `hii_live.py` | live / backfill / stations / bounds - Influx line protocol out |
| `waterviz/ingest.py` | 8-basin ingest to SQLite + page snapshot |
| `waterviz/radar.py` | bakes a RainViewer rain radar loop into the page as data URIs |
| `waterviz/layers.py` | bakes the rain-gauge and CCTV layers from the twa API, probing each camera |
| `waterviz/refresh.sh` | cron entry, run lock, live and full modes |
| `waterviz/page.template.html` | the page, single file |
| `CURL.md` | every endpoint as a runnable curl, all executed |
| `RPRO-INGEST.md` | ingest spec written for your side |
| `WATER-APIS.md` | the full survey of what exists |
| `../twa-thaiwater/twa_pull.py` | the second API - rainfall, water level, CCTV, radar |
| `../../learn/thaiwater/twa/twa.md` | the second API, written up in full |

Data lives outside git at `~/hii-data/` - 2.2 GB of CC BY-NC third-party data has no business in a public repo.

---

*Written by Leica Oracle (AI, ไม่ใช่คน). Every number here was measured in-session; where something is unverified it says so.*