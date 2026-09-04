# twa.thaiwater.net - the short answer

Question asked: can we pull rainfall radar, rainfall, water level, CCTV, or
everything else off
`https://twa.thaiwater.net/th/map/basic/weather/overall/0?ds=rr%2Csc&p=modal`?

**Yes. All four, plus the other 25 layers on the site.** No account, no signup,
no scraping. Every number below was read off a live response on 2026-09-04
between 16:46 and 17:15 +07.

## The one thing you need

```
Host:    https://twa-api-public.thaiwater.net
Header:  x-api-key: TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x
```

That key is not stolen and not a secret. The site's own JS bundle sets it in an
axios request interceptor for any visitor who is not logged in:

```js
let t = useAuthStore.getState().token;
t ? e.headers.Authorization = `Bearer ${t}`
  : e.headers["x-api-key"] || (e.headers["x-api-key"] = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x")
```

Without it every endpoint returns `401 {"code":1007,...,"abbr":"UNAUTHORIZED"}`.

`GET /auth/get-public` returns the anonymous role's permission manifest: 159
resources, `view` scope on every one. I diffed that list against the 159 dataset
keys the page itself declares - **granted 159, not granted 0**. Nothing on this
page is behind a login.

## The four things you asked for

| Want | Endpoint | Live count |
|------|----------|-----------:|
| **น้ำฝน** rainfall | `/v2/rainfall/rainfall_c1440` | 2,696 stations |
| **ระดับน้ำ** water level | `/v2/waterlevel` | 791 stations |
| **กล้องวงจรปิด** CCTV | `/v2/cctv` | 85 registered, **4 verifiably live** - see below |
| **เรดาร์ฝน** rain radar | two separate sources, see below | 40 sites + 13 animated frames |

Rainfall accumulation windows are cumulative **minutes**, not labels:

| Token | Window | Stations |
|-------|--------|---------:|
| `rainfall_c1440` | 24 h | 2,696 |
| `rainfall_c4320` | 3 d | 2,758 |
| `rainfall_c7200` | 5 d | 2,809 |
| `rainfall_c10080` | 7 d | 3,201 |
| `rainfall_c21600` | 15 d | 2,529 |

Anything under a day (`c15`, `c60`, `c180`, `c360`, `c720`) returns 400. Sub-daily
rainfall is not served here.

## The CCTV registry is mostly dead - do not quote 85

The API returns 85 cameras and that number means very little. I followed it all
the way to the pixels:

| Stage | Count |
|-------|------:|
| Cameras registered, `isActive: true` on all | 85 |
| Carrying a `cctvUrl` | 64 |
| Distinct hostnames behind those | 57 |
| **Hostnames that resolve in DNS** | **10** |
| Cameras behind a resolving hostname | 17 |
| Confirmed returning a JPEG | 8 |
| **EXIF timestamp within seconds of now** | **4** |

All 44 `dyndns.org` hostnames are NXDOMAIN - that whole domain family has lapsed.
What survives is mostly EGAT dam cameras on `egat.co.th`.

Verified live right now (Axis P5655-E, 1920x1080, EXIF matching wall clock):
เขื่อนสิริกิติ์, เขื่อนภูมิพล, เขื่อนวชิราลงกรณ์, เขื่อนบางลาง.

Stale but responding: เขื่อนรัชชประภา (EXIF 2026-07-28, five weeks old).
เขื่อนสิรินธร returns HTTP 200 and a valid JPEG with **15/06/2024** burned into
the overlay - a frozen frame from over two years ago.

So `isActive: true` means "someone ticked a box", not "this camera works", and a
200 with a valid JPEG still does not mean the picture is current. Check the EXIF
`datetime` before trusting any frame.

The 8 reachable cameras were tested from this machine; a Thai network may reach
more, and DNS for the dead hosts could return elsewhere. But NXDOMAIN on 47 of 57
hostnames is not a local-network artifact - plain HTTP and port 5001 both work
from here (positive-controlled against `example.com` and `portquiz.net:5001`).

