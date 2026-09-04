# HII / ThaiWater - curl cheat sheet

Every command below was executed successfully on 2026-09-03. No API key, no auth.
Needs `jq` for the JSON ones (`brew install jq`).

## Files - the historical corpus (tiservice.hii.or.th)

```bash
BASE=https://tiservice.hii.or.th/opendata/data_catalog/water_level

# 1,396 stations: code, name, lat/lon, basin, province, type
curl -s "$BASE/0all_stn_metadata.csv" -o stations.csv

# one station, one month - 10-minute readings, 4,320 rows
curl -s "$BASE/2025/202511/SLA001.csv" -o SLA001_202511.csv

# what years exist (2012 through 2026)
curl -s "$BASE/" | grep -o 'href="20[0-9][0-9]/"'

# what months actually hold files
curl -s "$BASE/2026/" | grep -o 'href="20[0-9]*/"'

# which stations reported in a month
curl -s "$BASE/2025/202511/" | grep -o 'href="[A-Z0-9]*\.csv"'

# a whole year, every station, one zip (40-70 MB, resumable with -C -)
curl -# -L -C - "$BASE/0zip_file/2025.zip" -o 2025.zip
```

Header changed in 2025. `date,time,water_lv` before, then
`station_code,measure_datetime,water_level,quality_flag`. Normalise on read.

## CKAN catalogue API (data.hii.or.th)

Metadata only. The time-series is never loaded into the datastore.

```bash
CKAN=https://data.hii.or.th/api/3/action

# filter stations - use `filters`, not `q`. Thai full-text search returns 0.
curl -sG "$CKAN/datastore_search" \
  --data-urlencode 'resource_id=47274e2b-c905-4762-b025-11ca9067d107' \
  --data-urlencode 'filters={"Province_Name":"ชัยนาท","Station_Type_Name":"ระดับน้ำ"}' \
  --data-urlencode 'limit=100' | jq -r '.result.records[] | [.Station_Code,.Station_Name] | @tsv'

# page through with offset
curl -sG "$CKAN/datastore_search" \
  --data-urlencode 'resource_id=47274e2b-c905-4762-b025-11ca9067d107' \
  --data-urlencode 'limit=100' --data-urlencode 'offset=100' | jq '.result.total'

# what else is on the portal (36 packages)
curl -s "$CKAN/package_list" | jq -r '.result[]'
curl -s "$CKAN/package_show?id=334aa20b-8187-430a-b8c5-d924f37334fe" \
  | jq -r '.result.resources[] | [.format,.name,.url] | @tsv'
```

`datastore_search_sql` is blocked by a WAF - it returns an HTML page, not JSON.

## Live API (api-v3.thaiwater.net)

```bash
API=https://api-v3.thaiwater.net/api/v1/thaiwater30/public

# current level, all 1,407 stations
curl -s "$API/waterlevel_load" | jq '.waterlevel_data.data | length'

# Chao Phraya basin, live
curl -s "$API/waterlevel_load" \
| jq -r '.waterlevel_data.data[]
         | select(.basin.basin_name.th == "ลุ่มน้ำเจ้าพระยา")
         | [.station.tele_station_oldcode, .station.tele_station_name.th,
            .waterlevel_msl, .diff_wl_bank, .waterlevel_datetime] | @tsv'

# stations currently over bank
curl -s "$API/waterlevel_load" \
| jq -r '[.waterlevel_data.data[]
          | select(.diff_wl_bank != null and (.diff_wl_bank|tonumber) <= 0)] | length'

# top rainfall in the last 24 h
curl -s "$API/rain_24h" \
| jq -r '[.data[] | select(.rain_24h != null)] | sort_by(.rain_24h|tonumber) | reverse
         | .[0:10][] | [.rain_24h, .station.tele_station_name.th,
                        .geocode.province_name.th] | @tsv'

# historical, one station. station_id 568 is CPY001 สะพานเดชาติวงศ์.
curl -sG "$API/waterlevel_graph" \
  --data-urlencode 'station_type=tele_waterlevel' \
  --data-urlencode 'station_id=568' \
  --data-urlencode 'start_date=2025-11-01 00:00' \
  --data-urlencode 'end_date=2025-12-01 00:00' \
| jq -r '.data | "bank=\(.min_bank) ground=\(.ground_level) points=\(.graph_data|length)"'

# the id -> code join table
curl -s "$API/waterlevel_load" \
| jq -r '.waterlevel_data.data[]
         | [.station.id, .station.tele_station_oldcode,
            .station.tele_station_name.th] | @tsv' > join.tsv
```

