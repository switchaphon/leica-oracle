# twa.thaiwater.net - curl and Python recipes

Every command here was executed successfully on 2026-09-04. Needs `jq` for the
shell ones. Python examples are stdlib only.

```bash
API=https://twa-api-public.thaiwater.net
KEY=TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x
```

Every call needs `-H "x-api-key: $KEY"`. Without it: `401 / 1007`.

## Rainfall

```bash
# 24h accumulation, 2,696 stations. Token is cumulative MINUTES.
curl -s -H "x-api-key: $KEY" "$API/v2/rainfall/rainfall_c1440" \
| jq -r '[.data[].features[]] | length'

# top 10 wettest in the last 24h
curl -s -H "x-api-key: $KEY" "$API/v2/rainfall/rainfall_c1440" \
| jq -r '[.data[].features[].properties]
         | sort_by(.measureValue) | reverse | .[0:10][]
         | [.measureValue, .station.station, .geoCode.province] | @tsv'

# other windows: c4320=3d  c7200=5d  c10080=7d  c21600=15d
# anything under a day (c15 c60 c180 c360 c720) returns 400
```

## Water level

```bash
# 791 stations
curl -s -H "x-api-key: $KEY" "$API/v2/waterlevel" \
| jq -r '[.data[].features[]] | length'

# stations closest to bank (diffWlBank positive = below bank, in metres)
curl -s -H "x-api-key: $KEY" "$API/v2/waterlevel" \
| jq -r '[.data[].features[].properties]
         | sort_by(.diffWlBank) | .[0:10][]
         | [.diffWlBank, .waterlevelMsl, .station.station, .riverName] | @tsv'

# canal (266) and discharge (311)
curl -s -H "x-api-key: $KEY" "$API/v2/waterlevel/canal"        | jq '[.data[].features[]]|length'
curl -s -H "x-api-key: $KEY" "$API/v2/waterlevel-discharge"    | jq '[.data[].features[]]|length'
```

## CCTV

```bash
# 85 cameras across 44 provinces, 64 with a stream URL
curl -s -H "x-api-key: $KEY" "$API/v2/cctv" \
| jq -r '[.data[].features[].properties] | map(select(.cctvUrl))[]
         | [.cctvTitle, .cctvUrl + (.cctvFilename // "")] | @tsv'
```

Most are Axis cameras exposed directly, e.g.
`http://banpom-cpy.dyndns.org:5001/axis-cgi/jpg/image.cgi?resolution=CiF` -
a single JPEG per request, so poll it rather than expecting a video stream.
`cctvMediaType` tells you `img` vs video.

## Rain radar - animated tiles (what the map paints)

```bash
# frame index: 13 past frames, one every 10 minutes. No key needed.
curl -s "https://api.rainviewer.com/public/weather-maps.json" \
| jq -r '.host as $h | .radar.past[] | "\(.time)  \($h)\(.path)/256/{z}/{x}/{y}/2/1_1.png"'

# one tile over Bangkok, z=6
curl -s -o bkk.png \
  "https://tilecache.rainviewer.com/v2/radar/$(curl -s https://api.rainviewer.com/public/weather-maps.json | jq -r '.radar.past[-1].path' | cut -d/ -f4)/256/6/49/29/4/1_1.png"
```

Tile template: `{host}{path}/{size}/{z}/{x}/{y}/{colour}/{smooth}_{snow}.png`.
The site uses size 256, colour 2. EPSG:3857 XYZ, drops straight into MapLibre,
Leaflet or OpenLayers.

## Rain radar - Thai station images

`startDate` and `endDate` are **mandatory**. Without them you get
`500 {"code":1006,"message":"无操作权限"}`, which looks like a permissions error
and is not.

```bash
DAY=$(date +%F)
# agencyId 13 = TMD (27 sites), 10 = Bangkok (2), 19 = HII (11)
curl -s -H "x-api-key: $KEY" \
  "$API/data/platform/v1/public/media?mediaTypeId=30&agencyId=13&startDate=$DAY%2000:00&endDate=$DAY%2023:59&limit=-1&latest=true" \
| jq -r '.data[].attributes | [.radarType, .mediaDatetime, .filename] | @tsv'
```

Then redeem the `mediaPath` blob for the actual image. Note `isStaticFile=false`:

