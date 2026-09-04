# How this was verified, and the eight traps

Every count in these notes came from executing the call and reading the response.
Where I could not verify something I said so rather than inferring it. This file
records the traps, including the two I fell into and had to back out of.

## Method

1. Fetched the page HTML (266 KB) - server-rendered RSC payload, no API host in it.
2. Pulled all 55 Next.js chunks (8.3 MB) and mined them for path constants,
   the axios `baseURL`, and the request interceptor.
3. Swept all 163 non-templated paths against the live API, recording HTTP status
   and flattened row count for each.
4. For anything that failed or needed a parameter, loaded the real page in a
   browser with the relevant `ds` layer code and read the request it issued.
5. Downloaded actual bytes for the image products and opened one to confirm it
   was a radar picture and not an error placeholder.

Step 4 is the technique worth keeping. Guessing parameter values wasted time;
making the frontend issue the call recovered `rainfall_c1440` in one page load.

## Trap 1 - the MAP endpoint's top-level key count is provinces, not records

`/v2/cctv` returns `{data: {"10": FeatureCollection, "11": ..., ...}}`.

`len(data)` is **44**. The true camera count is **85**. The keys are province
codes. Flatten before counting:

```python
rows = [f for fc in payload["data"].values() for f in fc["features"]]
```

I reported 44 to myself first and only caught it because `/v2/cctv/list` said
`totalItems: 85`. Two routes disagreeing is the check that saves you; a single
route read naively gives a confidently wrong number.

## Trap 2 - I claimed `/list` was capped at 10 rows. It is not.

I tested `pagination[page]=2` on its own, got `400 INVALID_DATA`, tested `page=2`
on its own, got page 1 back, and concluded the endpoint was hard-capped at ten
rows with pagination broken.

Then the browser capture showed the site itself calling:

```
/v2/agency?pagination[pageSize]=-1&pagination[page]=1&dataset=weather   -> 200
```

**Both parameters are required together.** With the pair sent properly,
`/v2/cctv/list` returns all 85. My "hard cap" was my own malformed request.

The lesson is the one already written down in
`ψ/memory/learnings/` about negative results: an error you produced yourself is
not a property of the system. Reproduce the client's exact call before declaring
a limitation.

`pageSize=-1` is separately unreliable - it works on `/v2/agency`, returns 0 rows
on `/v2/cctv/list`. Pass an explicit number.

## Trap 3 - `500 / 1006 无操作权限` says "no permission" and means "missing parameter"

`/data/platform/v1/public/media?mediaTypeId=30` returns
`{"code":1006,"message":"无操作权限"}` - literally "no operation permission".

That is not what is wrong. `/auth/get-public` grants the anonymous role `view` on
all 159 datasets including every radar site; I diffed the two lists to be sure.
The endpoint simply requires `startDate` and `endDate`:

```
media?mediaTypeId=30&agencyId=13&startDate=2026-09-04 00:00&endDate=2026-09-04 23:59&limit=-1&latest=true
```

With dates: 27 radar records. Reading 1006 as an auth wall would have cost the
entire radar catalogue - the largest single find here.

## Trap 4 - `isStaticFile=true` 404s every radar image

The bundle contains exactly one media URL builder:

```js
IMAGE_URL: e => "https://platform.thaiwater.net/api/v1/public/media/view?isStaticFile=true&mediaPath=" + e
```

Applied to a radar `mediaPath` it returns 404. I nearly recorded the radar images
as unreachable.

A positive control settled it: the same base with a **water level cross-section**
`mediaPath` returned a 9,004-byte PNG. So the host and route were right and the
flag was wrong. `isStaticFile=false` (or omitting it) returns the radar frame -
128,784 bytes of JPEG for `cmp240`.

Two different media classes, one hardcoded flag. Always run the positive control
before believing a 404 means "not available".

## Trap 5 - `mediaDatetime` is tagged +07:00 and mostly carries UTC

`ubn240` reports `2026-09-04T09:00:00+07:00` while the wall clock was 17:11 +07.
Taken at face value that is a seven-hour-old frame from a fifteen-minute product.

It is not stale. The value is the UTC wall-clock with a `+07:00` label glued on.
Three independent confirmations:

