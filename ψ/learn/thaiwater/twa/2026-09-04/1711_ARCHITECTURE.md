# twa.thaiwater.net - architecture

Explored 2026-09-04. This is a **web target, not a repo** - there is no source to
clone, so "architecture" here means the network surface recovered from the
shipped bundle plus live probing.

## Not the same site as thaiwater.net

`ψ/lab/hii-water-level/WATER-APIS.md` documents `api-v3.thaiwater.net`, mined
from `thaiwater.net/dist/js/app.chunk.js` in September 2026. **TWA is a different
frontend on a different API host with a different auth model and different
counts.** Both are live. Neither supersedes the other.

| | thaiwater.net (old) | twa.thaiwater.net (this) |
|---|---|---|
| Frontend | jQuery-era bundle, one 7.6 MB chunk | Next.js App Router, turbopack, 55 chunks |
| API host | `api-v3.thaiwater.net` | `twa-api-public.thaiwater.net` |
| Auth | none | `x-api-key` required, 401 without |
| Water level rows | 1,407 | 791 |
| CCTV rows | 106 | 85 |
| Error language | Thai/English | **Chinese** |

Two different row counts are NOT evidence of two different station sets - that
was my first reading and it was wrong. Joined on coordinates, 768 of twa's 780
water level stations are api-v3 stations under a different code scheme, matching
to within 0.1 m. See trap 9 in [[1711_TESTING]].

Do not assume a number carried over from the old notes applies here, and do not
assume a different number means different coverage either.

## Hosts

| Host | Role | Auth |
|------|------|------|
| `twa.thaiwater.net` | Next.js frontend, also proxies GeoServer + GeoTIFF | none |
| `twa-api-public.thaiwater.net` | **the API** - all JSON | `x-api-key` |
| `platform.thaiwater.net` | media/image byte serving | `x-api-key` |
| `api.rainviewer.com` + `tilecache.rainviewer.com` | the animated rain radar | none |
| `live1.hii.or.th` | GeoTIFF rain forecast/anomaly products | none |
| `api.hii.or.th/tiservice` | isohyet service, token in URL | token |
| `tiservice.hii.or.th` | historical bulk CSV (see old notes) | none |

## Auth model

Two credentials, one interceptor:

```js
// chunk 5f20bcef6fd83517.js and friends
axiosApiInstance.interceptors.request.use(async e => {
  e.headers["Accept-Language"] = await getLocaleCurrent();
  let t = useAuthStore.getState().token;
  t ? e.headers.Authorization = `Bearer ${t}`
    : e.headers["x-api-key"] || (e.headers["x-api-key"] = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x");
  return e;
});
```

A logged-in user gets a bearer token; everyone else gets the shared anonymous
key. There is no per-visitor key issuance and no rate-limit header in any
response I saw.

`GET /auth/get-public` describes what the anonymous role may read:

```json
{"id":"public","isPublic":true,
 "permissions":[{"rsname":"web-cctv","scopes":["view"]}, ...]}
```

159 resources, 119 `web-*` and 40 `mobile-*`. Diffed against the 159 dataset keys
embedded in the page's RSC payload: **every key is granted**. So permission is
never the reason a call fails here - see the trap in [[1711_TESTING]] where a
missing parameter masquerades as a permissions error.

## Error codes

The backend answers in Chinese, which is a strong hint this is an off-the-shelf
Chinese stack rather than something HII wrote:

| HTTP | code | message | actually means |
|------|------|---------|----------------|
| 401 | 1007 | 会话已过期，请重新登录 | no `x-api-key` sent |
| 500 | 1006 | 无操作权限 | "no permission" - **usually a missing required parameter** |
| 400 | 1004 | 数据不正确 | malformed parameter, e.g. half a pagination pair |

Treating 1006 as a permissions wall costs you the entire radar catalogue. It is
almost always `startDate`/`endDate` missing.

## Two API generations on one host

**v2** - `/v2/<domain>` - the current map layers. GeoJSON.
**v1** - `/data/platform/v1/public/<thing>` - media, images, graphs, older
products. JSON:API-ish with `attributes` / `relationships` / `included`.