```bash
MP=$(curl -s -H "x-api-key: $KEY" \
  "$API/data/platform/v1/public/media?mediaTypeId=30&agencyId=13&startDate=$DAY%2000:00&endDate=$DAY%2023:59&limit=-1&latest=true" \
  | jq -r '.data[] | select(.attributes.radarType=="cmp240") | .attributes.mediaPath')

curl -s -H "x-api-key: $KEY" -o cmp240.jpg \
  --data-urlencode "mediaPath=$MP" -G \
  "https://platform.thaiwater.net/api/v1/public/media/view?isStaticFile=false"

file cmp240.jpg   # JPEG 680x680
```

`isStaticFile=true` 404s on radar. Use `true` only for static assets such as
water level cross-sections.

**The timestamp lies.** `mediaDatetime` is tagged `+07:00` but carries UTC on
most sites. Parse `filename` instead - it holds the frame time in UTC on every
site:

```python
import re
from datetime import datetime, timedelta

def frame_time(filename):
    m = re.search(r"(20\d{6})[-_]?(\d{4})", filename)
    utc = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")
    return utc + timedelta(hours=7)   # true local
```

## Pagination, when you must use a /list route

Both parameters or nothing. One alone fails.

```bash
# correct - all 85
curl -s -H "x-api-key: $KEY" \
  "$API/v2/cctv/list?pagination%5Bpage%5D=1&pagination%5BpageSize%5D=1000" \
| jq '.data | length'

# pagination[page] alone  -> 400 {"code":1004,"abbr":"INVALID_DATA"}
# page=2 or pageSize=100  -> silently ignored, page 1 every time
```

`pageSize=-1` works on `/v2/agency` and returns 0 rows on `/v2/cctv/list`. Pass a
real number. Better: use the MAP route and skip paging entirely.

## Flattening a MAP payload

```python
def features(payload):
    """MAP routes are keyed by PROVINCE CODE. len(data) is provinces, not rows."""
    data = payload["data"]
    if isinstance(data, list):
        return data
    return [f for fc in data.values()
            if isinstance(fc, dict) and "features" in fc
            for f in fc["features"]]
```

`/v2/cctv` has 44 keys and 85 cameras. Counting keys is the easiest way to
publish a wrong number off this API.

## Field names that matter

Rainfall properties:
`measureAt`, `measureValue` (mm), `percentageDiff`, `station.station` (Thai name),
`station.stationCode`, `station.latitude/longitude`, `geoCode.province`,
`agency`, `basin`, `subbasin`.

Water level properties:
`waterlevelDatetime`, `waterlevelMsl`, `waterlevelMslPercent`, `storagePercent`,
`diffWlBank` (metres below bank, positive = safe), `diffWlBankText`, `minBank`,
`riverName`, `station.station`, `geoCode`, `basin`.

CCTV properties:
`cctvTitle`, `cctvUrl`, `cctvFilename`, `cctvMediaType` (`img`/video),
`isActive`, `latitude`, `longitude`, `agency.agency`, `geoCode`.

## Whole-site dump

```bash
python3 ψ/lab/twa-thaiwater/twa_pull.py all --out ./dump
#   2696  rainfall_24h.json      3201  rainfall_7d.json
#    791  waterlevel.json         266  waterlevel_canal.json
#    311  waterlevel_discharge.json  85  cctv.json
#   3756  weather.json             30  watergate.json
#     35  large_dam.json           40  radar_sites.json
#     13  radar_frames.json
# 11,224 records, 13 MB
```

## Recovering an unknown parameter

The trick that beat guessing. Load the page with the layer's `ds` code and read
what the frontend asks for:

```
https://twa.thaiwater.net/th/map/basic/weather/overall/0?ds=rf,wl,cc&p=hide
  -> GET /v2/rainfall/rainfall_c1440
  -> GET /v2/waterlevel
  -> GET /v2/cctv
```

Codes: `rr` radar-rain, `sc` storm-current, `rf` rainfall, `wl` water-level,
`cc` cctv, `wt` weather, `aq` air-quality, `ld` large-dam, `md` medium-dam,
`wg` water-gate, `wq` water-quality, `wv` wave, `fp` floodplain, `sl` salinity,
`rd` radar, `brr` bkk-rain-radar, `rfs` rain-forecast-station,
`raf` rain-anomaly-forecast. Full map in [[1711_ARCHITECTURE]].
