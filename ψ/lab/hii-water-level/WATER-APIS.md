# Thai water data - what else is out there

Survey run 2026-09-03. Every row below was fetched and its record count read off
the live response. Nothing here is copied from someone else's notes.

Two hosts carry almost everything:

- `api-v3.thaiwater.net` - live operational JSON, no key, no auth
- `tiservice.hii.or.th` - historical bulk files, plain directory index

Endpoint paths were recovered by pulling `thaiwater.net/dist/js/app.chunk.js`
(7.6 MB) and mining it, then testing each one.

## Tier 1 - live operational, all verified 200

Base `https://api-v3.thaiwater.net/api/v1/thaiwater30`

| Path | Records | What it gives you |
|------|---------|-------------------|
| `analyst/dam` | 989 dams | **full reservoir water balance** |
| `public/watergate_load` | 2,315 gates | **gate + pump operational state** |
| `frontend/shared/station_all` | 11,473 | every station of every type |
| `public/rain_monthly` | 3,603 | monthly rain totals |
| `provinces/rain3d` `rain7d` `rain15d` | 3,357 each | rolling rain by area |
| `frontend/shared/tele_canal_station` | 2,861 | canal level stations |
| `frontend/shared/watergate_station` | 2,167 | gate station registry |
| `public/waterlevel_load` | 1,407 | river level, current |
| `public/rain_24h` / `rain_today` / `rain_yesterday` | 4,433 / 4,499 / 3,609 | rain gauges |
| `public/canal_waterlevel` | 282 | canal level |
| `public/flood_road` | 262 | flooded road points |
| `analyst/waterquality_load` | 82 | water quality |
| `public/flow` | 55 | **discharge in m3/s**, all 55 reporting |
| `analyst/cctv` | 106 | cameras |
| `provinces/dam_uses_water` | 26 | usable water by province |
| `iframe/rain24` / `iframe/waterlevel` | 80 each | province rollups, small payload |

Returning 404 despite appearing in our June 2026 notes: `dam_daily_load`,
`dam_load`, `dam_medium_small`, `waterquality_load` (under `public/`),
`wl_load_all`, `situation_level`, `public_warning`, `rain_5m`, `weather_load`,
`sea_waterlevel`, `thaiwater_hourly`. That list was never verified; it is stale.

### The dam endpoint is the biggest find

`analyst/dam` returns four sections in one call:

| Section | Count |
|---------|-------|
| `dam_daily` | 50 large dams |
| `dam_medium` | 862 |
| `dam_small_tele` | 60 |
| `dam_hourly` | 17 |

Per dam: `dam_storage`, `dam_storage_percent`, `dam_inflow`,
`dam_inflow_acc_percent`, `dam_uses_water`, `dam_uses_water_percent`,
`dam_level`, `dam_released`, `dam_spilled`, `dam_losses`, `dam_evap`, plus
agency, basin and geocode.

That is inflow, outflow, spill, evaporation and losses - a closed water balance,
updated daily. Live sample from today:

```
รัชชประภา        3701.67 MCM  65.65%   inflow 12.23   released  3.51
ขุนด่านปราการชล   184.60 MCM  82.41%   inflow  2.43   released  1.15
แควน้อยบำรุงแดน   401.19 MCM  42.73%   inflow  5.67   released  4.32
```

**`dam_daily` holds 50 rows for only 39 dams.** Eleven are reported by both
ชป. and กฟผ., on different dates, and the two disagree on percentage even when
storage is identical - รัชชประภา reads 65.65% from ชป. and 77.76% from กฟผ.,
อุบลรัตน์ 35.91% against 81.26%, บางลาง 54.62% against a flat 0. The agencies
divide by different capacity denominators.

Summing the rows naively gives 93,647 MCM. Deduplicating to the newest row per
dam gives **49,033 MCM**. The naive figure overstates by 91%. I quoted the wrong
one before checking; the dedupe recipe is in CURL.md.

