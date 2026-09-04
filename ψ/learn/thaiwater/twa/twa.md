# twa.thaiwater.net Learning Index

## Source

- **Site**: https://twa.thaiwater.net
- **API**: https://twa-api-public.thaiwater.net
- **Owner**: สสน. / HII - Hydro-Informatics Institute, under MHESI
- **No `origin/` symlink**: this is a live web target, not a git repo. There is
  nothing to clone, so it is deliberately **not** listed in `ψ/learn/.origins` -
  that manifest is consumed by `/learn --init`, which runs `ghq get -u
  https://github.com/<row>` on every line and would fail on this one.

## Explorations

### 2026-09-04 1711 (deep)

- [[2026-09-04/1711_QUICK-REFERENCE|Quick Reference]] - the direct answer, start here
- [[2026-09-04/1711_ARCHITECTURE|Architecture]] - hosts, auth model, payload shapes
- [[2026-09-04/1711_API-SURFACE|API Surface]] - all 195 paths, verified status and counts
- [[2026-09-04/1711_TESTING|Testing]] - verification method and the ten traps
- [[2026-09-04/1711_CODE-SNIPPETS|Code Snippets]] - working curl and Python

**Key insights**:

1. **Everything on the page is pullable without an account.** The bundle ships an
   anonymous `x-api-key`, and `/auth/get-public` grants `view` on all 159
   datasets. Granted 159, not granted 0.
2. **`twa-api-public.thaiwater.net` is a second, separate API** from the
   `api-v3.thaiwater.net` already documented in `ψ/lab/hii-water-level/`.
   Different auth, different code schemes, and mostly the SAME stations:
   768 of twa's 780 water level stations sit on api-v3 coordinates to within
   0.1 m. For water level twa adds 12 stations and nothing else. Its value is
   radar, CCTV, PM2.5 and cumulative rainfall.
3. **The animated rain radar is RainViewer, not a Thai product.** Thai radar
   exists separately as 40 station images via `mediaTypeId=30`.
4. **Three separate fields lie**: MAP payload key counts are provinces not
   records (44 vs 85 cameras); `mediaDatetime` is tagged `+07:00` while carrying
   UTC; `isActive: true` is set on cameras whose DNS lapsed years ago.
5. **Two of my own errors are recorded in the Testing notes**, both from
   malformed requests read as system limitations. The fix that worked repeatedly:
   load the real page with the right `ds` layer code and read the call the
   frontend makes, instead of guessing parameters.

## Tooling

`ψ/lab/twa-thaiwater/twa_pull.py` - verified puller, stdlib only.
One `all` run: 11,224 records / 13 MB across every domain.

## Related

- `ψ/lab/hii-water-level/WATER-APIS.md` - the older `api-v3` surface
- `ψ/lab/hii-water-level/CURL.md` - historical bulk CSV and time-series recipes
- `ψ/memory/learnings/2026-09-04_a-name-can-lie-about-when-not-only-about-where.md`

## Open, not answered here

- Licensing. No terms are published on this host. CKAN at `data.hii.or.th` is
  CC-BY-**NC**. An anonymous key in a public bundle is not a licence, and this
  must be settled with สสน. in writing before any commercial ingest.
