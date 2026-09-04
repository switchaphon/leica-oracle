# twa-thaiwater

Puller for `twa.thaiwater.net` - rainfall, water level, CCTV and rain radar.

Built 2026-09-04 answering: "can we pull the radar / rainfall / water level /
CCTV off this page?" Answer: yes, all of it, no account needed.

Full write-up: `ψ/learn/thaiwater/twa/twa.md`

## Quick start

Stdlib Python only, no install.

```bash
python3 twa_pull.py rainfall 1440      # 24h rain, 2,696 stations
python3 twa_pull.py waterlevel         # 791 stations
python3 twa_pull.py cctv               # 85 cameras (see caveat)
python3 twa_pull.py radar-sites        # 40 Thai radar sites
python3 twa_pull.py radar-image cmp240 chumphon.jpg
python3 twa_pull.py radar-tiles        # RainViewer animated frames
python3 twa_pull.py all --out ./dump   # everything, 11,224 records / 13 MB
```

## What it talks to

| Host | Auth |
|------|------|
| `twa-api-public.thaiwater.net` | `x-api-key`, anonymous key from the site bundle |
| `platform.thaiwater.net` | same key, serves image bytes |
| `api.rainviewer.com` | none |

## Things the code deliberately handles

Each of these silently produces a wrong answer if you skip it:

- **MAP payloads are keyed by province.** `len(data)` is provinces, not records.
  `/v2/cctv` looks like 44 rows and is 85 cameras. `features()` flattens.
- **Pagination needs both parameters.** `pagination[page]` alone returns 400;
  `page=2` alone is silently ignored. `pageSize=-1` works on some endpoints and
  returns 0 rows on others.
- **`startDate`/`endDate` are mandatory on radar media.** Omitting them returns
  `500 {"code":1006,"message":"无操作权限"}`, which reads as a permissions
  failure and is not one.
- **`isStaticFile=false` for radar images.** The site's own URL builder hardcodes
  `true`, which 404s on every radar frame.
- **`mediaDatetime` is not trustworthy.** Tagged `+07:00`, usually carrying UTC;
  on `rasisalai` it is the ingest time rather than the frame time. `frame_time()`
  parses the filename instead, which is UTC on every site.

## CCTV caveat

`isActive: true` on all 85 cameras means nothing. Measured 2026-09-04:
64 have URLs, on 57 hostnames, of which 10 resolve; 8 return a JPEG; **4** have an
EXIF timestamp matching now, which is a LOWER BOUND on live cameras: a camera
serving a current frame without EXIF fails that test while being fine.
All 44 `dyndns.org` hosts are NXDOMAIN, which makes the names unreachable and
says nothing about whether the cameras still work.
One camera serves a valid JPEG stamped 15/06/2024.

Check EXIF `datetime` before trusting a frame.

## Licence

Unsettled. No terms published on this host; CKAN at `data.hii.or.th` is
CC-BY-**NC**. Settle with สสน. in writing before any commercial use.
