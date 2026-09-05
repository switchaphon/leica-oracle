# How this was verified, and the ten traps

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

### The timestamp you reach for is three different timestamps

rpro-ent-oracle traced this trap into their own platform and came back with the
distinction the probe above was blurring. "Check the time in the file" names three
defences of very different strength:

| layer | what it measures | survives | fails on |
|---|---|---|---|
| **3a** | when the file was **stored** | nothing - a re-upload refreshes it | the naive design |
| **3b** | when the **recording started** | re-upload | a live stream of a frozen frame |
| **3c** | time inside the **content** - EXIF, or text burned into the pixels | both | the only layer that caught เขื่อนสิรินธร |

RPRO sits at **3b**: the freshness timestamp comes from a MinIO object *tag* rather
than `lastModified` (`info.js:86`, `base.js:32-34`), and that tag is written at upload
from the media's own recording start
(`cctv.js:244` -> `cctv.js:108`, `moment(vod.data.startTime).unix()`). Re-uploading a
stale file therefore preserves the old start time, the age check exceeds its 3-minute
threshold, and the thumbnail is marked INACTIVE. It also **fails closed**: an empty
catch leaves the timestamp undefined, `NaN <= 3` evaluates false, and the result is
INACTIVE rather than a silent pass. That is the correct direction for a freshness
check to fail in.

The residual gap is narrow and is exactly the case in this trap. A camera pushing a
**frozen frame into a live RTSP stream** produces a genuinely new recording of a dead
image: the recording start is fresh, the status reads ACTIVE, and the picture is from
2024. 3b cannot see it because nothing about the transport is stale - only the pixels
are.

**The warning worth carrying: 3b feels like content time and is transport time wearing
its clothes.** A team that implements 3b will believe it has 3c. What is verifiable
here is that RPRO reads *recording* time rather than *storage* time - which is the
part worth copying - and that this still lands one layer short of the failure observed
above. Whether 3b was chosen or arrived at is not established, and the trace does not
show it either way.

For this trap the probe reached 3c on both cameras, but by two different routes:
burned-in overlay text at เขื่อนสิรินธร, EXIF at เขื่อนรัชชประภา. Only one of those is
machine-readable, which is why the check cannot be fully automated: **the layer that
works is the one that is hardest to read.**

### Layer 4 - do not ask what time it claims to be, ask whether it changed

rpro-ent-oracle's addition, and it escapes the whole family above:

| | question | can the source lie? |
|---|---|---|
| 3a, 3b, 3c | **what time does this claim to be?** | yes - every one is an assertion |
| **4** | **did it change?** | no timestamp is involved, so there is nothing to lie with |

Hash two successive polls of the same camera and ask whether the bytes changed.

**But the test is one-sided, and the first version of it here was wrong.** The
argument that "a real sensor cannot emit two byte-identical JPEGs" is true of
*frames*. An HTTP GET does not return a frame, it returns a **file**. If the server
encodes once per refresh cycle and serves that same file until the next one, sensor
noise never enters the comparison - the encoding already happened, once.

เขื่อนภูมิพล demonstrates it: EXIF advancing every minute, bytes identical at a
two-second gap. The naive form of this check calls a live camera frozen, with total
confidence. That is 3b wearing 3c's clothes again, one layer up.

| observation | conclusion | needs the refresh period? |
|---|---|---|
| bytes **differ** | the source produced something new. **NOT frozen.** | no - conclusive on its own |
| bytes **identical** | frozen, **or** polled inside one refresh cycle. **UNKNOWN.** | yes |

**Layer 4 proves liveness cheaply and can never prove frozenness by itself.** The
shipping rule is that identical bytes are reported as UNKNOWN, never as FROZEN.

### Measuring the refresh period, without aliasing

Sampling at guessed intervals (5, 15, 30, 60, 90 s) aliases: at exactly the period you
get "always same" or "always different" depending on phase, and a harmonic imitates the
real answer. **Poll fast and record when the bytes change** - every two seconds for a
few minutes, log the timestamp of each change, read the period off the gaps. One
measurement, no interval guessing, and it yields the *distribution* rather than a single
number, which matters because a jittery refresh needs a wider gap than a clean 60-second
one.

`Last-Modified`, `ETag` and `Cache-Control: max-age` are worth reading, and
`max-age` is often the declared period - but those are assertions the source makes about
itself, which is layer 3 material. **Headers to form the hypothesis, byte-change timing
to confirm it.**

### Pin a known-live camera as the positive control

เขื่อนภูมิพล is independently verified live by a different instrument - EXIF advancing
every minute. Any gap threshold chosen for layer 4 must still classify it LIVE. That is
the control discipline applied to the control itself, and it is the thing that catches a
threshold tuned too tight later, by someone who was not present for the reasoning.

It is **stronger on cameras than on the radar tiles this repo already applies it to**.
Consecutive JPEGs off a real sensor are byte-identical with probability approximately
zero - sensor noise plus lossy encoding guarantee difference - so byte-identity between
two polls is near-conclusive for a camera, where for a rendered tile it is only
suggestive. เขื่อนสิรินธร would have failed on the second poll, with no reading of
`15/06/2024` at all.

The instrument was already in this repo, pointed at RainViewer.

Caveat, so it is not over-claimed: a genuinely static night scene is not the same as a
frozen feed. That is what an interval and a perceptual threshold are for - and for
byte-exact identity the caveat barely applies, because a live sensor cannot produce it.

### The instrument usually already exists, aimed somewhere else

Layer 4 required no new capability. A byte-identity check was already written in this
repo, in the radar path, to reject a frame whose tiles are all identical. Applying the
same function to a camera poll is a change of target, not a change of tool - and it is
*stronger* there than where it was originally aimed.

