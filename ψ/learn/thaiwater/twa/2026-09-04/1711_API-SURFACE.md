# twa-api-public.thaiwater.net - full API surface

Recovered 2026-09-04 by pulling all 55 Next.js chunks (8.3 MB) from
`twa.thaiwater.net` and mining them for path constants, then executing every
non-templated path against the live API with the anonymous key.

- **195 distinct paths** found in the bundle
- 163 static (no `${}` placeholder) - all executed
- 32 templated - exercised by hand where the parameter could be recovered
- Result: **121 returned 200**, 110 of those with rows; 31 x 500, 9 x 400, 2 timeouts

All rows below are verified counts from a live response, not bundle strings.

## v2 - map layers, GeoJSON

`geojson-by-key(N)` means the payload is `{data: {"<provinceCode>": FeatureCollection}}`
across N provinces. **The count column is flattened features, not top-level keys.**

| Endpoint | Records | Shape |
|----------|--------:|-------|
| `/v2/weather` | 3,756 | geojson-by-key(78) |
| `/v2/pm25` | 1,133 | geojson-by-key(77) |
| `/v2/pm10` | 1,050 | geojson-by-key(77) |
| `/v2/waterlevel` | 792 | geojson-by-key(77) |
| `/v2/waterlevel-discharge` | 311 | geojson-by-key(64) |
| `/v2/waterlevel/canal` | 266 | geojson-by-key(6) |
| `/v2/waterlevel-discharge/forecast` | 147 | geojson-by-key(45) |
| `/v2/rain-month/six-anomaly` | 118 | geojson |
| `/v2/rain-month/six-forecast` | 118 | geojson |
| `/v2/cctv` | 85 | geojson-by-key(44) |
| `/v2/waterquality` | 84 | geojson-by-key(45) |
| `/v2/agency` | 56 | list |
| `/v2/large-dam/daily-geo-json` | 35 | geojson-by-key(26) |
| `/v2/watergate` | 30 | geojson-by-key(13) |
| `/v2/waterload-tide` | 30 | geojson |
| `/v2/flood/flow-measurement-bangkok` | 30 | geojson-by-key(2) |
| `/v2/waterlevel/sea-waterlevel` | 26 | geojson |
| `/v2/wave` | 25 | geojson-by-key(20) |
| `/v2/salinity-forecasting` | 7 | geojson-by-key(3) |
| `/v2/storm` | 2 | list |

### Templated - `/v2/rainfall/{token}`

The token is cumulative minutes. Recovered by loading the page with `ds=rf` and
reading the request the frontend made (`rainfall_c1440`), then walking the family.

| Token | Window | Stations |
|-------|--------|---------:|
| `rainfall_c1440` | 24 h | 2,696 |
| `rainfall_c4320` | 3 d | 2,758 |
| `rainfall_c7200` | 5 d | 2,809 |
| `rainfall_c10080` | 7 d | 3,201 |
| `rainfall_c21600` | 15 d | 2,529 |

`c15`, `c60`, `c180`, `c360`, `c720` all 400. Sub-daily is not served.

## v2 - summary and alert endpoints

| Endpoint | Rows |
|----------|-----:|
| `/v2/summary/dam-summary` | 6 |
| `/v2/summary/rainfall-forecast` | 6 |
| `/v2/summary/temperature-forecast` | 6 |
| `/v2/summary/rainfall-24hr-forecast` | 4 |
| `/v2/summary/summary4dam` | 4 |
| `/v2/summary/dam-crisis` | 2 |
| `/v2/summary/warning-rainfall-24h` | 2 |
| `/v2/summary/warning-rainfall-48h` | 2 |
| `/v2/summary/pm25-ranking-province` | 10 |
| `/v2/summary/rainfall24h-ranking-province` | 10 |
| `/v2/summary/waterlevel-ranking-province` | 10 |
| `/v2/drought/alert` | 1 |
| `/v2/flood/flash-flood` | 1 |
| `/v2/storm/alert` | 0 (empty, not broken - no active storm) |
| `/v2/flood/flood-bangkok` | 0 (empty) |

## v2 - `/list` variants

Every domain has one. All 24 returned exactly **10 rows** on a bare call, because
the default page size is 10 and **both** pagination parameters are required:

```
?pagination[page]=1&pagination[pageSize]=1000
```

Sending only one of the pair is worse than sending neither - `pagination[page]=2`
alone returns `400 {"code":1004,"abbr":"INVALID_DATA"}`, and bare `page=2` or
`pageSize=100` are silently ignored (identical row ids on every page).

`pageSize=-1` is **endpoint-specific**: the frontend uses it on `/v2/agency` and
gets everything, but on `/v2/cctv/list` it returns 0 rows. Pass a real number.

Prefer the MAP route for bulk anyway - one call, no paging.

## v2 - requires parameters (400 on a bare call)

`/v2/district-rain/accumulate`, `/v2/district-rain/actual-measure`,
`/v2/district-rain/forecast`, `/v2/summary-area/rainfall`,
`/v2/summary-area/temperature`, `/v2/summary-area/pm25`,
`/v2/summary-area/drought-warning`, `/v2/summary-area/flashflood-warning`,
`/v2/summary/weather-summary`.

These are real endpoints; I did not recover their parameter sets. The technique
that works: load the page with the matching `ds` code and read the request.

## v1 - `/data/platform/v1/public/...`

Media, images and graphs. Different conventions: `page`/`limit`, and here
`limit=-1` genuinely means unlimited.