**`waterlevel_graph` caps at 52,704 points and says nothing.** Ask for 14 years,
get one year back with HTTP 200. Window one year per request, always.

## Dams - `analyst/dam`

One call returns four sections: `dam_daily` (large), `dam_medium`,
`dam_small_tele`, `dam_hourly`. Per dam you get a closed water balance:
`dam_storage`, `dam_storage_percent`, `dam_inflow`, `dam_released`,
`dam_spilled`, `dam_losses`, `dam_evap`, `dam_level`, `dam_uses_water`.

```bash
API=https://api-v3.thaiwater.net/api/v1/thaiwater30

# section sizes
curl -s "$API/analyst/dam" | jq -r '.data | to_entries[] | "\(.key)\t\(.value|length)"'

# large dams, fullest first
curl -s "$API/analyst/dam" \
| jq -r '.data.dam_daily[]
         | [.dam.dam_name.th, .dam_storage, .dam_storage_percent,
            .dam_inflow, .dam_released, .dam_spilled] | @tsv' \
| sort -t$'\t' -k3 -rn

# rule curves - present, but NOT usable as served (see caveat below)
curl -s "$API/analyst/dam_yearly_graph" | jq -r '.data | keys[]'
curl -s "$API/analyst/dam_yearly_graph" \
| jq -r '(.data.upper_rule_curve|length) as $p
         | ([.data.upper_rule_curve[].date]|unique|length) as $d
         | "\($p) points / \($d) dates = \($p/$d) series concatenated"'
```

**Rule curve caveat.** 13,908 points span only 366 distinct dates, so 38 dam
series are concatenated into one array. Each point carries `date` and `value`
and nothing else - no dam identifier. Passing `dam_id`, `dam` or `id` changes
nothing, the response is byte-identical. The data is there but you cannot tell
which dam a value belongs to, so treat this endpoint as unresolved rather than
as a ready reference.

### The double-count trap - read this before you sum anything

`dam_daily` returned **50 rows for 39 distinct dams**. Eleven dams are reported
by both ชป. (RID) and กฟผ. (EGAT), on different dates, and the two disagree
badly on percentage even when storage is identical:

```
รัชชประภา   2026-09-03  storage 3701.67  pct 65.65  ชป.
รัชชประภา   2026-09-02  storage 3701.67  pct 77.76  กฟผ.
อุบลรัตน์    2026-09-03  storage  872.93  pct 35.91  ชป.
อุบลรัตน์    2026-09-02  storage  872.93  pct 81.26  กฟผ.
บางลาง      2026-09-03  storage  794.38  pct 54.62  ชป.
บางลาง      2026-09-02  storage  794.38  pct 0      กฟผ.
```

Storage agrees, percent does not - the two agencies clearly divide by different
capacity denominators, and some กฟผ. rows carry a flat 0.

A naive sum gives **93,647 MCM**. Deduplicating to the newest row per dam gives
**49,033 MCM**. The naive figure overstates by 91%.

```bash
# correct national total: newest row per dam, then sum
curl -s "$API/analyst/dam" \
| jq -r '[.data.dam_daily[] | select(.dam_storage != null)]
         | group_by(.dam.dam_name.th)
         | map(max_by(.dam_date))
         | map(.dam_storage|tonumber) | add | floor'
```

Key on `(dam_name, agency)` and pick a reporting agency deliberately. Do not
trust `dam_storage_percent` across agencies without knowing the denominator.

## Water gates - `public/watergate_load`

2,315 structures with control state, not just levels: `watergate_in`,
`watergate_out`, `watergate_out2`, `pump_on`, `pump`, `floodgate_open`,
`floodgate`, `floodgate_height`.