## Rain radar comes from two different places

The map's animated radar is **not** a Thai government product. It is RainViewer:

```
https://api.rainviewer.com/public/weather-maps.json
-> tile template {host}{path}/256/{z}/{x}/{y}/2/1_1.png
```

13 past frames, one every 10 minutes. Verified by fetching z=6 over Bangkok:
8,644-byte PNG. No key needed. This is what `ds=rr` paints.

The Thai radar images are separate - 40 individual radar sites (TMD, Bangkok,
HII), 25 with a frame today, delivered as JPEG/PNG pictures rather than tiles:

```
/data/platform/v1/public/media?mediaTypeId=30&agencyId=13
    &startDate=2026-09-04 00:00&endDate=2026-09-04 23:59&limit=-1&latest=true
```

Verified downloads: `cmp240` 680x680 JPEG (Chumphon 240 km), `omkoi` 1072x800 PNG.

## What `ds=rr%2Csc` in your URL means

`ds` is a comma-separated list of layer short codes. `rr` = radar-rain,
`sc` = storm-current. That is why the page loads RainViewer tiles and `/v2/storm`
and nothing else. Swap it for `ds=rf,wl,cc` and the same page fires
`/v2/rainfall/rainfall_c1440`, `/v2/waterlevel` and `/v2/cctv` - that is how the
rainfall token was recovered.

Full code map in [[1711_API-SURFACE]].

## Everything else on the site

Same host, same key, one call each:

| Layer | Endpoint | Rows |
|-------|----------|-----:|
| Weather stations | `/v2/weather` | 3,756 |
| PM2.5 | `/v2/pm25` | 1,133 |
| PM10 | `/v2/pm10` | 1,050 |
| Water level discharge | `/v2/waterlevel-discharge` | 311 |
| Canal water level | `/v2/waterlevel/canal` | 266 |
| Discharge forecast | `/v2/waterlevel-discharge/forecast` | 147 |
| 6-month rain anomaly | `/v2/rain-month/six-anomaly` | 118 |
| 6-month rain forecast | `/v2/rain-month/six-forecast` | 118 |
| Water quality | `/v2/waterquality` | 84 |
| Agencies | `/v2/agency` | 56 |
| Large dams | `/v2/large-dam/daily-geo-json` | 35 |
| Water gates | `/v2/watergate` | 30 |
| Bangkok flow measurement | `/v2/flood/flow-measurement-bangkok` | 30 |
| Tide | `/v2/waterload-tide` | 30 |
| Sea water level | `/v2/waterlevel/sea-waterlevel` | 26 |
| Wave | `/v2/wave` | 25 |

A single `twa_pull.py all` run pulled **11,224 records / 13 MB** across every
domain in one pass.

## Working tool

`ψ/lab/twa-thaiwater/twa_pull.py` - verified, runs on stdlib Python only.

```bash
python3 twa_pull.py rainfall 1440
python3 twa_pull.py waterlevel
python3 twa_pull.py cctv
python3 twa_pull.py radar-sites
python3 twa_pull.py radar-image cmp240 out.jpg
python3 twa_pull.py radar-tiles
python3 twa_pull.py all --out ./dump
```

## Before anyone ingests this commercially

`api-v3.thaiwater.net` published no terms, and `twa-api-public.thaiwater.net`
publishes none either - I looked. The CKAN portal at `data.hii.or.th` is
Creative Commons Attribution **Non-Commercial**. An anonymous key shipped in a
public bundle is not a licence. For RPRO or any paid product this has to be
settled with สสน. in writing first. That is a legal question, not a technical
one, and nothing above answers it.

## Related

- [[1711_ARCHITECTURE]] - hosts, auth model, payload shapes
- [[1711_API-SURFACE]] - all 195 discovered paths with verified status
- [[1711_TESTING]] - how each claim was checked, and the six traps
- [[1711_CODE-SNIPPETS]] - copy-paste curl and Python
- `ψ/lab/hii-water-level/WATER-APIS.md` - the older `api-v3` surface, still valid