- the filename, `ubn240_202609040900.jpg`, encodes the same `0900`
- newest frame across TMD tracked UTC-now minus ~20 min, all afternoon
- **the rendered image's own footer reads `CHU 2026-09-04 09:45:00`** - TMD stamps
  its own picture in UTC

And it is not uniform. `rasisalai` reports `16:41:06+07:00` - true local, but that
is the **ingest** time, while its filename says `0930` (frame time, UTC). So:

| Field | What it actually is |
|-------|---------------------|
| `mediaDatetime` on most sites | frame time in UTC, mislabelled `+07:00` |
| `mediaDatetime` on rasisalai | local ingest time, not frame time |
| `filename` | frame time in UTC, on every site |

**Parse the filename.** It is the only honest clock across all 40 sites.
`twa_pull.py` does this in `frame_time()`.

This is the same failure shape as the `rain_today` finding already in memory: a
field name that lies about *when*. Here the timezone suffix does the lying.

Note this applies to the **v1 media** records only. The v2 layers are correct -
water level stamped `16:50+07:00` against a 17:11 clock, rainfall `16:00`.

## Trap 6 - the animated radar is not a Thai product

`ds=rr` is "radar-rain", and it is natural to assume that means TMD or HII radar.
The browser capture shows the map painting tiles from
`tilecache.rainviewer.com` - **RainViewer**, a third-party global service.

The Thai radar images exist but are a separate, non-tiled product (40 station
pictures via `mediaTypeId=30`). If someone needs "the radar layer that the map
shows", that is RainViewer and it carries RainViewer's terms, not HII's.

## Trap 7 - `isActive: true` and a valid JPEG both lie about CCTV

All 85 cameras report `isActive: true`. Chasing that to the pixels:

64 have a URL, on 57 distinct hostnames, of which **10 resolve**. All 44
`dyndns.org` names are NXDOMAIN. 8 cameras returned a JPEG. Of those 8, only
**4** carried an EXIF `datetime` matching the wall clock.

Two separate lies stacked:

- `isActive` is a database flag nobody reviews - it says true for hosts whose DNS
  lapsed years ago
- HTTP 200 + valid JPEG still is not a live picture. เขื่อนสิรินธร serves a
  perfectly good image with **15/06/2024** burned into the overlay.
  เขื่อนรัชชประภา carries EXIF from 2026-07-28, five weeks stale.

Before concluding the cameras were dead I ran the control, because a sandbox that
blocks plain HTTP or high ports would produce exactly the same symptom:
`http://example.com` returned 200 and `http://portquiz.net:5001` returned 200, so
plain HTTP and port 5001 both work from here. The failures are NXDOMAIN, not
egress filtering. That check is the difference between "the registry is stale"
and "my network is limited", and they are indistinguishable from the error alone.

## Trap 8 - this is not the API already in our notes

`ψ/lab/hii-water-level/WATER-APIS.md` documents `api-v3.thaiwater.net`. This is
`twa-api-public.thaiwater.net`: different host, different auth, different counts
(water level 791 here vs 1,407 there; CCTV 85 vs 106).

Both are live and both are correct for their own station sets. Do not carry a
number across.

## Checks that passed

- **Pagination positive control**: `pagination[page]=2&pagination[pageSize]=10`
  returned page 2 with different ids - the mechanism works, my earlier call was wrong.
- **Over-bank filter sanity**: `diffWlBank` across 791 stations ranged 0.28 to
  19.49 with zero nulls, so "0 stations over bank" is a real reading of a working
  filter, not a filter matching nothing.
- **Image reality check**: opened `cmp240.jpg` - a genuine Chumphon 240 km PPI
  scan with a dBZ scale and live echoes over the peninsula.
- **Bulk run**: `twa_pull.py all` pulled 11,224 records / 13 MB with no failures.

## Not verified

Stated as leads, not facts:

- the `live1.hii.or.th` GeoTIFF products (paths from the bundle, never fetched)
- the GeoServer WMS and `proxy-tiff` routes
- the `api.hii.or.th/tiservice` isohyet endpoint
- parameter sets for the nine 400-ing `/v2/summary-area` and `/v2/district-rain`
  endpoints, and for the v1 `/graph` family
- whether the anonymous key is rate-limited, rotated, or intended for reuse
- **licensing** - no terms are published on this host at all