```bash
# head difference across each structure
curl -s "$API/public/watergate_load" \
| jq -r '.watergate_data.data[]
         | select(.watergate_in != null and .watergate_out != null)
         | [.station.tele_station_name.th, .watergate_in, .watergate_out,
            ((.watergate_out|tonumber) - (.watergate_in|tonumber) | .*1000|round|./1000),
            .agency.agency_shortname.th] | @tsv'

# who operates what
curl -s "$API/public/watergate_load" \
| jq -r '[.watergate_data.data[].agency.agency_shortname.th] | group_by(.)
         | map({a:.[0], n:length}) | sort_by(-.n)[] | "\(.a)\t\(.n)"'
```

## Discharge - `public/flow`

55 stations, all reporting. **The station object here is shaped differently
from every other endpoint** - it uses `flow_name.th` and `flow_oldcode`, not
`tele_station_name` / `tele_station_oldcode`.

```bash
curl -s "$API/public/flow" \
| jq -r '.data[] | select(.flow_value != null)
         | [.station.flow_oldcode, .station.flow_name.th, .flow_value, .flow_datetime] | @tsv'
```

## Rolling rain by area - `provinces/rain3d|rain7d|rain15d`

3,357 records each. **The field is `rain_7d` with an underscore**, not `rain7d`
like the path, and each row carries `rainfall_start_date` / `rainfall_end_date`
so you know the window it actually covers.

```bash
curl -s "$API/provinces/rain7d" \
| jq -r '[.data[] | select(.rain_7d != null)] | sort_by(.rain_7d|tonumber) | reverse
         | .[0:10][] | [.rain_7d, .station.tele_station_name.th,
                        .geocode.province_name.th, .rainfall_start_date] | @tsv'
```

## Other live endpoints, all verified 200

```bash
curl -s "$API/frontend/shared/station_all"        | jq '.data | length'          # 11473
curl -s "$API/public/rain_monthly"                | jq '.data | length'          # 3603
curl -s "$API/frontend/shared/tele_canal_station" | jq '.data.tele_waterlevel|length'  # 2861
curl -s "$API/frontend/shared/watergate_station"  | jq '.data | length'          # 2167
curl -s "$API/public/canal_waterlevel"            | jq '.data | length'          # 282
curl -s "$API/public/flood_road"                  | jq '.data | length'          # 262
curl -s "$API/analyst/cctv"                       | jq '.data | length'          # 106
curl -s "$API/analyst/waterquality_load"          | jq '.data.data | length'     # 82
curl -s "$API/provinces/dam_uses_water"           | jq '.data | length'          # 26
curl -s "$API/iframe/waterlevel"                  | jq '.data | length'          # 80, tiny payload
```

## Rainfall history - same bulk layout as water level

```bash
# hourly and daily rain, 2012-2026, identical directory shape
curl -s "https://tiservice.hii.or.th/opendata/data_catalog/hourly_rain/" | grep -o 'href="20[0-9][0-9]/"'
curl -s "https://tiservice.hii.or.th/opendata/data_catalog/daily_rain/0all_stn_metadata.csv" | head -3
curl -# -L -C - "https://tiservice.hii.or.th/opendata/data_catalog/hourly_rain/0zip_file/2025.zip" -o rain2025.zip
```

Also under `data_catalog/`: `temperature/`, `humidity/`, `pressure/`, and the
`*_mou/` headwater-forest variants. `hii_pull.py` works on all of them by
changing the base path.

## Sanity checks worth running once

```bash
# does the file corpus agree with the API? (it does - 100% on CPY001 2025)
curl -s "$BASE/2025/202511/CPY001.csv" | head -3

# missing-data markers: blank, "-", -999, 9999, 999999, plus strays 999976/999997
curl -s "$BASE/2025/202511/CPY001.csv" | awk -F, 'NR>1 && ($3=="" || $3=="-" || $3+0>9000)' | wc -l
```

Licence is CC BY-NC. Attribute สถาบันสารสนเทศทรัพยากรน้ำ (HII).