| Endpoint | Rows | Note |
|----------|-----:|------|
| `media?agencyId=9&mediaTypeId=223&sort=-mediaDatetime&limit=-1` | 1,104 | proves `limit=-1` works on v1 |
| `media/rain/image/rain_distribution?type=48year&limit=-1` | 26 | |
| `media/rain/image/rain_distribution?type=301year&limit=-1` | 16 | |
| `media/rain/image/rain_distribution?type=30year&limit=-1` | 13 | 30-year normal |
| `dam_pdaily_sum_by_date` | 10 | |
| `media_internal?type=gnssPrecip` | 8 | |
| `media_internal?type=wrfromsTrough` | 4 | |
| `media_internal?type=radarCompositeTh` | 1 | composite radar image |
| `media_internal?type=gsMap10x10` / `gpm10x10` / `persian4x4` | 1 each | satellite rain bias |
| `media_internal?type=latest3dayRisk` / `nhcRD1` | 1 each | |
| `media_internal?type=forecastTemp` / `forecastWind1d5Km` | 1 each | |
| `media/waterlevel/image/crossection` | 1 | station cross-section PNG |

### Radar images - `media?mediaTypeId=30`

Requires `startDate`, `endDate`, `agencyId`. Without dates: `500 / 1006`.

```
/data/platform/v1/public/media?mediaTypeId=30&agencyId=13
  &startDate=2026-09-04 00:00&endDate=2026-09-04 23:59&limit=-1&latest=true
```

| agencyId | Sites | Products |
|---------:|------:|----------|
| 13 | 27 | TMD radars, `<code>240` / `<code>120`, JPEG + GIF |
| 10 | 2 | Bangkok (`NJ` Nong Chok, `NK` Nong Khaem), JPEG |
| 19 | 11 | HII radars (omkoi, rongkwang, takhli, rasisalai, singha, phimai, banphue, sattahip, pathio), CAPPI dBZ PNG |

40 sites total, 25 carrying a frame on the day tested.

### `/graph` endpoints - all 500 on a bare call

`tele_waterlevel/graph`, `waterquality/graph`, `medium_dam/graph_year`,
`dam_rulecurve/graph`, `salinity_forecast_cpy/graph`,
`sea_waterlevel_forecast/graph`, `latest_watertide/forecast/graph`,
`dam_pdaily_sum_by_region_graph`, plus `canal_waterlevel/graph`, `flow/graph`,
`pm10/graph`, `pm25/graph`, `swan/graph`, `tele_watergate/graph`,
`floodplain_area/graph`, `flood_road/graph` (these return 200 with 0 rows).

They need a station id and a date range. The old `api-v3` equivalents are
documented and working in `ψ/lab/hii-water-level/CURL.md` - use those for time
series until these are worked out.

## Other hosts referenced by the bundle

| URL | Content | Status |
|-----|---------|--------|
| `api.rainviewer.com/public/weather-maps.json` | animated rain radar frames | **verified working, no key** |
| `live1.hii.or.th/product/latest/rain/one_map/data/om_mfcst_{1..6}m.tif` | 1-6 month rain forecast GeoTIFF | not fetched |
| `live1.hii.or.th/product/latest/rain/one_map/data/anomaly_rain_{1..6}m.tif` | rain anomaly GeoTIFF | not fetched |
| `live1.hii.or.th/product/latest/wrfroms/tiff/description_wrfroms.json` | WRF-ROMS index | not fetched |
| `api.hii.or.th/tiservice/v1/ws/<token>/isohyet/daily/latest/province/10` | isohyet, token in path | not fetched |
| `www.thaiwater.net/proxy/hims.php?file=...urban/data?token=...` | Bangkok HIMS urban radar | not fetched |
| `twa.thaiwater.net/api/geoserver/thaiwater30/wms` | WMS raster proxy, `thaiwater30:river_thailand` | not fetched |
| `twa.thaiwater.net/api/proxy-tiff` | GeoTIFF proxy | not fetched |
| `waterchart.thaiwater.net`, `tiwrm.hii.or.th`, `pdpa.hii.or.th` | referenced, not probed | - |

Marked "not fetched" honestly: they are in the bundle and look right, but I did
not execute them, so treat them as leads rather than facts.

## Dataset key catalogue

The page declares 159 dataset keys (119 `web-*`, 40 `mobile-*`), and
`/auth/get-public` grants `view` on all 159. The 41 radar-related keys:

```
web-composite-radar-image  web-radar-image  web-rain-radar
web-radar-banphue-240      web-radar-chainat-240    web-radar-chiangrai-240
web-radar-chumphon-240     web-radar-huahin-240     web-radar-inburi-240
web-radar-khonkaen-240     web-radar-krabi-240      web-radar-lamphun-240
web-radar-maehongson-240   web-radar-nan-120        web-radar-nan-240
web-radar-narathiwat-240   web-radar-nongchok-120   web-radar-nongkhaem-150
web-radar-omkoi-240        web-radar-pathiu-240     web-radar-phanom-240
web-radar-phetchabun-240   web-radar-phimai-160     web-radar-phitsanulok-240
web-radar-phuket-120       web-radar-phuket-240     web-radar-rasiisalai-240
web-radar-rayong-240       web-radar-rongkwang-240  web-radar-sakonnakhon-240
web-radar-samutsongkhram-120  web-radar-samutsongkhram-240
web-radar-sattahip-240     web-radar-songkhla-240   web-radar-suratthani-240
web-radar-surin-240        web-radar-suvarnabhumi-120  web-radar-suvarnabhumi-240
web-radar-takli-240        web-radar-ubonratchathani-120  web-radar-ubonratchathani-240
```