That is the common case rather than a lucky one. The gap between "we cannot detect
this" and "we can" is usually a question of where an existing check is pointed, not of
building a new one. Before designing a detector, it is worth asking which check already
in the codebase would fire on this input if it were shown it.

Two of the corrections in this document arrived the same way. The cardinality check
that validated the 110 m join (trap 9) and the second-run freshness test that destroyed
the latency reading (below) were both one-line uses of data already loaded. Neither
needed new instrumentation; both needed someone to name the test.

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

## Trap 9 - the station overlap, and a figure that existed only in a message

Two independent keys were tried against the `api-v3` water level set: station code
and coordinates. They disagreed maximally - **0 overlap by code, 768 by position.**

Resolved in favour of coordinates, but not because coordinates are better. **A
code-scheme mismatch fully explains a zero-overlap result; nothing explains 768 exact
coordinate coincidences.** One key's failure had an available mechanism, the other's
did not. The rule to carry forward is *prefer the key whose failure has no available
mechanism* - not "prefer coordinates", which would be the wrong lesson and may point
the other way next time.

### The numbers, re-derived 2026-09-04 and reproducible

| | twa | api-v3 |
|---|---|---|
| water level stations | **780** | **1,406** |
| with usable coordinates | 780 | 1,406 |
| without coordinates | **0** | **0** |

| join at 110 m | |
|---|---|
| twa matched to a v3 station | **768 (98.5%)** |
| twa with no match | **12** |
| v3 stations matched by more than one twa | **0** |
| match distance: median / p90 / max | 0.0 m / 0.0 m / **0.1 m** |
| matched within 10 m | 768 of 768 (100%) |

Two things follow. **The 110 m tolerance is doing no work** - the hosts publish
identical coordinates, not nearby ones, so a 1 m tolerance returns the same 768.
Choosing 110 m was luck, not method; the load-bearing check is the cardinality, and
it is 1:1 everywhere. And **twa-only = 12 is a count, not a lower bound**, because
nothing was excluded by construction: every station on both hosts had coordinates and
entered the join.

The 12 are coherent rather than scattered - nine are a GNSS programme in Nan
(`GNSS01`-`GNSS10`), plus บางพระ (ตราด), บ้านดอนยาง (ยโสธร) and น้ำพวย อ.ผาขาว (เลย).
Their nearest `api-v3` neighbour is **0.68 km to 25.50 km** away, so they are genuinely
absent, not tolerance misses.

### The trap itself

An earlier pass reported `791` stations and `721 of 733` matched. **None of those
three figures was written to any file** - they existed only in a message to
rpro-ent-oracle. When challenged on the denominator they could not be re-derived,
because 791 had already moved to 780 on live data and 733 corresponds to nothing
recoverable.

**A number that lives only in a message cannot survive its first "where did that come
from".** The join is now scripted and its output recorded here, so the next challenge
is answered by re-running it rather than by defending a remembered figure.

### Operational conclusion

For water level, `twa` adds nothing `api-v3` does not already carry - the coordinate
identity shows one station registry surfaced twice, not two surveys. The new host's
value is radar, CCTV, PM2.5 and cumulative rainfall.

## Trap 10 - coordinate identity proves the registry, not the readings

rpro-ent-oracle refused the conclusion drawn from trap 9: 768 exact coordinate matches
prove the two hosts share a **station registry**, and say nothing about whether those
stations report the same **values**, at the same cadence, with the same gaps. The
objection is correct, and this host pair demonstrates why.

### The near-miss first

The initial cross-host comparison reported **timestamps differing on all 768 pairs**
and was about to be filed as a freshness divergence. It was a serialisation artefact:

```
twa : '2026-09-04T22:40:00+07:00'
v3  : '2026-09-04 22:40'
```

Both were sliced `[:16]`, so position 10 compared `T` against a space on every row.
The tell was in the output being read rather than the code: the most common
"difference" printed as `twa 22:40 vs v3 22:40`, times visibly identical while the
comparison called them different. **A difference count that disagrees with the values
printed beside it is an instrument fault, not a finding.**

### The comparison after normalising

768 matched pairs, same instant:

| | count |
|---|---|
| timestamps identical | **763 (99.3%)** |
| timestamps differing | 5 - all five twa **fresher**, v3 a full day stale |
| values identical exactly | 294 |
| values within 5 mm (float/rounding) | 467 |
| **values genuinely different** | **7** |

The seven, largest first:

| station | twa | api-v3 | difference |
|---|---|---|---|
| แม่น้ำชี ฝายมหาสารคาม | 146.813 | 138.030 | **8.783 m** |
| บ้านค่าย | 5.500 | 6.150 | 0.650 m |
| บ้านดอนขยอม | 120.430 | 120.000 | 0.430 m |
| บ้านห้วยทับทัน | 123.550 | 123.600 | 0.050 m |
| ตลาดเสนา | 1.220 | 1.210 | 0.010 m |
| ลำโดมใหญ่ บ้านนาเยีย | 112.860 | 112.850 | 0.010 m |

**761 of 768 (99.1%) agree within 5 mm.** But an 8.78 m disagreement about a river
level at a weir is not rounding: one of the two hosts is currently wrong about
มหาสารคาม, and nothing in the coordinate join could have surfaced it.

### What this settles

| claim | status |
|---|---|
| one registry surfaced twice | **proven** - 768 exact matches, 1:1 |
| current values agree | **99.1% within 5 mm**, 7 exceptions |
| freshness | 5 stations where twa leads v3 by a day |
| cadence, backfill, history | **unproven** - this is one snapshot, not a window |

The full-window comparison (the shape used against the file corpus on CPY001, 51,872
timestamps) has **not** been run across hosts. Until it is, the honest statement is
that this settles coverage and one snapshot of values, not equivalence.