`analyst/dam_yearly_graph` returns `upper_rule_curve` and `lower_rule_curve`
(13,908 points each), plus `lower_bound`, `upper_bound`, `normal_bound`,
`average_inflow`, `sum_average_inflow`.

Rule curves are the envelope a reservoir is meant to be operated inside, so this
would be the reference for any release-decision model - **but as served it is not
usable.** 13,908 points across 366 distinct dates is 38 series concatenated, and
each point carries only `date` and `value`, with no dam identifier. The endpoint
ignores `dam_id`, `dam` and `id`. Someone has to work out how the frontend
selects a single dam's series before this is worth anything.

### Water gates carry control state, not just levels

`public/watergate_load` gives `watergate_in`, `watergate_out`, `watergate_out2`,
`pump_on`, `pump`, `floodgate_open`, `floodgate`, `floodgate_height`. Head
difference across a structure plus whether the pumps are running.

By operator: สสน. 1,144, ชป. 734, พพภ 213, สนน กทม. 74, อส. 2.

## Tier 2 - historical bulk, same shape as water_level

`https://tiservice.hii.or.th/opendata/data_catalog/<name>/`

| Directory | Content |
|-----------|---------|
| `water_level/` | 10-min river level, 2012-2026 |
| `hourly_rain/` | **hourly rain, 2012-2026, identical layout** |
| `daily_rain/` | **daily rain, 2012-2026, identical layout** |
| `temperature/` `humidity/` `pressure/` | met variables |
| `*_mou/` | headwater forest telemetry, 259 stations |

Each carries `0all_stn_metadata.csv`, `0zip_file/<year>.zip`, and
`<year>/<yyyymm>/<STATION>.csv`. `hii_pull.py` works on all of them by changing
the base path - the rainfall corpus is the obvious next pull, since level
without rain gives a model no forcing input.

## Tier 3 - derived products and forecasts

From the 36-package CKAN catalogue on `data.hii.or.th`:

| Dataset | Why it matters |
|---------|----------------|
| `ratingcurve` | **Elevation-Capacity-Area curves - converts level to volume** |
| `6months-forecast-rainfall` | ML rain forecast, 6 months ahead, by province |
| `spatial-rain` | IDW-interpolated rain by province and district, plus a 30-year normal |
| `flood-risk-area` | tambon-level flood risk, 6 months ahead, monthly |
| `drought-risk-area` | tambon-level drought risk, same cadence |
| `r35mm` | days with rain >= 35 mm, 1992-2024, province and tambon |
| `dsl` / `dsl-dry` | longest dry spell in wet and dry season, 1992-2023 |
| `wrf-rom` | 7-day rain and wind from WRF-ROMS on GFS 0.5 deg |
| `swan-model` | wave height forecast for the Gulf |
| `hydro-historical-report` | recorded water events |

Without a rating curve, a level series cannot become a volume, so `ratingcurve`
is the piece that turns telemetry into something you can do water accounting on.

## Tier 4 - survey and terrain, via gisservice.hii.or.th

`road-level` (road and levee crest heights, MMS-surveyed against NCDC),
`flood-mark` (surveyed flood marks on poles and walls), `bathymetry`
(multibeam echosounder), `dem-reservoir` (LiDAR DTM, 60 small reservoirs
surveyed in 2568), `terrain`.

These are SHP and GeoTIFF behind a directory browser, not an API.

## What I would pull next, in order

1. `hourly_rain` bulk, same basins - rainfall is the forcing input the level data lacks
2. `analyst/dam` on a schedule - 989 dams, closed water balance, nothing else gives this
3. `ratingcurve` - so level becomes volume
4. `public/watergate_load` on a schedule - control state, and 2,315 points is cheap
5. `spatial-rain` 30-year normal - the baseline any anomaly is measured against

## Licence, unchanged

The CKAN portal is Creative Commons Attribution **Non-Commercial**.
`api-v3.thaiwater.net` publishes no terms at all. For RPRO that has to be
settled with สสน. in writing before any of this is ingested commercially.