They do not share conventions. v2 uses `pagination[page]`/`pagination[pageSize]`;
v1 uses `page`/`limit`, and `limit=-1` genuinely means unlimited there
(`media?...&limit=-1` returned 1,104 rows).

## v2 payload shapes - the important one

Every v2 domain exposes up to three routes:

| Route | Shape | Use for |
|-------|-------|---------|
| `/v2/<domain>` (MAP) | `{data: {"<provinceCode>": FeatureCollection}}` | **bulk pulls** |
| `/v2/<domain>/list` (LIST) | `{meta:{pagination}, data:[...]}` | paged tables |
| `/v2/<domain>/{id}/detail` | one record | drill-down |

The MAP route is keyed by province code and needs flattening:

```python
rows = [f for fc in payload["data"].values() for f in fc["features"]]
```

`len(payload["data"])` is the **province count**, not the record count. For CCTV
that is 44 vs the true 85. This is the single easiest way to publish a wrong
number off this API.

## Frontend layer selection

The `ds` query parameter is a comma-separated list of two-to-four letter layer
codes, mapped in the bundle:

```js
{canal_waterlevel:"cw","bkk-flow":"bf","bkk-floodroad":"bfr",
 "water-level-discharge-forecast":"wldf","radar-rain":"rr","radar-wind":"rw",
 "storm-current":"sc","bkk-rain-radar":"brr",rainfall:"rf",weather:"wt",
 "air-quality":"aq","water-level":"wl","large-dam":"ld","medium-dam":"md",
 "water-gate":"wg","water-quality":"wq",cctv:"cc","water-load-tide":"wlt",
 wave:"wv","water-level-discharge":"wld","rainfall-5d":"rf5",
 "rainfall-bkk-1d":"rfb1","water-level-river":"wlr",floodplain:"fp",
 salinity:"sl",seaWaterLevel:"swl","basin-water-level":"bwl",
 "storm-history":"sh",radar:"rd","rain-forecast-station":"rfs",
 "rain-anomaly-forecast":"raf"}
```

This is a useful lever: loading the page with a chosen `ds` makes the frontend
issue exactly the calls for those layers, which is how undocumented parameter
values get recovered without guessing.

## Raster layers

Not everything is JSON. Three separate raster paths:

1. **RainViewer tiles** - `tilecache.rainviewer.com/v2/radar/<frame>/256/{z}/{x}/{y}/2/1_1.png`, XYZ, EPSG:3857.
2. **GeoServer WMS**, proxied through the frontend so it inherits no auth:
   `/api/geoserver/thaiwater30/wms?service=WMS&version=1.1.1&request=GetMap&layers=thaiwater30:river_thailand&format=image/png&transparent=true&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}`
3. **GeoTIFF** rain forecast/anomaly on `live1.hii.or.th/product/latest/rain/one_map/data/`
   (`om_mfcst_1m..6m.tif`, `anomaly_rain_1m..6m.tif`), fetched through
   `/api/proxy-tiff`.

## Media images

Records carry an obfuscated `mediaPath` blob rather than a URL:

```json
{"radarType":"ubn240","mediaDatetime":"2026-09-04T09:00:00+07:00",
 "mediaPathRaw":"image_radar_ubn/2026/09/04",
 "mediaPath":"AAECAwQFBgcICQoLDA0ODzmzoKDAqCut...",
 "filename":"ubn240_202609040900.jpg"}
```

Redeem it at:

```
https://platform.thaiwater.net/api/v1/public/media/view?isStaticFile=<bool>&mediaPath=<urlencoded>
```

`isStaticFile` is not cosmetic: `true` for static assets (water level
cross-sections), `false` for radar frames. The bundle's only URL builder
hardcodes `true`, which 404s on every radar image. `mediaPathRaw` and `filename`
cannot be used to build a URL - only the blob works.

## See also

- [[1711_API-SURFACE]] - the full path catalogue
- [[1711_TESTING]] - verification method and traps
